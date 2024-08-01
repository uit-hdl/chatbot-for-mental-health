"""Functions concerned with interactivity in the console window during a
chat. These functions are primarily used in `console_chat.py`."""

import re

from utils.backend import dump_chat_to_results
from utils.backend import dump_copy_of_chat_info_to_results
from utils.backend import get_input_from_command_line
from utils.backend import collect_prompts_in_dictionary
from utils.chat_utilities import index_of_assistant_responses_visible_to_user
from utils.general import ROLE_TO_ANSI_COLOR_MAP
from utils.general import RESET_COLOR
from utils.general import silent_print
from utils.console_chat_display import reprint_whole_conversation_without_syntax
from utils.backend import dump_chat_to_dashboard


def offer_to_store_conversation(conversation):
    """Asks the user in the console if he wants to store the conversation, and
    if so, how to name it."""
    store_conversation_response = input("Store conversation? (Y/N): ").strip().lower()
    if store_conversation_response == "y":
        label = input("File name (hit enter for default): ").strip().lower()
        if label == "":
            label = "conversation"
        dump_chat_to_results(conversation, label)
    else:
        print("Conversation not stored")


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response number = n_current -
    n_rewind.

    E.g. if n_rewind == 1 then conversation resets to the second to last
    bot-response, allowing you to investigate the bots behaviour given the chat
    up to that point.

    Works by identifing and deleting messages between the current message and
    the bot message you are resetting to, but does not nessecarily reset the
    overall conversation to the state it was in at the time that message was
    produced (for instance, the prompt might have been altered)."""
    # Get index of assistant responses that are part of the non-backend chat
    assistant_indices = index_of_assistant_responses_visible_to_user(conversation)
    # Ensure that chat always has at least initial prompt + one response
    n_rewind_capped = min([n_rewind, len(assistant_indices) - 1])
    highest_index_to_keep = assistant_indices[-(n_rewind_capped + 1)]
    # Ensure we dont remove any system warnings linked to the AI message
    counter = 0
    while conversation[highest_index_to_keep + 1 + counter]["role"] == "system":
        counter += 1
    highest_index_to_keep += counter

    conversation_reset = conversation[: highest_index_to_keep + 1]

    return conversation_reset


def rewind_chat_by_n_user_messages(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to user-message number = n_current -
    n_rewind. Set n_rewind == 1 to regenerate bot message.

    E.g. if n_rewind == 1 then conversation resets to the most recent user
    message that was entered, and so it effectively just regenerates its last
    response. This can be useful for testing the variability in the bots
    responses."""
    # Get index of user messages
    user_indices = [
        i for i, message in enumerate(conversation) if message["role"] == "user"
    ]
    print(user_indices)

    # Ensure that you dont go further back then there are user messages
    n_rewind_capped = min([n_rewind, len(user_indices) - 1])
    highest_index_to_keep = user_indices[-n_rewind_capped]
    conversation_reset = conversation[: highest_index_to_keep + 1]
    return conversation_reset


def take_snapshot_of_conversation_status():
    """Dumps all information about the status of the current chat to a
    directory."""
    dump_info_response = get_input_from_command_line("Dump chat information (y/n)?")
    if dump_info_response == "y":
        dump_name = get_input_from_command_line("Name the dump-directory:")
        if dump_name == "":
            dump_name = "unnamed-dump"
        dump_copy_of_chat_info_to_results(dump_name)
    else:
        print("Conversation not stored")


def reload_and_refresh_initial_prompt(conversation, chatbot_id):
    """Reloads prompts and updates the initial prompt."""
    global PROMPTS
    PROMPTS = collect_prompts_in_dictionary()
    conversation[0]["content"] = PROMPTS[chatbot_id]
    return conversation


def search_for_console_command(user_message, conversation, chatbot_id):
    """Scans for commands in the message that is entered in the console window
    by the user, and updates conversation according to whether the message is or
    is not a command.

    Outputs: conversation, role_that_gets_to_speak_next, break_conversation."""
    # Variable that tracks whose turn it is to speak
    role_that_gets_to_speak_next = "assistant"
    break_conversation = False

    if "rewindaiby" in user_message:
        n_rewind = extract_number_as_int(user_message)
        conversation = rewind_chat_by_n_assistant_responses(n_rewind, conversation)
        reprint_whole_conversation_without_syntax(conversation)
        dump_chat_to_dashboard(conversation)
        role_that_gets_to_speak_next = "user"

    elif "rewinduserby" in user_message:
        n_rewind = extract_number_as_int(user_message)
        conversation = rewind_chat_by_n_user_messages(n_rewind, conversation)
        reprint_whole_conversation_without_syntax(conversation)
        dump_chat_to_dashboard(conversation)

    elif "dumpinfo" in user_message:
        take_snapshot_of_conversation_status()
        role_that_gets_to_speak_next = "user"

    elif "refreshprompts" in user_message:
        conversation = reload_and_refresh_initial_prompt(
            conversation, chatbot_id=chatbot_id
        )
        role_that_gets_to_speak_next = "user"
        silent_print("Prompts refreshed.")

    elif user_message == "break":
        break_conversation = True

    else:
        # Message is not a command
        conversation.append({"role": "user", "content": user_message})
        role_that_gets_to_speak_next = "assistant"

    return conversation, role_that_gets_to_speak_next, break_conversation


def extract_number_as_int(user_message):
    """Takes a string like 'hello1234' and returns 1234 as integer."""
    return int("".join(re.findall(r"\d", user_message)))


def get_user_message_from_console():
    """Prompts user to enter input into console window. Uses color coding to
    make it look nicer."""
    return input(ROLE_TO_ANSI_COLOR_MAP["user"] + "user" + RESET_COLOR + ": ")
