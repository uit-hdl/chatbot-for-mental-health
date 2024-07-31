"""Functions responsible for keeping the length of the chat below a specified limit."""

import os
import numpy as np

from utils.consumption_of_tokens import count_tokens_in_chat
from utils.general import silent_print
from utils.general import list_subtraction
from utils.managing_sources import get_index_of_currently_inserted_sources
from utils.managing_sources import get_names_of_currently_inserted_sources
from utils.managing_sources import get_inactivity_times_for_sources
from utils.managing_sources import remove_inserted_sources_from_conversation
from utils.backend import dump_to_json
from utils.backend import add_element_to_existing_json_file
from utils.backend import load_json_from_path
from utils.backend import update_field_value_in_json
from utils.backend import CHATBOT_CONFIG
from utils.backend import DELETED_MESSAGES_DUMP_PATH
from utils.backend import TOKEN_USAGE_DUMP_PATH
from utils.backend import TRANSCRIPT_DUMP_PATH


def truncate_if_too_long(conversation):
    """Truncates the conversation if it exceeds the maximum allowed length. Deletes
    oldest messages first. In the future, we may want to replace this with a summary bot
    using GPT 3.5."""
    conversation_trimmed = trim_sources(conversation)
    # Delete the first/oldest message in chat that is not the initial prompt
    conversation_trimmed, removed_messages = trim_conversation(conversation_trimmed)

    if removed_messages:
        add_element_to_existing_json_file(removed_messages, DELETED_MESSAGES_DUMP_PATH)

    update_chat_transcript(conversation_trimmed)
    update_field_value_in_json(
        file_path=TOKEN_USAGE_DUMP_PATH,
        field="current_chat_token_count",
        new_value=count_tokens_in_chat(conversation_trimmed),
    )

    return conversation_trimmed


def trim_conversation(conversation):
    """Removes messages if nessecary to prevent chat getting too long. Ensures
    that there is a minimum of 2 user messages left in the conversation."""
    removed_messages = []
    counter = 0

    while exceeding_max_tokens(conversation) and count_user_messages(conversation) >= 2:
        index_first_removable_message = find_first_removable_message(conversation)
        removed_messages.append(conversation[index_first_removable_message])
        del conversation[index_first_removable_message]

        if counter == 0:
            silent_print("Truncating conversation")
        counter += 1

    return conversation, removed_messages


def trim_sources(conversation):
    """Ensures that the number of sources inserted in the conversation does not
    exceed a maximum number (specified in the settings). Preferentially keeps
    the most recently cited sources. In case of ties, keeps the most recently
    inserted sources."""
    n_inserted_sources_allowed = CHATBOT_CONFIG["max_inserted_sources"]
    replacement_message = f"Source removed to keep number of inserted sources below {n_inserted_sources_allowed}."

    names_inserted_sources = get_names_of_currently_inserted_sources(conversation)
    inactivity_times = get_inactivity_times_for_sources(
        conversation, names_inserted_sources
    )
    sources_to_remove = []
    while len(names_inserted_sources) > n_inserted_sources_allowed:
        idx_source_to_remove = np.argmax(inactivity_times)
        sources_to_remove.append(names_inserted_sources[idx_source_to_remove])
        del names_inserted_sources[idx_source_to_remove]
        del inactivity_times[idx_source_to_remove]
        silent_print(replacement_message)

    conversation_trimmed = remove_inserted_sources_from_conversation(
        conversation,
        sources_to_remove,
        replacement_message=replacement_message,
    )

    return conversation_trimmed


def find_first_removable_message(conversation):
    """Identifies the index of the first message that is neither system prompt
    nor a source, and is therefore 'removable'."""
    index_not_prompt = list(range(1, len(conversation)))
    index_inserted_sources = get_index_of_currently_inserted_sources(conversation)
    index_of_removable_messages = list_subtraction(
        index_not_prompt, index_inserted_sources
    )
    index_first_removable_message = index_of_removable_messages[0]

    return index_first_removable_message


def exceeding_max_tokens(conversation):
    """Checks if the number of tokens in chat exceeds the maximum allowed number."""
    return count_tokens_in_chat(conversation) > CHATBOT_CONFIG["max_tokens_before_truncation"]


def update_chat_transcript(conversation_current):
    """Ensures that the complete chat history (without truncation to stay within length
    limits) can be viewed in `chat-info/transcript.json`."""
    if os.path.exists(DELETED_MESSAGES_DUMP_PATH):
        all_removed_messages = load_json_from_path(DELETED_MESSAGES_DUMP_PATH)
        full_conversation = all_removed_messages + conversation_current[1:]
    else:
        full_conversation = []

    full_conversation += conversation_current[1:]
    dump_to_json(full_conversation, TRANSCRIPT_DUMP_PATH)


def count_user_messages(conversation):
    """Counts how many user messages are in the chat. Used to prevent deleting too many
    messages."""
    return len([msg for msg in conversation if msg["role"] == "user"])
