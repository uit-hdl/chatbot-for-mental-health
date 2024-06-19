"""Functions for creating AI-monitors which oversee various parts of the
conversation and chatbot messages and provides feedback to prevent chatbot
identity drift. Overseer bots are assumed to generate a message on the form
`¤:provide_feedback(<data on JSON format>):¤`"""

from typing import Tuple

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


def ai_filter(conversation, harvested_syntax, chatbot_id):
    """Uses prompted AI-agents to evaluate the chatbots response. Returns the
    evaluation of the AI-judges (ACCEPT, WARNING, REJECT), and a list of warning
    messages ([] if no warnings). Currently AI checking stages:

    1. Check if the user consents to being redirected (if requesting redirect)
    2. Preliminary check of response using swift judges (using cheaper LLM)
    3. If flagged in S2: Evaluate with Chief judges (using expensive LLM)
    4. If Rejected in S3: Correct response so that it complies with warnings
    """
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

    # Update PROMPTS dictionary
    update_global_variables(chatbot_id)

    # Extract the overseer dictionary corresponding to the chatbot
    overseer_stages = OVERSEERS_CONFIG["chatbots"][chatbot_id]

    # Check for referals
    redirect_checkers = overseer_stages["redirect_consent_checkers"]
    if harvested_syntax["referral"] and redirect_checkers:
        overseer_evaluation = check_if_user_confirms_redirect(
            conversation, redirect_checkers
        )
        if overseer_evaluation == "ACCEPT":
            silent_print("Overseer confirms that user wants to be referred.")
        else:

            warning_messages.append(SYSTEM_MESSAGES["confirm_before_redirect"])

    else:
        # Evaluate with AI-judges
        cheif_evaluation, warning_messages, conversation = evaluate_with_ai_judges(
            chatbot_id, conversation, chatbot_citations
        )

    return cheif_evaluation, warning_messages, conversation


def evaluate_with_ai_judges(chatbot_id, conversation, chatbot_citations):
    """Runs the AI-response through the AI-filters - first the preliminary
    AI-judges (cheap LLMs) and, if flagged by the preliminary judges, then the
    Chief judges are activated to get the final evaluation. Each stage produces
    an evaluation (ACCEPT or REJECT) and a list of warning messages. If the
    message is rejected by the Chief judges, then another AI-agent will take the
    message and warning messages and modify it so that it complies with the
    system warnings."""
    # Set default values
    preliminary_evaluation = "ACCEPT"
    cheif_evaluation = "ACCEPT"
    warning_messages = []

    # Response type determines which AI-agents will screen the response
    response_labels = classify_response_based_on_citation(chatbot_citations)
    # Identify judges that handle that response type
    relevant_prelim_judges, relevant_cheif_judges = fetch_relevant_judges(
        chatbot_id, response_labels
    )

    # Collect variables required to complete the prompts of the relevant judges
    prompt_variables = collect_relevant_prompt_variables(
        conversation,
        relevant_prelim_judges,
        relevant_cheif_judges,
        chatbot_id,
        chatbot_citations,
    )

    # ** Preliminary check **
    if relevant_prelim_judges:
        preliminary_evaluation = get_evaluation_from_preliminary_judges(
            relevant_prelim_judges, prompt_variables
        )

    # ** Cheif overseers **
    if relevant_cheif_judges:
        if preliminary_evaluation == "REJECT":
            cheif_evaluation, warning_messages = get_evaluation_from_cheif_judges(
                relevant_cheif_judges, prompt_variables
            )

        # Correct rejected responses so that it complies with cheif judge feedback
        response_modifiers = OVERSEERS_CONFIG["chatbots"][chatbot_id][
            "chatbot_response_modifiers"
        ]
        if response_modifiers and cheif_evaluation == "REJECT":
            # Response modifier takes warning message as an input
            conversation, warning_messages = (
                correct_rejected_response_and_modify_chat_and_warning(
                    conversation,
                    prompt_variables,
                    response_modifiers,
                    warning_messages,
                )
            )
            # Set to ACCEPT again since response is corrected
            cheif_evaluation = "ACCEPT"

    return cheif_evaluation, warning_messages, conversation


def update_global_variables(chatbot_id):
    """Ensures that PROMPTS only contains prompts from assistant subfolder.
    Fills the source_communication field in CITATIONS with citations that
    correspond to that response class."""
    global PROMPTS, CITATIONS
    PROMPTS = collect_prompts_in_dictionary(chatbot_id)
    CITATIONS["source_communication"] = get_sources_available_to_chatbot(chatbot_id)


def classify_response_based_on_citation(chatbot_citations) -> list[str]:
    """Inferrs which "mode" the chatbot is in, e.g. default or source
    communicator."""
    class_matches = []
    for citation_class in CITATIONS.keys():
        overlap_between_citations_and_class = list_intersection(
            CITATIONS[citation_class], chatbot_citations
        )
        if overlap_between_citations_and_class:
            class_matches.append(citation_class)
    if not class_matches:
        raise ValueError(f"{chatbot_citations} does not match any citation classes.")
    return class_matches


def fetch_relevant_judges(chatbot_id, response_labels):
    """Decide which judges are relevant based on the classification of the
    response."""
    # Check which preliminary judges are relevant
    prelim_judges = OVERSEERS_CONFIG["chatbots"][chatbot_id]["preliminary_judges"]
    relevant_prelim_judges = reduce_to_relevant_only(prelim_judges, response_labels)
    # Check which chief judges are relevant
    overseers_cheif = OVERSEERS_CONFIG["chatbots"][chatbot_id]["chief_judges"]
    relevant_cheif_judges = reduce_to_relevant_only(overseers_cheif, response_labels)

    return relevant_prelim_judges, relevant_cheif_judges


def reduce_to_relevant_only(
    judge_list: list[dict], response_labels: list[str]
) -> list[str]:
    """Iterates over the dictionaries, each of which corresponds to a particular
    judge, and determines if it is relevant."""
    relevant_judges = []
    for judge_dict in judge_list:
        mode_that_activates_judge = judge_dict["associated_mode"]
        if mode_that_activates_judge in response_labels:
            relevant_judges.append(judge_dict)
    return relevant_judges


def collect_relevant_prompt_variables(
    conversation,
    relevant_prelim_judges: list[dict],
    relevant_cheif_judges: list[dict],
    chatbot_id: str,
    chatbot_citations: list[str],
) -> dict:
    """Collects variables that are inserted as variables in the overseer prompts
    in a dictionary, such as chatbot_message. Note: if you want to have a
    variable "... {var_name} ..." in your prompt, then you need to add it below
    and make sure the names in the code and prompt are identical."""
    # Get names of prompt variables needed to complete the prompts
    prompt_variable_names_prelim = get_nessecary_prompt_variables(
        relevant_prelim_judges
    )
    prompt_variable_names_cheif = get_nessecary_prompt_variables(relevant_cheif_judges)
    # Currently unused (idea is to use it to prevent needless computations)
    names_of_nessecary_prompt_variables = list(
        set(prompt_variable_names_prelim + prompt_variable_names_cheif)
    )

    nessecary_prompt_variables = {
        "chatbot_message": remove_syntax_from_message(
            grab_last_assistant_response(conversation)
        )
    }
    nessecary_prompt_variables["user_message"] = grab_last_user_message(conversation)
    # Source-based variables
    content_cited_sources = get_content_of_cited_sources(chatbot_citations, chatbot_id)
    if content_cited_sources:
        nessecary_prompt_variables["sources"] = string_together_cited_sources(
            content_cited_sources
        )
        # If source (singular) is requested, grabs only the first cited string [UPDATE]
        nessecary_prompt_variables["source"] = content_cited_sources[0]

    return nessecary_prompt_variables


def get_nessecary_prompt_variables(judges_list) -> list[str]:
    """Iterates over the values in the dictionary, extracts the names of the
    required prompt variables, and collects them in a list."""
    prompt_variable_names = [d["prompt_variables"] for d in judges_list]
    return sum(prompt_variable_names, [])


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
            preliminary_evaluation_from_ai_judge(
                judge_name=judge_dict["name"],
                prompt_variables=prompt_variables,
                failure_keyword=judge_dict["evaluation_keywords"][0],
            )
        )

    if not prelim_evaluations:
        raise ValueError(f"None evaluations obtained from preliminary judges")

    if "REJECT" in prelim_evaluations:
        return "REJECT"
    else:
        return "ACCEPT"


def preliminary_evaluation_from_ai_judge(
    judge_name: str, prompt_variables: dict, failure_keyword="REJECT"
):
    """Uses GPT-3.5-turbo-instruct to generate a preliminary quality check on source
    adherence. This evaluation is decent at catching deviations from source materials, but
    sometimes flags messages that are perfectly fine. If flagged, a more computationally
    expensive model is called to double check the evaluation."""
    prompt = PROMPTS[judge_name]
    prompt_completed = prompt.format(**prompt_variables)
    evaluation = generate_single_response_to_prompt(
        prompt_completed, model="gpt-35-turbo-16k"
    )
    dump_prompt_response_pair_to_md(prompt_completed, evaluation, judge_name)
    LOGGER.info(f"{judge_name}:\n{evaluation}")

    if failure_keyword in evaluation:
        silent_print(f"Message fails preliminary check by {judge_name}")
        return "REJECT"
    else:
        silent_print(f"Message passes preliminary check by {judge_name}")
        return "ACCEPT"


# *** CHEIF JUDGES ***


def get_evaluation_from_cheif_judges(
    relevant_cheif_judges: list[dict], prompt_variables: list[str]
):
    """Cheif judges evaluates the chatbots response. Returns evaluation (str) and
    list of warning messages (list)."""
    cheif_evaluations = []
    warning_messages = []
    for judge_dict in relevant_cheif_judges:
        evaluation, warning = cheif_judge_evaluation(
            judge_dict,
            prompt_variables,
        )
        cheif_evaluations.append(evaluation)
        warning_messages.append(warning)

    silent_print(f"chief_judge_source_fidelity evaluations: {cheif_evaluations}")

    if "REJECT" in cheif_evaluations:
        return "REJECT", warning_messages
    elif "WARNING" in cheif_evaluations:
        return "WARNING", warning_messages
    else:
        return "ACCEPT", []


def cheif_judge_evaluation(judge_dict, prompt_variables: dict):
    """Conducts a preliminary evaluation of the chatbots message using smart but
    expensive LLM."""
    prompt_completed = PROMPTS[judge_dict["name"]].format(**prompt_variables)

    response = generate_single_response_to_prompt(prompt_completed, model="gpt-4")

    dump_prompt_response_pair_to_md(prompt_completed, response, judge_dict["name"])
    LOGGER.info(f"{judge_dict['name']}:\n{response}")

    _, overseer_output = extract_command_names_and_arguments(response)

    overseer_evaluation = "ACCEPT"
    warning_message = []

    if overseer_output:
        evaluation_dict = convert_json_string_to_dict(overseer_output[0])
        overseer_evaluation, warning_message = extract_overseer_evaluation_and_feedback(
            evaluation_dict
        )

    return overseer_evaluation, warning_message


def extract_overseer_evaluation_and_feedback(
    evaluation_dict: dict,
    evaluation_keywords=["REJECT", "WARNING", "ACCEPT"],
) -> Tuple[str, str]:
    """Appends warning message under system if the overseer evaluation is
    WARNING` or NOT ACCEPTED`."""
    overseer_evaluation = "ACCEPT"
    warning_message = []
    if not overseer_response_is_valid(evaluation_dict):
        return overseer_evaluation, warning_message

    if evaluation_dict["evaluation"] == evaluation_keywords[0]:
        overseer_evaluation = "REJECT"
        warning_message = evaluation_dict["message_to_bot"]

    elif evaluation_dict["evaluation"] == evaluation_keywords[1]:
        overseer_evaluation = "WARNING"
        warning_message = evaluation_dict["message_to_bot"]

    else:
        overseer_evaluation = "ACCEPT"

    return overseer_evaluation, warning_message


def overseer_response_is_valid(evaluation_dict: dict) -> bool:
    """Checks the dictionary extracted from the overseer response follows the
    expected conventions."""
    if not evaluation_dict:
        return False
    if "evaluation" in evaluation_dict.keys():
        if "message_to_bot" in evaluation_dict.keys():
            return True
    return False


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
    conversation = replace_last_assistant_response(
        conversation, replacement_content=response_corrected
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
    # Extract and put into formatted string
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
        prompt_completed, response, "referral_consent_checker"
    )
    failure_keyword = redirect_checker["evaluation_keywords"][0]
    if failure_keyword in response:
        silent_print(f"Message fails preliminary check by {redirect_checker['name']}")
        return "REJECT"
    else:
        silent_print(f"Message passes preliminary check by {redirect_checker['name']}")
        return "ACCEPT"
