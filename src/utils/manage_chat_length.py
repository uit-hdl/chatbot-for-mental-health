from utils.consumption_of_tokens import count_tokens_in_chat
from utils.general import silent_print
from utils.backend import dump_to_json
from utils.backend import load_json_from_path
from utils.backend import update_field_value_in_json
from utils.backend import SETTINGS
from utils.backend import TRUNCATION_INFO_DUMP_PATH
from utils.backend import TOKEN_USAGE_DUMP_PATH
from utils.backend import TRANSCRIPT_DUMP_PATH


def truncate_if_too_long(conversation):
    """Truncates the conversation if it exceeds the maximum allowed length. Deletes
    oldest messages first. In the future, we may want to replace this with a summary bot
    using GPT 3.5."""
    # Delete the first/oldest message in chat that is not the initial prompt
    conversation_trimmed, removed_messages = trim_conversation(conversation)

    if removed_messages:
        dump_to_json(removed_messages, TRUNCATION_INFO_DUMP_PATH)

    update_chat_transcript(conversation_trimmed)
    update_field_value_in_json(
        file_path=TOKEN_USAGE_DUMP_PATH,
        field="current_chat_token_count",
        new_value=count_tokens_in_chat(conversation_trimmed),
    )

    return conversation_trimmed


def trim_conversation(conversation):
    """Removes messages if nessecary to prevent chat getting too long."""
    removed_messages = []
    counter = 0
    while exceeding_max_tokens(conversation) and len(conversation) > 1:
        removed_messages.append(conversation[1])
        del conversation[1]
        if counter == 0:
            silent_print("Truncating conversation")
        counter += 1
    return conversation, removed_messages


def exceeding_max_tokens(conversation):
    """Checks if the number of tokens in chat exceeds the maximum allowed number."""
    return count_tokens_in_chat(conversation) > SETTINGS["max_tokens_before_truncation"]


def update_chat_transcript(conversation_current):
    """Ensures that the complete chat history can be viewed in a file even after messages
    get deleted."""
    all_removed_messages = load_json_from_path(TRUNCATION_INFO_DUMP_PATH)
    full_conversation = all_removed_messages + conversation_current[1:]
    dump_to_json(full_conversation, TRANSCRIPT_DUMP_PATH)
