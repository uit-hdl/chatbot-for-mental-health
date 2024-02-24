"""Functions for creating external overseer bots which various parts of the conversation
and chatbot messages and provides feedback to prevent chatbot identity drift. Overseer
bots are assumed to generate a message on the form `¤:provide_feedback(<data on JSON
format>):¤`"""

from typing import Tuple

from utils.backend import get_source_content_and_path
from utils.backend import dump_to_json
from utils.backend import dump_current_conversation_to_json
from utils.backend import convert_json_string_to_dict
from utils.backend import OVERSEER_DUMP_PATH
from utils.backend import PROMPTS
from utils.backend import CONFIG
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import grab_last_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.process_syntax import extract_command_names_and_arguments
from utils.general import list_intersection
from utils.general import list_subtraction
from utils.general import silent_print

# Citations that do not reference a source but serves to classify the bots response
CLASSIFICATION_CITATIONS = [
    "initial_prompt",
    "sources_dont_contain_answer",
    "no_advice_or_claims",
    "support_phone_number",
    "the_architect",
    "sources_dont_contain_answer",
]
OVERSEER_SOURCE_FIDELITY = "overseer_source_fidelity"
OVERSEER_MISC = "overseer_misc"


# -- SOURCE FIDELITY BOT --
def overseer_evaluates_source_fidelity(
    conversation, harvested_syntax: dict, chatbot_id: str
) -> list:
    """An overseer bot checks fidelity of bot response to the source it cites. Only
    considers citations that reference files containing information, as opposed to dummy
    citations that are used classify what type of response the bot is giving."""
    chatbot_message = grab_last_assistant_response(conversation)
    # Remove citatons that do not reference a source (only label the response)
    source_citations = list_subtraction(
        harvested_syntax["citations"], CLASSIFICATION_CITATIONS
    )
    if source_citations:
        overseer_input = generate_source_fidelity_overseer_input(
            chatbot_message, source_citations, chatbot_id
        )
        evaluation_dict = generate_overseer_response(
            overseer_input, overseer_id=OVERSEER_SOURCE_FIDELITY
        )
        silent_print(f"{OVERSEER_SOURCE_FIDELITY} evaluation of {source_citations}:")
        conversation = update_conversation_based_on_overseer_evaluation(
            evaluation_dict, conversation
        )

    dump_current_conversation_to_json(conversation)

    return conversation


def generate_source_fidelity_overseer_input(
    bot_message: str, source_names: list[str], chatbot_id: str
) -> str:
    """Takes the response generated by the bot and a list of sources
    that the bot cites to support its message, and concatenates them in a string in the
    format that the overseer bot expects."""
    source_texts = ""
    for i, source_name in enumerate(source_names):
        source_texts += f"source {i}: '{get_source_content_and_path(chatbot_id, source_name)[0]}'\n\n"
    system_message = f"{source_texts}\nbot response: '{bot_message}'\n"
    return system_message


def generate_overseer_response(
    system_message_to_overseer: str, overseer_id: str
) -> Tuple[str, str]:
    """Generates the response of the overseer."""
    backend_conversation = initiate_conversation_with_prompt(
        PROMPTS[overseer_id], system_message_to_overseer
    )
    backend_conversation = generate_and_add_raw_bot_response(
        backend_conversation, CONFIG
    )
    overseer_response_raw = grab_last_response(backend_conversation)
    _, overseer_evaluation = extract_command_names_and_arguments(overseer_response_raw)

    if overseer_evaluation:
        evaluation_dict = convert_json_string_to_dict(overseer_evaluation[0])
    else:
        evaluation_dict = None

    dump_to_json(backend_conversation, OVERSEER_DUMP_PATH)

    return evaluation_dict


def update_conversation_based_on_overseer_evaluation(
    evaluation_dict: dict, conversation: list
) -> list:
    """Appends warning message under system if the overseer evaluation is `WARNING` or
    NOT ACCEPTED`."""
    if evaluation_dict and overseer_response_is_valid(evaluation_dict):
        silent_print(evaluation_dict)
        if evaluation_dict["evaluation"] != "ACCEPTED":
            warning = evaluation_dict["message_to_bot"]
            conversation.append({"role": "system", "content": warning})
    return conversation


def overseer_response_is_valid(overseer_dict: dict):
    """Basic check of the dictionary extracted from the overseer response."""
    if (
        "evaluation" in overseer_dict.keys()
        and "message_to_bot" in overseer_dict.keys()
    ):
        return True
    else:
        return False


# -- CONFIRMATION BOT --
def intent_classification_bot(user_message) -> str:
    """Checks if the user is answering yes or no."""
    confirmation_chat = initiate_conversation_with_prompt(
        PROMPTS["confirmation_bot"],
        system_message="{'user_message': '%s'}" % user_message,
    )
    confirmation_bot_response = grab_last_response(
        generate_and_add_raw_bot_response(confirmation_chat, CONFIG)
    )
    _, command_arguments = extract_command_names_and_arguments(
        confirmation_bot_response
    )
    intent_classification = interpret_bot_command_argument(command_arguments)
    return intent_classification


def interpret_bot_command_argument(command_arguments: list[str]):
    """Determines based on the command argument of the bot if it has
    concluded "YES" or "NO"."""
    if command_arguments:
        if command_arguments[0] == "YES":
            return "YES"
        else:
            return "NO"
    else:
        return "NO"


# -- OVERSEER OF NON-FACTUAL MESSAGES --
def overseer_evaluates_non_factual_messages(conversation, harvested_syntax: dict):
    """This bot is responsible for monitoring and evaluating bot messages that do not cite
    sources. These are messages cite the initial prompt, messages that referr the user to
    emergency phone number, and messages where the bot is explaining basic things that are
    not coming directly from a scripted source."""
    # Remove citatons that do not reference a source (only label the response)
    classification_citations = [
        source
        for source in harvested_syntax["citations"]
        if source in CLASSIFICATION_CITATIONS
    ]
    classification_citations = list_intersection(
        CLASSIFICATION_CITATIONS, harvested_syntax["citations"]
    )

    if classification_citations:
        user_message = grab_last_user_message(conversation)
        chatbot_response = grab_last_assistant_response(conversation)
        system_message_to_overseer = f"""
        user message: '{user_message}'
        bot response: '{chatbot_response}'\n
        """
        evaluation_dict = generate_overseer_response(
            system_message_to_overseer, overseer_id=OVERSEER_MISC
        )
        silent_print(f"{OVERSEER_MISC} evaluation:")
        conversation = update_conversation_based_on_overseer_evaluation(
            evaluation_dict, conversation
        )

    dump_current_conversation_to_json(conversation)

    return conversation
