"""Functions for creating external overseer bots which various parts of the conversation
and chatbot messages and provides feedback to prevent chatbot identity drift. Overseer
bots are assumed to generate a message on the form `¤:provide_feedback(<data on JSON
format>):¤`"""

from typing import Tuple
import os

from utils.backend import get_source_content_and_path
from utils.backend import dump_to_json
from utils.backend import dump_chat_to_markdown
from utils.backend import convert_json_string_to_dict
from utils.backend import get_sources_available_to_chatbot
from utils.backend import dump_overseer_interactions
from utils.backend import dump_file
from utils.backend import OVERSEER_INTERACTIONS_DIR
from utils.backend import OVERSEER_DUMP_PATH
from utils.backend import SWIFT_JUDGEMENT_DUMP_PATH
from utils.backend import PROMPTS
from utils.backend import DEPLOYMENTS
from utils.backend import CONFIG
from utils.backend import SETTINGS
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import grab_last_response
from utils.chat_utilities import generate_and_add_raw_bot_response
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
# These are names of the various prompts.
OVERSEER_SOURCE_FIDELITY = "overseer_source_fidelity"  # Checks factual content
OVERSEER_MISC = "overseer_misc"  # Checks non-factual content
SWIFT_JUDGE_SOURCE_FIDELITY = (
    "swift_judge_source_fidelity"  # Swift version of OVERSEER_SOURCE_FIDELITY
)
SWIFT_JUDGE_MISC = "swift_judge_misc"  # Swift version of OVERSEER_MISC
MESSAGE_LENGTH_CUTTER = (
    "message_length_cutter"  # Responsible for summarizing messages that are too long
)
MAX_TOKENS_PER_MESSAGE = SETTINGS["max_tokens_before_summarization"]


def evaluate_with_overseers(
    conversation, harvested_syntax, chatbot_id, model_id=CONFIG["model_id"]
):
    """Overseer agents checks rule-adherence of the response generated by the
    main chatbot. The overseer that checks the response is selected based on
    which citation the chatbot uses. For example, `¤:cite(["some_source"]):¤`
    will activate the source-fidelity overseer which compares the bots response
    to the cited source, and `¤:cite(["no_advice_or_claims"]):¤ will activate
    the miscellaneous overseer which checks "non-factual" responses.

    If the overseer evaluation is "ACCEPTED" then warning_message = [] is
    returned."""

    available_sources = get_sources_available_to_chatbot(chatbot_id)
    citations = harvested_syntax["citations"]

    if harvested_syntax["referral"]:
        overseer_evaluation = user_confirms_they_want_redirect(conversation)
        if overseer_evaluation == "ACCEPTED":
            silent_print("Overseer confirms that user wants to be referred.")
            warning_message = []
        else:
            warning_message = """Ask for confirmation before redirecting the
                              user."""

    elif list_intersection(available_sources, citations):
        overseer_evaluation, warning_message = overseer_evaluates_source_fidelity(
            conversation, citations, chatbot_id, model_id
        )

    else:
        overseer_evaluation, warning_message = overseer_evaluates_misc_messages(
            conversation, citations, model_id
        )

    return overseer_evaluation, warning_message


# -- SOURCE FIDELITY BOT --
def overseer_evaluates_source_fidelity(
    conversation, citations: list, chatbot_id: str, model_id: str
) -> list:
    """An overseer bot checks fidelity of bot response to the source it cites. Only
    considers citations that reference files containing information, as opposed to dummy
    citations that are used classify what type of response the bot is giving."""
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
            return "ACCEPTED", warning_message
        else:
            silent_print("Message flagged by gpt-3.5-turbo-instruct.")

        prompt_completed = fill_in_prompt_template_for_source_fidelity_overseer(
            chatbot_message, sources
        )
        evaluation_dict = generate_overseer_response(
            prompt=prompt_completed,
            model_id=model_id,
        )
        silent_print(f"{OVERSEER_SOURCE_FIDELITY} evaluation of {source_citations}:")
        overseer_evaluation, warning_message = extract_overseer_evaluation_and_feedback(
            evaluation_dict
        )
    else:
        overseer_evaluation = "ACCEPTED"
        warning_message = []

    return overseer_evaluation, warning_message


def preliminary_check_of_source_fidelity(
    sources: list[str],
    chatbot_message: str,
    prompt=PROMPTS[SWIFT_JUDGE_SOURCE_FIDELITY],
):
    """Uses GPT-3.5-turbo-instruct to generate a preliminary quality check on source
    adherence. This evaluation is decent at catching deviations from source materials, but
    sometimes flags messages that are perfectly fine. If flagged, a more computationally
    expensive model is called to double check the evaluation."""
    source = sources[0]
    prompt_completed = prompt.format(chatbot_message=chatbot_message, source=source)
    evaluation = generate_single_response_to_prompt(prompt_completed)
    dump_swift_judgement_to_markdown(prompt_completed, evaluation)
    silent_print(f"turbo-instruct says {evaluation}")
    if "ACCEPTED" in evaluation:
        return "ACCEPTED"
    else:
        return "WARNING"


def fill_in_prompt_template_for_source_fidelity_overseer(
    chatbot_message: str,
    sources: list[str],
    prompt_template=PROMPTS[OVERSEER_SOURCE_FIDELITY],
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
    deployment_name: str = CONFIG["deployment_name"],
) -> dict:
    """Generates the response of the overseer (uses GPT-4) and returns it as a
    dictionary."""
    response = generate_single_response_to_prompt(
        prompt, deployment_name=deployment_name
    )
    _, overseer_evaluation = extract_command_names_and_arguments(response)
    if overseer_evaluation:
        evaluation_dict = convert_json_string_to_dict(overseer_evaluation[0])
    else:
        evaluation_dict = None

    dump_file(f"{prompt}\n\n# Output\n\n{overseer_evaluation}.md", OVERSEER_DUMP_PATH)

    return evaluation_dict


def extract_overseer_evaluation_and_feedback(
    evaluation_dict: dict,
) -> Tuple[str, str]:
    """Appends warning message under system if the overseer evaluation is
    WARNING` or NOT ACCEPTED`."""
    overseer_evaluation = "ACCEPTED"
    warning_message = []
    if evaluation_dict and overseer_response_is_valid(evaluation_dict):
        silent_print(evaluation_dict)
        if evaluation_dict["evaluation"] != "ACCEPTED":
            warning_message = evaluation_dict["message_to_bot"]
            overseer_evaluation = evaluation_dict["evaluation"]
    return overseer_evaluation, warning_message


def overseer_response_is_valid(overseer_dict: dict) -> bool:
    """Checks the dictionary extracted from the overseer response follows the
    expected conventions."""
    if "evaluation" in overseer_dict.keys():
        if "message_to_bot" in overseer_dict.keys():
            return True
    return False


# -- OVERSEER OF MISCELLANEOUS/NON-FACTUAL MESSAGES --
def overseer_evaluates_misc_messages(conversation, citations: list, model_id: str):
    """This bot is responsible for monitoring and evaluating bot messages that
    do NOT cite sources. These are messages that cite the initial prompt, refers
    the user to emergency phone number, or explain basic things that are not
    coming directly from a scripted source."""
    # Remove citatons that do NOT reference a source (they label the response)
    misc_citations = [
        source for source in citations if source in MESSAGE_CLASSIFICATIONS
    ]
    misc_citations = list_intersection(MESSAGE_CLASSIFICATIONS, citations)

    overseer_evaluation = "ACCEPTED"
    warning_message = []

    if misc_citations:
        user_message = grab_last_user_message(conversation)
        chatbot_message = grab_last_assistant_response(conversation)
        swift_judgement = preliminary_check_of_misc_message(
            user_message, chatbot_message
        )
        if swift_judgement != "ACCEPTED":
            prompt = PROMPTS[OVERSEER_MISC].format(
                user_message=user_message, chatbot_message=chatbot_message
            )
            evaluation_dict = generate_overseer_response(prompt)
            silent_print(f"{OVERSEER_MISC} evaluation:")
            overseer_evaluation, warning_message = (
                extract_overseer_evaluation_and_feedback(evaluation_dict)
            )

    return overseer_evaluation, warning_message


def preliminary_check_of_misc_message(
    user_message: str,
    chatbot_message: str,
    prompt=PROMPTS[SWIFT_JUDGE_MISC],
):
    """Uses GPT-3.5-turbo-instruct to screen for behaviours that violates the
    chatbots role limitations."""
    prompt_completed = prompt.format(
        user_message=user_message, chatbot_message=chatbot_message
    )
    evaluation = generate_single_response_to_prompt(prompt_completed)
    dump_swift_judgement_to_markdown(prompt_completed, evaluation)
    silent_print(f"turbo-instruct (non-factual) says {evaluation}")
    if "ACCEPTED" in evaluation:
        return "ACCEPTED"
    else:
        return "WARNING"


def dump_swift_judgement_to_markdown(prompt_adjusted, evaluation):
    """Dumps the prompt and evaluation of the swift judgement overseer to a markdown
    file in chat-info/swift_judgement.md."""
    [{"input": prompt_adjusted, "content": evaluation}]
    dump_chat_to_markdown(
        [
            {"role": "input", "content": prompt_adjusted},
            {"role": "evaluation", "content": evaluation},
        ],
        SWIFT_JUDGEMENT_DUMP_PATH,
    )


def trim_message_length(
    conversation,
    prompt=PROMPTS[MESSAGE_LENGTH_CUTTER],
    deployment_name=DEPLOYMENTS[MESSAGE_LENGTH_CUTTER],
    max_tokens_per_message=SETTINGS["max_tokens_before_summarization"],
) -> list:
    """Chatbot responsible for summarizing messages that are too long. Returns
    the conversation with a trimmed version of the last assistant message."""
    chatbot_message = grab_last_assistant_response(conversation)
    commands = get_commands(chatbot_message)
    # Insert variables into prompt
    prompt = prompt.format(
        max_tokens=max_tokens_per_message, chatbot_message=chatbot_message
    )
    shortened_message = generate_single_response_to_prompt(
        prompt,
        deployment_name=deployment_name,
    )
    # Re-insert commands
    shortened_message = insert_commands(commands, shortened_message)
    # Replace with original message with shortened message
    conversation[-1]["content"] = shortened_message
    return conversation


def user_confirms_they_want_redirect(
    conversation,
    deployment_name=DEPLOYMENTS["referral_consent_checker"],
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
    response = generate_single_response_to_prompt(prompt_completed, deployment_name)
    dump_path = os.path.join(OVERSEER_INTERACTIONS_DIR, "referral_consent_checker.md")
    dump_overseer_interactions(prompt_completed, response, dump_path)
    if "True" in response:
        return "ACCEPTED"
    else:
        "NOT ACCEPTED"
