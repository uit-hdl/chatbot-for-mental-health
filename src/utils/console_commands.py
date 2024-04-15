from utils.backend import dump_conversation
from utils.backend import dump_copy_of_chat_info_to_results
from utils.backend import get_command_line_input
from utils.chat_utilities import index_of_assistant_responses_intended_for_user


def offer_to_store_conversation(conversation):
    """Asks the user in the console if he wants to store the conversation, and
    if so, how to name it."""
    store_conversation_response = input("Store conversation? (Y/N): ").strip().lower()
    if store_conversation_response == "y":
        label = input("File name (hit enter for default): ").strip().lower()
        if label == "":
            label = "conversation"
        dump_conversation(conversation, label)
    else:
        print("Conversation not stored")


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response number = n_current - n_rewind. If
    n_rewind == 1 then conversation resets to the second to last bot-response, allowing
    you to investigate the bots behaviour given the chat up to that point. Useful for
    testing how likely the bot is to reproduce an error (such as forgetting an
    instruction) or a desired response, since you don't have to restart the conversation
    from scratch. Works by Identifing and deleting messages between the current message
    and the bot message you are resetting to, but does not nessecarily reset the overall
    conversation to the state it was in at the time that message was produced (for
    instance, the prompt might have been altered)."""
    assistant_indices = index_of_assistant_responses_intended_for_user(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def take_snapshot_of_conversation_status():
    """Dumps all information about the status of the current chat to a
    directory."""
    dump_info_response = get_command_line_input("Dump chat information (y/n)?")
    if dump_info_response == "y":
        dump_name = get_command_line_input("Name the dump-directory:")
        if dump_name == "":
            dump_name = "unnamed-dump"
        dump_copy_of_chat_info_to_results(dump_name)
    else:
        print("Conversation not stored")
