import sys
import re

from utils.general import silent_print
from utils.general import offer_to_store_conversation
from utils.backend import PROMPTS

from utils.backend import LOGGER
from utils.backend import CONFIG
from utils.backend import dump_current_conversation_to_json
from utils.backend import load_yaml_file
from utils.managing_sources import remove_inactive_sources
from utils.chat_utilities import rewind_chat_by_n_assistant_responses
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.overseers import overseer_evaluates_source_fidelity
from utils.overseers import overseer_evaluates_non_factual_messages
from utils.create_chatbot_response import respond_to_user
from utils.console_chat_display import display_last_response
from utils.console_chat_display import display_last_assistant_response
from utils.console_chat_display import reprint_whole_conversation_without_syntax
from utils.console_chat_display import play_videos
from utils.console_chat_display import print_whole_conversation_with_backend_info
from utils.console_chat_display import display_images
from utils.console_chat_display import ROLE_TO_ANSI_COLOR_MAP
from utils.console_chat_display import RESET_COLOR
from utils.manage_chat_length import truncate_if_too_long
from utils.consumption_of_tokens import reset_chat_consumption

# Initiate global variables
BREAK_CONVERSATION = False
reset_chat_consumption()


def sleep_diary_assistant_bot(chatbot_id, chat_filepath=None):
    """Running this function starts a conversation with a tutorial bot that
    helps explain how a web-app (https://app.consensussleepdiary.com) functions. The web
    app is a free online app for collecting sleep data."""

    if chat_filepath:
        conversation = continue_previous_conversation(chat_filepath, chatbot_id)
    else:
        conversation = initiate_new_conversation(chatbot_id)
        display_last_response(conversation)

    while True:
        conversation = get_user_input(conversation)

        if BREAK_CONVERSATION:
            offer_to_store_conversation(conversation)
            break

        conversation, harvested_syntax = respond_to_user(
            conversation, chatbot_id
        )

        display_last_assistant_response(conversation)
        display_images(harvested_syntax["images"])
        play_videos(harvested_syntax["videos"])

        conversation = overseer_evaluates_source_fidelity(
            conversation, harvested_syntax, chatbot_id
        )
        conversation = overseer_evaluates_non_factual_messages(
            conversation, harvested_syntax
        )
        dump_current_conversation_to_json(conversation)

        if harvested_syntax["referral"]:
            if harvested_syntax["referral"]["file_exists"]:
                assistant_name = harvested_syntax["referral"]["name"]
                conversation = direct_to_new_assistant(assistant_name)
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


def initiate_new_conversation(chatbot_id: str, system_message=None):
    """Initiates a conversation with the chat bot."""
    conversation = initiate_conversation_with_prompt(
        PROMPTS[chatbot_id], system_message
    )
    LOGGER.info("Starting new conversation with %s.", chatbot_id)
    conversation = generate_and_add_raw_bot_response(conversation, CONFIG)
    dump_current_conversation_to_json(conversation)
    return conversation


def get_user_input(conversation) -> list:
    """Prompts user to input a prompt (the "question") in the command line."""
    global BREAK_CONVERSATION

    while True:
        user_message = input(
            ROLE_TO_ANSI_COLOR_MAP["user"] + "user" + RESET_COLOR + ": "
        )
        if "rewind_by" in user_message:
            n_rewind = int(user_message[-1])
            conversation = rewind_chat_by_n_assistant_responses(n_rewind, conversation)
            reprint_whole_conversation_without_syntax(conversation)
            dump_current_conversation_to_json(conversation)
        else:
            if user_message == "break":
                BREAK_CONVERSATION = True
            break
    conversation.append({"role": "user", "content": user_message})
    dump_current_conversation_to_json(conversation)
    return conversation


def direct_to_new_assistant(assistant_name: str) -> list:
    """Receives information about the users issue collected in json format, and
    redirects to the requested chatbot assistant."""
    LOGGER.info("Transferring to assistant %s", assistant_name)
    silent_print(f"Transferring user to {assistant_name}")
    new_conversation = initiate_new_conversation(assistant_name)
    return new_conversation


if __name__ == "__main__":
    chatbot_id = "referral"
    chat_filepath = None

    if len(sys.argv) > 1:
        chatbot_id = sys.argv[1]
        if chatbot_id == "":
            chatbot_id = "referral"
    if len(sys.argv) > 2:
        chat_filepath = sys.argv[2]

    sleep_diary_assistant_bot(chatbot_id, chat_filepath)
