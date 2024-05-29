"""Functions for creating AI-monitors which oversee various parts of the
conversation and chatbot messages and provides feedback to prevent chatbot
identity drift. Overseer bots are assumed to generate a message on the form
`¤:provide_feedback(<data on JSON format>):¤`"""

from typing import Tuple

from utils.backend import get_source_content_and_path
from utils.backend import convert_json_string_to_dict
from utils.backend import get_sources_available_to_chatbot
from utils.backend import dump_prompt_response_pair_to_md
from utils.backend import dump_file
from utils.backend import PRE_SUMMARY_DUMP_PATH
from utils.backend import PROMPTS
from utils.backend import MODEL_TO_DEPLOYMENT_MAP
from utils.backend import CONFIG
from utils.backend import SETTINGS
from utils.backend import SYSTEM_MESSAGES
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import replace_last_assistant_response
from utils.chat_utilities import (
    remove_system_messages_following_last_assistant_response,
)
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import generate_single_response_to_prompt
from utils.process_syntax import extract_command_names_and_arguments
from utils.process_syntax import get_commands
from utils.process_syntax import insert_commands
from utils.general import list_intersection
from utils.general import list_subtraction
from utils.general import remove_syntax_from_message
from utils.general import silent_print

# Classifications are dummy-citations that do not reference a source but serves to
# classify the bots response.
MESSAGE_CLASSIFICATIONS = [
    "initial_prompt",
    "sources_dont_contain_answer",
    "no_advice_or_claims",
    "support_phone_number",
    "the_architect",
    "sources_dont_contain_answer",
]


def evaluate_with_overseers(conversation, harvested_syntax, chatbot_id):
    """Overseer agents checks rule-adherence of the response generated by the
    main chatbot. The overseer that checks the response is selected based on
    which citation the chatbot uses. For example, `¤:cite(["some_source"]):¤`
    will activate the source-fidelity overseer which compares the bots response
    to the cited source, and `¤:cite(["no_advice_or_claims"]):¤ will activate
    the miscellaneous overseer which checks "non-factual" responses.

    If the overseer evaluation is "ACCEPTED" then warning_message = [] is
    returned. If evaluation is "REJECTED" then message gets replaced by
    corrected response so that it complies with system warning."""

    available_sources = get_sources_available_to_chatbot(chatbot_id)
    citations = harvested_syntax["citations"]

    if harvested_syntax["referral"]:
        overseer_evaluation = user_confirms_they_want_redirect(conversation)
        if overseer_evaluation == "ACCEPTED":
            silent_print("Overseer confirms that user wants to be referred.")
            warning_message = []
        else:
            warning_message = SYSTEM_MESSAGES["confirm_before_redirect"]

    elif list_intersection(available_sources, citations):
        overseer_evaluation, warning_message, conversation = (
            overseer_evaluates_source_fidelity(conversation, citations, chatbot_id)
        )

    else:
        overseer_evaluation, warning_message, conversation = (
            overseer_evaluates_default_mode_messages(conversation, citations)
        )

    return overseer_evaluation, warning_message, conversation


# -- SOURCE FIDELITY BOT --
def overseer_evaluates_source_fidelity(
    conversation, citations: list, chatbot_id: str
) -> list:
    """An overseer bot checks fidelity of bot response to the source it cites.
    Only considers citations that reference files containing information, as
    opposed to dummy citations that are used classify what type of response the
    bot is giving."""
    chatbot_message = grab_last_assistant_response(conversation)
    chatbot_message = remove_syntax_from_message(chatbot_message)
    # Remove citatons that do not reference a source (only label the response)
    source_citations = list_subtraction(citations, MESSAGE_CLASSIFICATIONS)

    if source_citations:
        sources = [
            get_source_content_and_path(chatbot_id, name)[0]
            for name in source_citations
        ]
        preliminary_opinion = preliminary_check_of_source_fidelity(
            sources, chatbot_message
        )

        if preliminary_opinion == "ACCEPTED":
            warning_message = []
            return "ACCEPTED", warning_message, conversation
        else:
            silent_print(f"** SOURCE-FIDELITY MESSAGE CHECK **")
            silent_print("Message flagged in preliminary check by GPT-3.5.")

        prompt_completed = fill_in_prompt_template_for_source_fidelity_overseer(
            chatbot_message, sources
        )
        evaluation_dict = generate_overseer_response(
            prompt=prompt_completed,
        )
        silent_print(f"chief_judge_default raw evaluation: {evaluation_dict}")
        overseer_evaluation, warning_message = extract_overseer_evaluation_and_feedback(
            evaluation_dict
        )
        if overseer_evaluation == "REJECTED":
            conversation, warning_message = (
                correct_rejected_response_and_modify_chat_and_warning_accordingly(
                    conversation, chatbot_message, warning_message
                )
            )
            overseer_evaluation = "WARNING"

    else:
        overseer_evaluation = "ACCEPTED"
        warning_message = []

    return overseer_evaluation, warning_message, conversation


def preliminary_check_of_source_fidelity(
    sources: list[str],
    chatbot_message: str,
    prompt=PROMPTS["swift_judge_source_fidelity"],
):
    """Uses GPT-3.5-turbo-instruct to generate a preliminary quality check on source
    adherence. This evaluation is decent at catching deviations from source materials, but
    sometimes flags messages that are perfectly fine. If flagged, a more computationally
    expensive model is called to double check the evaluation."""
    source = sources[0]
    prompt_completed = prompt.format(chatbot_message=chatbot_message, source=source)
    evaluation = generate_single_response_to_prompt(
        prompt_completed, model="gpt-35-turbo-16k"
    )
    dump_prompt_response_pair_to_md(
        prompt_completed, evaluation, "swift_judge_source_fidelity"
    )

    if "NOT_SUPPORTED" in evaluation:
        silent_print(f"Message fails preliminary source-fidelity check")
        return "WARNING"
    else:
        silent_print(f"Message passes preliminary source-fidelity check")
        return "ACCEPTED"


def fill_in_prompt_template_for_source_fidelity_overseer(
    chatbot_message: str,
    sources: list[str],
    prompt_template=PROMPTS["chief_judge_source_fidelity"],
) -> str:
    """Takes the response generated by the chatbot and a list of sources
    that the bot cites to support its message and inserts them into the prompt
    template to produce the prompt for the source-fidelity overseer."""
    source_texts = ""
    for i, source in enumerate(sources):
        source_texts += f"source {i}: '{source}'\n\n"
    prompt_completed = prompt_template.format(
        chatbot_message=chatbot_message, sources=source_texts
    )
    return prompt_completed


def generate_overseer_response(
    prompt: str,
    model="gpt-4",
) -> dict:
    """Generates the response of the overseer (uses GPT-4) and returns it as a
    dictionary."""
    response = generate_single_response_to_prompt(prompt, model)
    _, overseer_evaluation = extract_command_names_and_arguments(response)
    if overseer_evaluation:
        evaluation_dict = convert_json_string_to_dict(overseer_evaluation[0])
    else:
        evaluation_dict = None
    dump_prompt_response_pair_to_md(prompt, response, "chief_judge_evaluation")

    return evaluation_dict


def extract_overseer_evaluation_and_feedback(
    evaluation_dict: dict,
) -> Tuple[str, str]:
    """Appends warning message under system if the overseer evaluation is
    WARNING` or NOT ACCEPTED`."""
    overseer_evaluation = "ACCEPTED"
    warning_message = []
    if evaluation_dict and overseer_response_is_valid(evaluation_dict):

        if evaluation_dict["evaluation"] != "ACCEPTED":
            silent_print(evaluation_dict)
            overseer_evaluation = evaluation_dict["evaluation"]
            warning_message = evaluation_dict["message_to_bot"]

    return overseer_evaluation, warning_message


def overseer_response_is_valid(overseer_dict: dict) -> bool:
    """Checks the dictionary extracted from the overseer response follows the
    expected conventions."""
    if "evaluation" in overseer_dict.keys():
        if "message_to_bot" in overseer_dict.keys():
            return True
    return False


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


# -- OVERSEER OF MISCELLANEOUS/NON-FACTUAL MESSAGES --
def overseer_evaluates_default_mode_messages(conversation, citations: list):
    """This bot is responsible for monitoring and evaluating bot messages that
    do NOT cite sources. These are messages that cite the initial prompt, refers
    the user to emergency phone number, or explain basic things that are not
    coming directly from a scripted source."""
    # Remove citatons that do NOT reference a source (they label the response)
    default_mode_citations = [
        source for source in citations if source in MESSAGE_CLASSIFICATIONS
    ]
    default_mode_citations = list_intersection(MESSAGE_CLASSIFICATIONS, citations)

    overseer_evaluation = "ACCEPTED"
    warning_message = []

    if default_mode_citations:
        user_message = grab_last_user_message(conversation)
        chatbot_message = grab_last_assistant_response(conversation)
        chatbot_message = remove_syntax_from_message(chatbot_message)
        swift_judgement = preliminary_check_of_default_mode_message(
            user_message, chatbot_message
        )
        if swift_judgement != "ACCEPTED":
            prompt = PROMPTS["chief_judge_default"].format(
                user_message=user_message, chatbot_message=chatbot_message
            )
            evaluation_dict = generate_overseer_response(prompt)
            silent_print(f"chief_judge_default raw evaluation: {evaluation_dict}")
            overseer_evaluation, warning_message = (
                extract_overseer_evaluation_and_feedback(evaluation_dict)
            )
            if overseer_evaluation == "REJECTED":
                conversation, warning_message = (
                    correct_rejected_response_and_modify_chat_and_warning_accordingly(
                        conversation, chatbot_message, warning_message
                    )
                )
                overseer_evaluation = "WARNING"

    return overseer_evaluation, warning_message, conversation


def preliminary_check_of_default_mode_message(
    user_message: str,
    chatbot_message: str,
):
    """Uses GPT-3.5-turbo-instruct to screen for behaviours that violates the
    chatbots role limitations."""
    # Disclaimer check
    prompt_disclaimer_check = PROMPTS["swift_judge_disclaimer_check"].format(
        user_message=user_message, chatbot_message=chatbot_message
    )
    evaluation_disclaimer = generate_single_response_to_prompt(
        prompt_disclaimer_check, model="gpt-35-turbo-16k"
    )
    dump_prompt_response_pair_to_md(
        prompt_disclaimer_check,
        evaluation_disclaimer,
        dump_name="swift_judge_disclaimer_check",
    )

    # Role and referral to emergency contact check
    prompt_role_check = PROMPTS["swift_judge_role_and_emergency_contact"].format(
        user_message=user_message, chatbot_message=chatbot_message
    )
    evaluation_role = generate_single_response_to_prompt(
        prompt_role_check, model="gpt-35-turbo-16k"
    )
    dump_prompt_response_pair_to_md(
        prompt_role_check,
        evaluation_role,
        dump_name="swift_judge_role_and_emergency_contact",
    )

    silent_print(f"** DEFAULT MODE MESSAGE CHECK **")
    silent_print(f"swift-judge disclaimer check: {evaluation_disclaimer}")
    silent_print(f"swift-judge role check: {evaluation_role}")

    disclaimer_check_passed = "AGREE" in evaluation_disclaimer
    role_check_passed = "ACCEPTED" in evaluation_role

    silent_print(f"Message passes disclaimer-check: {disclaimer_check_passed}")
    silent_print(f"Message passes role-check: {role_check_passed}")

    if disclaimer_check_passed and role_check_passed:
        return "ACCEPTED"
    else:
        return "WARNING"


def user_confirms_they_want_redirect(
    conversation,
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
    # Insert into prompt
    prompt_completed = PROMPTS["referral_consent_checker"].format(
        last_2_messages=last_2_messages
    )
    # Generate response
    response = generate_single_response_to_prompt(prompt_completed, model)
    dump_prompt_response_pair_to_md(
        prompt_completed, response, "referral_consent_checker"
    )
    if "True" in response:
        return "ACCEPTED"
    else:
        "NOT ACCEPTED"
