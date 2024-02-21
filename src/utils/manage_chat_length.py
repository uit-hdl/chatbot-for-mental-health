from utils.consumption_of_tokens import count_tokens_in_chat
from utils.general import silent_print
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.backend import dump_to_json
from utils.backend import TRUNCATION_INFO_DUMP_PATH


def truncate_if_too_long(conversation):
    """Truncates the conversation if it exceeds the maximum allowed length. Deletes oldest messages
    first. In the future, we may want to replace this with a summary bot using GPT 3.5."""
    # Delete the first/oldest message in chat that is not the initial prompt
    removed_messages = []
    while exceeding_max_tokens(conversation) and len(conversation) > 1:
        removed_messages.append(conversation[1])
        del conversation[1]
        silent_print("Truncating conversation")
    if removed_messages:
        dump_to_json(removed_messages, TRUNCATION_INFO_DUMP_PATH)
    LOGGER.info(f"Tokens in chat: {count_tokens_in_chat(conversation)}")
    
    return conversation


def exceeding_max_tokens(conversation):
    """Checks if the number of tokens in chat exceeds the maximum allowed number."""
    return count_tokens_in_chat(conversation) > SETTINGS["max_tokens_before_truncation"]
