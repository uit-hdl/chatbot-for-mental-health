"""Functions for creating AI-monitors which oversee various parts of the
conversation and chatbot messages and provides feedback to prevent chatbot
identity drift. Overseer bots are assumed to generate a message on the form
`¤:provide_feedback(<data on JSON format>):¤`"""

from typing import Tuple
import re

from utils.backend import get_source_content_and_path
from utils.backend import convert_json_string_to_dict
from utils.backend import get_sources_available_to_chatbot
from utils.backend import dump_prompt_response_pair_to_md
from utils.backend import OVERSEERS_CONFIG
from utils.backend import CITATIONS
from utils.backend import SYSTEM_MESSAGES
from utils.backend import collect_prompts_in_dictionary
from utils.backend import LOGGER
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import replace_last_assistant_response
from utils.chat_utilities import (
    remove_system_messages_following_last_assistant_response,
)
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import generate_single_response_to_prompt
from utils.chat_utilities import index_of_assistant_responses_intended_for_user
from utils.process_syntax import extract_command_names_and_arguments
from utils.general import list_intersection
from utils.general import remove_syntax_from_message
from utils.general import silent_print


CITATIONS_DEFAULT = [
    "initial_prompt",
    "sources_dont_contain_answer",
    "no_advice_or_claims",
    "support_phone_number",
    "the_architect",
    "sources_dont_contain_answer",
]
CITATIONS_SOURCES = []


def ai_filter(conversation, harvested_syntax, chatbot_id):
    """Uses prompted AI-agents - monitors - to evaluate and give feedback on the
    chatbots response. Returns the evaluation of the AI-judges (ACCEPT, WARNING,
    REJECT), and a list of warning messages ([] if no warnings). The stages are:

    1. Check if the user consents to being redirected (if requesting redirect)
    2. Preliminary check of response using swift judges (using cheaper LLM)
    3. If flagged in 2: Evaluate with Chief judges (using expensive LLM)
    4. If Rejected in 3: Correct response so that it complies with warnings
    """
    global PROMPTS, CITATIONS
    # from utils.backend import load_json_from_path
    # from utils.backend import (
    #     get_file_names_in_directory,
    #     get_subfolder_of_assistant,
    #     os,
    #     PROMPTS_DIR,
    # )
    # chatbot_id = "mental_health"
    # conversation = load_json_from_path(
    #     "results/chat-dumps/ai_thinks_it_is_socialisation_expert/conversation.json"
    # )[:-10]
    # # conversation = load_json_from_path(
    # #     "chat-dashboard/conversation.json"
    # # )[]
    # harvested_syntax = load_json_from_path(
    #     "results/chat-dumps/ai_thinks_it_is_socialisation_expert/harvested_syntax.json"
    # )
    # # harvested_syntax["citations"] = []
    # prompts = get_file_names_in_directory(
    #     # os.path.join(PROMPTS_DIR, get_subfolder_of_assistant(chatbot_id))
    # )

    chatbot_citations = harvested_syntax["citations"]

    # Set default ouptut values
    cheif_evaluation = "ACCEPT"
    warning_messages = []

    # Update PROMPTS and CITATIONS dictionaries
    PROMPTS = collect_prompts_in_dictionary(chatbot_id)
    CITATIONS["source_communication"] = get_sources_available_to_chatbot(chatbot_id)

    # Check for referals
    redirect_checkers = OVERSEERS_CONFIG[chatbot_id]["redirect_consent_checkers"]

    if harvested_syntax["referral"] and redirect_checkers:
        overseer_evaluation = check_if_user_confirms_redirect(
            conversation, redirect_checkers
        )
        if overseer_evaluation == "ACCEPT":
            silent_print("Overseer confirms that user wants to be referred.")
        else:
            warning_messages.append(SYSTEM_MESSAGES["confirm_before_redirect"])
    else:
        overseers = OVERSEERS_CONFIG[chatbot_id]
        content_of_cited_sources = get_content_of_cited_sources(
            chatbot_citations, chatbot_id
        )
        # Evaluate with AI-judges
        cheif_evaluation, warning_messages, conversation = evaluate_with_ai_judges(
            preliminary_judges=overseers["preliminary_judges"],
            chief_judges=overseers["chief_judges"],
            content_of_cited_sources=content_of_cited_sources,
            response_modifiers=overseers["chatbot_response_modifiers"],
            conversation=conversation,
            chatbot_citations=chatbot_citations,
        )

    return cheif_evaluation, warning_messages, conversation


def evaluate_with_ai_judges(
    preliminary_judges,
    chief_judges,
    response_modifiers,
    content_of_cited_sources,
    conversation,
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
    cheif_verdict = "ACCEPT"
    warning_messages = []

    # Find judges that are suitable for the current response categories
    relevant_prelim_judges = identify_relevant_judges(
        preliminary_judges, chatbot_citations
    )
    relevant_cheif_judges = identify_relevant_judges(chief_judges, chatbot_citations)

    # Collect variables that complete the prompts of the judges
    prompt_variables = prepare_prompt_variables(
        conversation,
        content_of_cited_sources,
    )

    # ** Preliminary check **
    if relevant_prelim_judges:
        preliminary_verdict = get_evaluation_from_preliminary_judges(
            relevant_prelim_judges, prompt_variables
        )

    # ** Cheif overseers **
    if relevant_cheif_judges:
        if preliminary_verdict == "REJECT":
            cheif_verdict, warning_messages = get_evaluation_from_cheif_judges(
                relevant_cheif_judges, prompt_variables
            )

        # ** Response modification **
        if response_modifiers and cheif_verdict == "REJECT":
            # Modify response to comply with feedback from cheif-judges
            conversation, warning_messages = (
                correct_rejected_response_and_modify_chat_and_warning(
                    conversation,
                    prompt_variables,
                    response_modifiers,
                    warning_messages,
                )
            )
            # Set to ACCEPT again since response is now corrected
            cheif_verdict = "ACCEPT"

    return cheif_verdict, warning_messages, conversation


def inferr_response_categories(chatbot_citations) -> list[str]:
    """Inferrs which "mode" the chatbot is in, e.g. default or
    source_communication."""
    modes_activated = []
    response_categories = CITATIONS.keys()
    for chatbot_mode in response_categories:
        overlap_between_citations_and_class = list_intersection(
            CITATIONS[chatbot_mode], chatbot_citations
        )
        if overlap_between_citations_and_class:
            modes_activated.append(chatbot_mode)
    if not modes_activated:
        raise ValueError(f"{chatbot_citations} does not match any citation classes.")
    return modes_activated


def identify_relevant_judges(
    judge_list: list[dict], chatbot_citations: list[str]
) -> list[str]:
    """Iterates over the dictionaries, each of which corresponds to a particular
    judge, and determines if it is relevant."""
    response_categories = inferr_response_categories(chatbot_citations)
    relevant_judges = []
    for judge_dict in judge_list:
        mode_that_activates_judge = judge_dict["associated_mode"]
        if mode_that_activates_judge in response_categories:
            relevant_judges.append(judge_dict)
    return relevant_judges


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


def get_content_of_cited_sources(chatbot_citations, chatbot_id) -> list[str]:
    """Fetches the content of the sources cited by the chatbot, if any."""
    cited_sources = list_intersection(
        chatbot_citations, CITATIONS["source_communication"]
    )
    contents_of_cited_sources = []
    if cited_sources:
        for source_name in cited_sources:
            contents_of_cited_sources.append(
                get_source_content_and_path(chatbot_id, source_name)[0]
            )

    return contents_of_cited_sources


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


# *** PRELIMINARY JUDGES ***


def get_evaluation_from_preliminary_judges(
    relevant_prelim_judges: list[dict], prompt_variables: dict
) -> str:
    """Iterates over the relevant preliminary judges and obtains evaluations
    from each. Converts evaluations to either REJECT or ACCEPT. If one
    preliminary judge flags the message, it gets passed on to the cheif judges
    (that uses GPT 4). prompt_variables contains the variables needed to
    complete the prompt templates of the relevant judges."""
    prelim_evaluations = []

    for judge_dict in relevant_prelim_judges:
        prelim_evaluations.append(
            get_verdict_from_preliminary_judge(
                judge_name=judge_dict["name"],
                prompt_variables=prompt_variables,
                keyword_to_verdict_map=judge_dict["verdict"],
            )
        )

    if not prelim_evaluations:
        raise ValueError(f"None evaluations obtained from preliminary judges")

    if "REJECT" in prelim_evaluations:
        return "REJECT"
    else:
        return "ACCEPT"


def get_verdict_from_preliminary_judge(
    judge_name: str, prompt_variables: dict, keyword_to_verdict_map: dict
):
    """Uses GPT-3.5-turbo-instruct to do a preliminary check of fidelity to
    cited sources. This evaluation is decent at catching deviations from source
    materials, but sometimes flags messages that are perfectly fine. If flagged,
    a more computationally expensive model is called to double check the
    evaluation."""
    prompt = PROMPTS[judge_name]
    prompt_completed = prompt.format(**prompt_variables)
    judge_response = generate_single_response_to_prompt(
        prompt_completed, model="gpt-35-turbo-16k"
    )
    verdict = convert_overseer_response_to_official_verdict(
        judge_response, keyword_to_verdict_map
    )
    dump_prompt_response_pair_to_md(
        prompt_completed, judge_response, judge_name, verdict
    )
    LOGGER.info(f"{judge_name}:\n{judge_response}")

    return verdict


def convert_overseer_response_to_official_verdict(
    overseer_response, keyword_to_verdict_map: dict
):
    """The overseer outputs a string which contains evaluation keywords like
    AGREE or WARNING. This functions map these keywords to official verdicts
    which are used in subsequent nodes in the decision tree. The verdict map
    shows the verdict that each keyword maps to."""
    verdict = "ACCEPT"
    for keyword in keyword_to_verdict_map.keys():
        if keyword in overseer_response:
            verdict = keyword_to_verdict_map[keyword]
    return verdict


# *** CHEIF JUDGES ***


def get_evaluation_from_cheif_judges(
    relevant_cheif_judges: list[dict], prompt_variables: list[str]
):
    """Cheif judges evaluates the chatbots response. Returns evaluation (str) and
    list of warning messages (list)."""
    cheif_evaluations = []
    warning_messages = []
    for judge_dict in relevant_cheif_judges:
        evaluation, feedback = get_cheif_judge_feedback_and_verdict(
            judge_dict,
            prompt_variables,
        )
        cheif_evaluations.append(evaluation)
        if feedback:
            warning_messages.append(feedback)

    silent_print(f"chief_judge_source_fidelity evaluations: {cheif_evaluations}")

    if "REJECT" in cheif_evaluations:
        return "REJECT", warning_messages
    elif "WARNING" in cheif_evaluations:
        return "WARNING", warning_messages
    else:
        return "ACCEPT", []


def get_cheif_judge_feedback_and_verdict(judge_dict, prompt_variables: dict):
    """Produces a final verdict and feedback for the chatbot response using
    smart but expensive LLM."""
    prompt_completed = PROMPTS[judge_dict["name"]].format(**prompt_variables)
    overseer_response = generate_single_response_to_prompt(
        prompt_completed, model="gpt-4"
    )
    verdict = extract_field_content(overseer_response, "VERDICT")
    feedback = extract_field_content(overseer_response, "FEEDBACK")
    if verdict == "ACCEPT":
        feedback = None

    dump_prompt_response_pair_to_md(
        prompt_completed, overseer_response, judge_dict["name"], verdict
    )
    LOGGER.info(f"{judge_dict['name']}:\n{overseer_response}")

    if not verdict:
        raise ValueError(
            "'verdict' must be present in the cheif judges response."
        )
    else:
        return verdict, feedback


def extract_field_content(text, field_name="VERDICT"):
    """Extracts the content of the specified field from the string.
    Assumes that the following format is used in the response:

    FIELD_NAME: "..."."""
    # Define regular expression pattern to extract the field content
    pattern = rf'{field_name}:\s*"([^"]*)"'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return None


# *** HANDLING REJECTED RESPONSES ***


def correct_rejected_response_and_modify_chat_and_warning(
    conversation,
    prompt_variables: dict,
    response_modifiers: dict,
    warning_messages: list[str],
):
    """An AI agent corrects the message generated by the chatbot so that it
    complies with the systems warning. Returns updated conversation and
    warning_message."""

    response_modifier = response_modifiers[0]  # Currently only one response modifier
    prompt_variables["system_message"] = "\n\n".join(warning_messages)
    response_corrected = correct_rejected_response(prompt_variables, response_modifier)

    # Update chat accordingly
    conversation = replace_last_assistant_response(
        conversation, subsitute_message=response_corrected
    )
    # Remove old warnings that no longer apply, such as length warnings
    conversation = remove_system_messages_following_last_assistant_response(
        conversation
    )
    warning_messages = [
        f"Your message was corrected to comply with the following: '{warning_messages}'"
    ]
    return conversation, warning_messages


def correct_rejected_response(prompt_variables: dict, response_modifier: dict) -> str:
    """An AI agent has been prompted to correct the message generated by the
    chatbot so that it complies with the systems warning. Typically replaces an
    out-of-scope response with a more standard 'I am not allowed to talk about
    that'-type message."""
    prompt_completed = PROMPTS[response_modifier["name"]].format(**prompt_variables)
    corrected_response = generate_single_response_to_prompt(prompt_completed, "gpt-4")
    # Use the no_advice_or_claims or claims response label
    corrected_response = f'¤:cite(["no_advice_or_claims"]):¤ {corrected_response}'
    silent_print("** Rejected message substituted **")
    dump_prompt_response_pair_to_md(
        prompt_completed, corrected_response, "corrected_response.md"
    )
    return corrected_response


def check_if_user_confirms_redirect(
    conversation,
    redirect_checkers: list,
    model="gpt-35-turbo-16k",
) -> str:
    """Checks if the user has confirmed that they want to be referred to another
    assistant, assuming that a referral request has been issued. AI agent checks
    the two messages preceeding the redirect command."""
    # Grab the last two messages before the referral request (initial prompt excluded)
    chat_last2 = conversation[1:-1][-2:]
    # Extract messages and put into formatted string
    last_2_messages = "\n\n".join(
        [f"{message['role']}: {message['content']}" for message in chat_last2]
    )
    # Currently only one agent used in this stage
    redirect_checker = redirect_checkers[0]
    # Insert variables into prompt
    prompt_completed = PROMPTS[redirect_checker["name"]].format(
        last_2_messages=last_2_messages
    )
    # Generate response
    response = generate_single_response_to_prompt(prompt_completed, model)
    dump_prompt_response_pair_to_md(
        prompt_completed, response, dump_name="referral_consent_checker"
    )
    failure_keyword = redirect_checker["evaluation_keywords"][0]

    if failure_keyword in response:
        silent_print(f"Message fails preliminary check by {redirect_checker['name']}")
        return "REJECT"
    else:
        silent_print(f"Message passes preliminary check by {redirect_checker['name']}")
        return "ACCEPT"
