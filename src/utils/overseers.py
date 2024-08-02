"""Functions for creating AI-monitors which oversee various parts of the
conversation and chatbot messages and provides feedback to prevent chatbot
identity drift. Overseer bots are assumed to generate a message on the form
`¤:provide_feedback(<data on JSON format>):¤`"""

import re

from utils.backend import get_source_content_and_path
from utils.backend import get_sources_available_to_chatbot
from utils.backend import dump_prompt_response_pair
from utils.backend import write_to_file
from utils.backend import OVERSEERS_CONFIG
from utils.backend import OVERSEER_LOG_PATH
from utils.backend import CHATBOT_MODES_TO_CITATIONS
from utils.backend import SYSTEM_MESSAGES
from utils.backend import update_overseer_log
from utils.backend import collect_prompts_in_dictionary
from utils.backend import LOGGER
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import replace_last_assistant_response
from utils.chat_utilities import (
    remove_system_messages_following_last_assistant_response,
)
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import generate_single_response_to_prompt
from utils.chat_utilities import index_of_assistant_responses_visible_to_user
from utils.general import list_intersection
from utils.general import remove_syntax_from_message
from utils.general import silent_print
from utils.general import find_longest_string


def ai_filter(conversation, harvested_syntax, chatbot_id):
    """Uses prompted AI-agents - monitors - to evaluate and give feedback on the
    chatbots response. Returns the evaluation of the AI-judges (ACCEPT, WARNING,
    REJECT), and a list of warning messages ([] if no warnings). The stages are:

    1. Check if the user consents to being redirected (if requesting redirect)
    2. Preliminary check of response using swift judges (using cheaper LLM)
    3. If flagged in 2: Evaluate with Chief judges (using expensive LLM)
    4. If Rejected in 3: Correct response so that it complies with warnings
    """
    global PROMPTS, CHATBOT_MODES_TO_CITATIONS

    # ** PREPARATION **
    write_to_file(OVERSEER_LOG_PATH, "\n\n\n\n# ** RESPONSE EVALUATION **", mode="a")
    # Update PROMPTS and CITATIONS dictionaries
    PROMPTS = collect_prompts_in_dictionary(chatbot_id)
    CHATBOT_MODES_TO_CITATIONS["source_communication"] = (
        get_sources_available_to_chatbot(chatbot_id)
    )
    # Set default output values
    final_verdict = "ACCEPT"
    warning_messages = []

    chatbot_citations = harvested_syntax["citations"]
    content_of_cited_sources = get_content_of_cited_sources(
        chatbot_citations, chatbot_id
    )

    # Extract stages associated with the chatbot
    filter_stages = OVERSEERS_CONFIG[chatbot_id]
    # Extract various classes of overseers
    redirect_consent_checker = filter_stages["redirect_consent_check"][
        "redirect_consent_checker"
    ]

    # Collect variables needed to fill the prompts of the overseers
    prompt_variables = prepare_prompt_variables(
        conversation,
        content_of_cited_sources,
    )

    # ** CHECK IF CHATBOT IS REQUESTING REDIRECT **
    if harvested_syntax["referral"] and redirect_consent_checker:
        redirect_checker_verdict = check_if_user_confirms_redirect(
            conversation, redirect_consent_checker
        )
        if redirect_checker_verdict == "ACCEPT":
            silent_print("Overseer confirms that user wants to be referred.")
        else:
            warning_messages.append(SYSTEM_MESSAGES["confirm_before_redirect"])
            final_verdict = "REJECT"

    else:
        # ** AI JUDGES **
        final_verdict, cheif_judge_warnings = evaluate_with_ai_judges(
            filter_stages["preliminary_judgement"],
            filter_stages["final_judgement"],
            prompt_variables,
            chatbot_citations,
        )
        warning_messages += cheif_judge_warnings

        # ** RESPONSE REFINEMENT **
        conversation, warning_messages = refine_response(
            filter_stages["response_refinement"],
            prompt_variables,
            final_verdict,
            warning_messages,
            conversation,
        )

    return warning_messages, conversation


def get_content_of_cited_sources(chatbot_citations, chatbot_id) -> list[str]:
    """Fetches the content of the sources cited by the chatbot, if any."""
    cited_sources = list_intersection(
        chatbot_citations, CHATBOT_MODES_TO_CITATIONS["source_communication"]
    )
    contents_of_cited_sources = []
    if cited_sources:
        for source_name in cited_sources:
            contents_of_cited_sources.append(
                get_source_content_and_path(chatbot_id, source_name)[0]
            )
    return contents_of_cited_sources


def prepare_prompt_variables(
    conversation,
    content_of_cited_sources,
) -> dict:
    """Collects variables that needed to complete the the overseer prompts
    in a dictionary, such as "chatbot_message". Note: if you want to have a
    variable "... {var_name} ..." in your prompt, then you need to ensure that
    that variable gets added to the 'prompt_variables' dictionary below."""

    chatbot_message = remove_syntax_from_message(
        grab_last_assistant_response(conversation)
    )
    user_message = grab_last_user_message(conversation)
    prompt_variables = {
        "chatbot_message": chatbot_message,
        "user_message": user_message,
    }

    # Source-based variables
    if content_of_cited_sources:
        prompt_variables["sources"] = string_together_cited_sources(
            content_of_cited_sources
        )
        # If source (singular) is requested, grabs only the first cited string [NEEDS UPDATE]
        prompt_variables["source"] = content_of_cited_sources[0]

    return prompt_variables


def string_together_cited_sources(
    cited_sources: list[str],
) -> str:
    """If the chatbot has cited multiple sources, this function combines them
    into one single string that can be inserted into a prompt ('sources'
    argument)."""
    combined_source_string = ""
    for i, source in enumerate(cited_sources):
        combined_source_string += f"source {i}: '{source}'\n\n"
    return combined_source_string


def check_if_user_confirms_redirect(
    conversation,
    overseer_dict: list,
    model="gpt-35-turbo-16k",
) -> str:
    """Checks if the user has confirmed that they want to be referred to another
    assistant, assuming that a referral request has been issued. AI agent checks
    the two messages preceeding the redirect command."""
    prompt_filled = fill_prompt_of_redirect_consent_checker(
        conversation,
        overseer_dict,
    )
    overseer_response = generate_single_response_to_prompt(prompt_filled, model)
    dump_prompt_response_pair(
        prompt_filled, overseer_response, dump_name="redirect_consent_checker"
    )
    verdict = extract_verdict(overseer_response, overseer_dict["verdict_map"])

    if verdict == "REJECT":
        silent_print(f"Message fails preliminary check by redirect_consent_checker")
    else:
        silent_print(f"Message passes preliminary check by redirect_consent_checker")

    return verdict


def fill_prompt_of_redirect_consent_checker(conversation):
    """Fills the prompt of the overseer responsible for checking if the user
    has confirmed that they want to be redirected to a new assistant. The
    decisions is based on the last two messages before the request to redirect
    the user."""
    # Grab the last two messages before the referral request (initial prompt
    # excluded)
    visible_conversation = conversation[
        index_of_assistant_responses_visible_to_user(conversation)
    ]
    chat_last2 = visible_conversation[1:-1][-2:]
    # Extract messages and insert them into a formatted string
    last_2_messages = "\n\n".join(
        [f"{message['role']}: {message['content']}" for message in chat_last2]
    )
    # Fill prompt template
    prompt_filled = PROMPTS["redirect_consent_checker"].format(
        last_2_messages=last_2_messages
    )
    return prompt_filled


def extract_verdict(overseer_response, keyword_to_verdict_map: dict):
    """The overseer outputs a string which contains evaluation keywords like
    AGREE or WARNING. This functions map these keywords to official verdicts
    which are used in subsequent nodes in the filter stage. The verdict field
    shows which verdict each keyword maps to, such as DENY -> REJECT."""
    official_verdict = "ACCEPT"
    identified_keywords = []
    for keyword in keyword_to_verdict_map:
        if keyword in overseer_response:
            identified_keywords.append(keyword)
    # If multiple keywords match, select the longest one (Can occurr if, for
    # instance, both ACCEPTED and NOT ACCEPTED are keywords)
    longest_identified_keyword = find_longest_string(identified_keywords)
    if longest_identified_keyword:
        official_verdict = keyword_to_verdict_map[longest_identified_keyword]
    return official_verdict


def evaluate_with_ai_judges(
    preliminary_judges,
    chief_judges,
    prompt_variables,
    chatbot_citations,
):
    """Runs the AI-response through the AI-filters - first the preliminary
    AI-judges (cheap LLMs) and, if flagged by the preliminary judges, then the
    Chief judges are activated to get the final evaluation. Each stage produces
    an evaluation (ACCEPT or REJECT) and a list of warning messages. If the
    message is rejected by the Chief judges, then another AI-agent will take the
    message and warning messages and modify it so that it complies with the
    system warnings."""

    # Set default values
    preliminary_verdict = "ACCEPT"
    final_verdict = "ACCEPT"
    cheif_judge_warnings = []

    # Find judges that are suitable for the current response categories
    relevant_prelim_judges = find_relevant_judges(preliminary_judges, chatbot_citations)
    relevant_cheif_judges = find_relevant_judges(chief_judges, chatbot_citations)

    # ** Preliminary check **
    if relevant_prelim_judges:
        preliminary_verdict = get_preliminary_evaluation(
            relevant_prelim_judges, prompt_variables
        )

    # ** Cheif overseers **
    if relevant_cheif_judges and preliminary_verdict == "REJECT":
        final_verdict, cheif_judge_warnings = get_final_evaluation(
            relevant_cheif_judges, prompt_variables
        )

    return final_verdict, cheif_judge_warnings


def find_relevant_judges(judges: dict, chatbot_citations: list[str]) -> list[str]:
    """Iterates over the dictionaries, each of which corresponds to a particular
    judge, and determines if it is relevant based on the citations in the
    chatbots response."""
    chatbot_mode = inferr_chatbot_mode(chatbot_citations)
    relevant_judges = []
    for judge_name, judge in judges.items():
        if judge["associated_mode"] in chatbot_mode:
            judge["name"] = judge_name
            relevant_judges.append(judge)
    return relevant_judges


def inferr_chatbot_mode(chatbot_citations) -> list[str]:
    """Inferrs which "mode" the chatbot is in, e.g. default or
    source_communication."""
    current_chatbot_modes = []

    for mode in CHATBOT_MODES_TO_CITATIONS:
        citations_overlapping_with_mode = list_intersection(
            CHATBOT_MODES_TO_CITATIONS[mode], chatbot_citations
        )
        if citations_overlapping_with_mode:
            current_chatbot_modes.append(mode)

    if not current_chatbot_modes:
        raise ValueError(f"{chatbot_citations} does not match any citation classes.")

    return current_chatbot_modes


def get_preliminary_evaluation(
    relevant_prelim_judges: list[dict], prompt_variables: dict
) -> str:
    """Iterates over the relevant preliminary judges and obtains evaluations
    from each. Converts evaluations to either REJECT or ACCEPT. If any
    preliminary judge flags the message, it gets passed on to the cheif judges
    (that uses GPT 4) for final verdict. prompt_variables contains the variables
    needed to complete the prompt templates of the relevant judges."""
    prelim_verdicts = []

    for judge in relevant_prelim_judges:
        prelim_verdicts.append(
            get_verdict_from_single_preliminary_judge(judge, prompt_variables)
        )

    if not prelim_verdicts:
        raise ValueError(f"None evaluations obtained from preliminary judges")

    if "REJECT" in prelim_verdicts:
        return "REJECT"
    else:
        return "ACCEPT"


def get_verdict_from_single_preliminary_judge(judge: dict, prompt_variables: dict):
    """Uses GPT-3.5-turbo-instruct to do a preliminary check of fidelity to
    cited sources. This evaluation is decent at catching deviations from source
    materials, but sometimes flags messages that are perfectly fine. If flagged,
    a more computationally expensive model is called to double check the
    evaluation."""
    prompt = PROMPTS[judge["name"]]
    prompt_filled = prompt.format(**prompt_variables)
    judge_response = generate_single_response_to_prompt(
        prompt_filled, model="gpt-35-turbo-16k"
    )
    verdict = extract_verdict(judge_response, judge["verdict_map"])
    dump_prompt_response_pair(prompt_filled, judge_response, judge["name"], verdict)
    update_overseer_log(judge["name"], judge_response, verdict)
    if verdict == "REJECT":
        silent_print(f"{judge['name']} rejected the response")
    LOGGER.info(f"{judge['name']}:\n{judge_response}")

    return verdict


def get_final_evaluation(
    relevant_cheif_judges: list[dict],
    prompt_variables: list[str],
):
    """Cheif judges evaluates the chatbots response. Returns the final verdict
    and list of warning messages (generated if not accepted)."""
    final_verdict = "ACCEPT"
    cheif_verdicts = []
    cheif_judge_warnings = []
    for judge in relevant_cheif_judges:
        verdict, feedback = get_single_cheif_judge_evaluation(
            judge,
            prompt_variables,
        )
        cheif_verdicts.append(verdict)
        if feedback:
            cheif_judge_warnings.append(feedback)

    silent_print(f"chief_judge_source_fidelity evaluations: {cheif_verdicts}")

    if "REJECT" in cheif_verdicts:
        final_verdict = "REJECT"

    return final_verdict, cheif_judge_warnings


def get_single_cheif_judge_evaluation(judge: dict, prompt_variables: dict):
    """Produces a final verdict and feedback for the chatbot response using
    smart but expensive LLM."""
    prompt_filled = PROMPTS[judge["name"]].format(**prompt_variables)
    overseer_response = generate_single_response_to_prompt(prompt_filled, model="gpt-4")
    verdict = extract_field_content(overseer_response, "VERDICT")
    feedback = extract_field_content(overseer_response, "FEEDBACK")
    if verdict == "ACCEPT":
        feedback = None

    dump_prompt_response_pair(prompt_filled, overseer_response, judge["name"], verdict)
    update_overseer_log(judge["name"], overseer_response, verdict)
    LOGGER.info(f"{judge['name']}:\n{overseer_response}")

    if not verdict:
        raise ValueError("'verdict' must be present in the cheif judges response.")
    else:
        return verdict, feedback


def extract_field_content(text, field_name="VERDICT"):
    """Extracts the content of the specified field from the string.
    Assumes that the following convention is used:

    FIELD_NAME: "content"

    """
    # Define regular expression pattern to extract the field content
    pattern = rf'{field_name}:\s*"([^"]*)"'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return None


def refine_response(
    response_refiners,
    prompt_variables,
    final_verdict,
    warning_messages,
    conversation,
):
    """Overseers refines the chatbots response and updates the conversation and
    warnings accordingly."""
    if "compliance_enforcer" in response_refiners and final_verdict == "REJECT":
        response_corrected = modify_response_to_comply_with_warnings(
            prompt_variables, warning_messages
        )
        conversation, warning_messages = update_variables_after_refinement(
            conversation,
            warning_messages,
            response_corrected,
        )

    return conversation, warning_messages


def correct_response_and_update_chat_and_warning(
    conversation,
    prompt_variables: dict,
    warning_messages: list[str],
):
    """An AI agent corrects the message generated by the chatbot so that it
    complies with the systems warning. Returns updated conversation and
    warning_message."""
    response_corrected = modify_response_to_comply_with_warnings(
        prompt_variables, warning_messages
    )
    conversation, warning_messages = update_variables_after_refinement(
        conversation, warning_messages, response_corrected
    )
    return conversation, warning_messages


def modify_response_to_comply_with_warnings(
    prompt_variables: dict, warning_messages: list[str]
) -> str:
    """An AI agent has been prompted to correct the message generated by the
    chatbot so that it complies with the systems warning. Typically replaces an
    out-of-scope response with a more standard 'I am not allowed to talk about
    that'-type message."""
    prompt_variables["system_message"] = "\n\n".join(warning_messages)
    prompt_completed = PROMPTS["compliance_enforcer"].format(**prompt_variables)
    corrected_response = generate_single_response_to_prompt(prompt_completed, "gpt-4")
    # Use the no_advice_or_claims or claims response label
    corrected_response = f'¤:cite(["no_advice_or_claims"]):¤ {corrected_response}'
    silent_print("** Rejected message substituted **")
    dump_prompt_response_pair(
        prompt_completed, corrected_response, "corrected_response.md"
    )
    return corrected_response


def update_variables_after_refinement(
    conversation, warning_messages: list[str], refined_response: str, final_verdict
):
    """Updates the conversation and warning messages after message refinement."""
    # Update chat accordingly
    conversation = replace_last_assistant_response(
        conversation, subsitute_message=refined_response
    )
    silent_print(
        "REJECTED responses was modified according to feedback from cheif judges"
    )
    # Remove old warnings that no longer apply, such as length warnings
    conversation = remove_system_messages_following_last_assistant_response(
        conversation
    )
    warning_messages = [
        f"Your message was corrected to comply with the following: '{warning_messages}'"
    ]
    return conversation, warning_messages
