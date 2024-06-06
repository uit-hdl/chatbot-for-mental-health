"""Functions for creating AI-monitors which oversee various parts of the
conversation and chatbot messages and provides feedback to prevent chatbot
identity drift. Overseer bots are assumed to generate a message on the form
`¤:provide_feedback(<data on JSON format>):¤`"""

from typing import Tuple

from utils.backend import get_source_content_and_path
from utils.backend import convert_json_string_to_dict
from utils.backend import get_sources_available_to_chatbot
from utils.backend import dump_prompt_response_pair_to_md
from utils.backend import PROMPTS_DIR
from utils.backend import OVERSEERS_CONFIG
from utils.backend import CITATIONS
from utils.backend import collect_prompts_in_dictionary
from utils.backend import LOGGER
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import replace_last_assistant_response
from utils.chat_utilities import (
    remove_system_messages_following_last_assistant_response,
)
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import generate_single_response_to_prompt
from utils.process_syntax import extract_command_names_and_arguments
from utils.general import list_intersection
from utils.general import list_subtraction
from utils.general import remove_syntax_from_message
from utils.general import silent_print
from utils.backend import load_json_from_path
from utils.backend import get_file_names_in_directory
from utils.backend import get_subfolder_of_assistant
import os


def evaluate_with_overseers(chatbot_id, conversation, chatbot_citations):
    # chatbot_id = "mental_health"
    # conversation = load_json_from_path(
    #     "results/chat-dumps/ai_thinks_it_is_socialisation_expert/conversation.json"
    # )[:-8]
    # harvested_syntax = load_json_from_path(
    #     "results/chat-dumps/ai_thinks_it_is_socialisation_expert/harvested_syntax.json"
    # )
    # # chatbot_citations = harvested_syntax["citations"]
    # chatbot_citations = ["13_stigma"]
    # prompts = get_file_names_in_directory(
    #     os.path.join(PROMPTS_DIR, get_subfolder_of_assistant(chatbot_id))
    # )
    update_global_variables(chatbot_id)

    # Response type is needed to know which chatbot to activate
    response_labels = classify_response_based_on_citation(chatbot_citations)
    relevant_prelim_judges, relevant_cheif_judges = fetch_relevant_judges(
        chatbot_id, response_labels
    )
    # Collect the variables that are required to complete the prompts of the
    # relevant judges
    prompt_variables = collect_relevant_prompt_variables(
        conversation,
        relevant_prelim_judges,
        relevant_cheif_judges,
        chatbot_id,
        chatbot_citations,
    )

    preliminary_evaluation = get_evaluation_from_preliminary_judges(
        relevant_prelim_judges, prompt_variables
    )

    if preliminary_evaluation == "REJECT":
        cheif_evaluation, warning_messages = get_evaluation_from_cheif_judges(
            relevant_cheif_judges, prompt_variables
        )
    else:
        cheif_evaluation = "ACCEPT"
        warning_messages = []

    return cheif_evaluation, warning_messages


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
    overseers_prelim = OVERSEERS_CONFIG["chatbots"][chatbot_id]["preliminary_judges"]
    relevant_prelim_judges = reduce_to_relevant_only(overseers_prelim, response_labels)
    # Check which chief judges are relevant
    overseers_cheif = OVERSEERS_CONFIG["chatbots"][chatbot_id]["chief_judges"]
    relevant_cheif_judges = reduce_to_relevant_only(overseers_cheif, response_labels)

    return relevant_prelim_judges, relevant_cheif_judges


def reduce_to_relevant_only(overseers_dict, response_labels):
    """Iterates over the dictionaries, each of which corresponds to a particular
    judge, and determines if it is relevant."""
    relevant_judges = {}
    for judge_name, judge_dict in overseers_dict.items():
        mode_that_triggers_judge = judge_dict["associated_mode"]
        if mode_that_triggers_judge in response_labels:
            relevant_judges[judge_name] = judge_dict
    return relevant_judges


def collect_relevant_prompt_variables(
    conversation,
    relevant_prelim_judges,
    relevant_cheif_judges,
    chatbot_id,
    chatbot_citations,
) -> dict:
    """Collects variables (e.g. user message, chatbot message, sources) needed
    to complete the overseer prompts in a dictionary."""
    # Get names of prompt variables
    prompt_variable_names_prelim = get_nessecary_prompt_variables(
        relevant_prelim_judges
    )
    prompt_variable_names_cheif = get_nessecary_prompt_variables(relevant_cheif_judges)
    names_of_nessecary_prompt_variables = list(
        set(prompt_variable_names_prelim + prompt_variable_names_cheif)
    )
    cited_sources = get_cited_sources(chatbot_citations, chatbot_id)

    nessecary_prompt_variables = {
        "chatbot_message": remove_syntax_from_message(
            grab_last_assistant_response(conversation)
        )
    }

    # Optional prompt variables
    if "user_message" in names_of_nessecary_prompt_variables:
        nessecary_prompt_variables["user_message"] = grab_last_user_message(
            conversation
        )

    if "sources" in names_of_nessecary_prompt_variables:
        nessecary_prompt_variables["sources"] = string_together_cited_sources(
            cited_sources
        )

    if "source" in names_of_nessecary_prompt_variables:
        # If source (singular) is requested, grabs only the first cited string
        # (requires UPDATE)
        nessecary_prompt_variables["source"] = cited_sources[0]

    if nessecary_prompt_variables == {}:
        raise ValueError(
            f"Request prompt variables {names_of_nessecary_prompt_variables} not valid."
        )

    return nessecary_prompt_variables


def get_nessecary_prompt_variables(judges_dict) -> list[str]:
    """Iterates over the values in the dictionary, extracts the names of the
    required prompt variables, and collects them in a list."""
    prompt_variable_names = [d["prompt_variables"] for d in judges_dict.values()]
    return sum(prompt_variable_names, [])


def get_cited_sources(chatbot_citations, chatbot_id) -> list[str]:
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
    relevant_prelim_judges: dict, prompt_variables: dict
) -> str:
    """Iterates over the relevant preliminary judges and obtains evaluations
    from each. Converts evaluations to either REJECT or ACCEPT. If one
    preliminary judge flags the message, it gets passed on to the cheif judges
    (that uses GPT 4). prompt_variables contains the variables needed to
    complete the prompt templates of the relevant judges."""
    prelim_evaluations = []
    for judge_name, judge_dict in relevant_prelim_judges.items():
        prelim_evaluations.append(
            preliminary_evaluation_from_ai_judge(
                judge_name=judge_name,
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


def get_evaluation_from_cheif_judges(relevant_cheif_judges, prompt_variables):
    cheif_evaluations = []
    warning_messages = []
    for judge_name, judge_dict in relevant_cheif_judges.items():
        evaluation, warning = cheif_judge_evaluation(
            prompt_name=judge_name,
            prompt_variables=prompt_variables,
            evaluation_keywords=judge_dict["evaluation_keywords"],
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


def cheif_judge_evaluation(prompt_name, prompt_variables: dict, evaluation_keywords):
    """Conducts a preliminary evaluation of the chatbots message using GPT-3.5."""
    prompt_completed = PROMPTS[prompt_name].format(**prompt_variables)

    response = generate_single_response_to_prompt(prompt_completed, model="gpt-4")

    dump_prompt_response_pair_to_md(prompt_completed, response, prompt_name)
    LOGGER.info(f"{prompt_name}:\n{response}")

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


def correct_rejected_response_and_modify_chat_and_warning_accordingly(
    conversation, chatbot_message, warning_message
):
    """An AI agent corrects the message generated by the chatbot so that it
    complies with the systems warning. Returns updated conversation and
    warning_message."""
    response_corrected = correct_rejected_response(
        user_message=grab_last_user_message(conversation),
        chatbot_message=chatbot_message,
        system_message=warning_message,
    )
    conversation = replace_last_assistant_response(
        conversation, replacement_content=response_corrected
    )
    # Warnings, such as length warnings, following corrected response are not needed
    conversation = remove_system_messages_following_last_assistant_response(
        conversation
    )
    warning_message = [
        f"Your message was corrected to comply with the following: '{warning_message}'"
    ]
    return conversation, warning_message


def correct_rejected_response(user_message, chatbot_message, system_message) -> str:
    """An AI agent has been prompted to correct the message generated by the
    chatbot so that it complies with the systems warning. Typically replaces an
    out-of-scope response with a more standard 'I am not allowed to talk about
    that'-type message."""
    prompt_completed = PROMPTS["conversation_killer"].format(
        user_message=user_message,
        chatbot_message=chatbot_message,
        system_message=system_message,
    )
    corrected_response = generate_single_response_to_prompt(prompt_completed, "gpt-4")
    corrected_response = f'¤:cite(["no_advice_or_claims"]):¤ {corrected_response}'
    silent_print("** Rejected message substituted **")
    return corrected_response
