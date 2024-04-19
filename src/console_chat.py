import sys

from utils.general import silent_print
from utils.overseers import redirect_confirmation_status
from utils.backend import PROMPTS
from utils.backend import LOGGER
from utils.backend import CONFIG
from utils.backend import TRANSCRIPT_DUMP_PATH
from utils.backend import SETTINGS
from utils.backend import dump_to_json
from utils.backend import dump_current_conversation_to_json
from utils.backend import load_yaml_file
from utils.backend import reset_files_that_track_cumulative_variables
from utils.console_interactions import offer_to_store_conversation
from utils.console_interactions import get_user_message_from_console
from utils.console_interactions import search_for_console_command
from utils.managing_sources import remove_inactive_sources
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.create_chatbot_response import respond_to_user
from utils.console_chat_display import display_last_response
from utils.console_chat_display import display_last_assistant_response
from utils.console_chat_display import play_videos
from utils.console_chat_display import print_whole_conversation_with_backend_info
from utils.console_chat_display import display_images
from utils.manage_chat_length import truncate_if_too_long


# Initiate global variables
BREAK_CONVERSATION = False
ASSISTANT_SPEAKS_FIRST = SETTINGS["role_that_speaks_first"] == "assistant"
reset_files_that_track_cumulative_variables()
silent_print(f"Overseer filters enabled: {SETTINGS['enable_overseer_filter']}")


def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Have a chat with a chatbot assistant in the console. The chatbot id is the name of
    the file (no extension) that contains the prompt of the chatbot."""

    if chat_filepath:
        conversation = continue_previous_conversation(chat_filepath, chatbot_id)
    else:
        conversation = initiate_conversation_object(chatbot_id)
        if ASSISTANT_SPEAKS_FIRST:
            conversation = generate_and_add_raw_bot_response(conversation)
            display_last_response(conversation)

    while True:
        conversation = get_user_input(conversation)

        if BREAK_CONVERSATION:
            offer_to_store_conversation(conversation)
            break

        conversation, harvested_syntax = respond_to_user(conversation, chatbot_id)

        display_last_assistant_response(conversation)
        display_images(harvested_syntax["images"])
        play_videos(harvested_syntax["videos"])
        dump_current_conversation_to_json(conversation)

        if harvested_syntax["referral"]:
            assistant_name = harvested_syntax["referral"]["name"]
            conversation = direct_to_new_assistant(assistant_name)
            conversation = generate_and_add_raw_bot_response(conversation)
            display_last_response(conversation)

        conversation = remove_inactive_sources(conversation)
        conversation = truncate_if_too_long(conversation)


def continue_previous_conversation(chat_filepath: str, chatbot_id: str) -> list:
    """Inserts the current prompt into a previous stored conversation that was
    discontinued, so that you can pick up where you left of."""
    conversation = load_yaml_file(chat_filepath)
    prompt = PROMPTS[chatbot_id]
    # Replace original prompt with requested prompt
    conversation[0] = {"role": "system", "content": prompt}
    print_whole_conversation_with_backend_info(conversation)
    dump_current_conversation_to_json(conversation)
    return conversation


def initiate_conversation_object(
    chatbot_id: str,
    system_message=None,
):
    """Initiates a conversation list by identifying the relevant prompt."""
    conversation = initiate_conversation_with_prompt(
        PROMPTS[chatbot_id], system_message
    )
    LOGGER.info("Starting new conversation with %s.", chatbot_id)
    dump_current_conversation_to_json(conversation)
    dump_to_json(conversation, TRANSCRIPT_DUMP_PATH)
    return conversation


def get_user_input(conversation) -> list:
    """Prompts user to input a prompt (the "question") in the command line."""
    global BREAK_CONVERSATION

    role_that_gets_to_speak_next = "user"
    while role_that_gets_to_speak_next == "user" and BREAK_CONVERSATION == False:
        user_message = get_user_message_from_console()
        conversation, role_that_gets_to_speak_next, BREAK_CONVERSATION = (
            search_for_console_command(user_message, conversation)
        )

    dump_current_conversation_to_json(conversation)

    return conversation


def direct_to_new_assistant(assistant_name: str) -> list:
    """Receives information about the users issue collected in json format, and
    redirects to the requested chatbot assistant."""
    LOGGER.info("Transferring to assistant %s", assistant_name)
    silent_print(f"Transferring user to {assistant_name}")
    new_conversation = initiate_conversation_object(assistant_name)
    return new_conversation


if __name__ == "__main__":
    chatbot_id = "mental_health"
    chat_filepath = None

    if len(sys.argv) > 1:
        chatbot_id = sys.argv[1]
        if chatbot_id == "":
            chatbot_id = "referral"
    if len(sys.argv) > 2:
        chat_filepath = sys.argv[2]

    sleep_diary_assistant_bot(chatbot_id, chat_filepath)
