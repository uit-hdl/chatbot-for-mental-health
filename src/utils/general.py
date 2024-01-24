"""General utilities."""

import tiktoken
import re
import logging

from utils.backend import MODEL_ID
from utils.backend import dump_conversation
from utils.backend import SETTINGS
from utils.backend import LOGGER
from utils.chat_utilities import identify_assistant_responses


def remove_quotes_from_string(input_str):
    """Removes quotation marks, `"` or `'`, from a string. Used for standardization
    in cases where bot is not always consistent, such as play_video("video_name") instead of
    play_video(video_name)."""
    pattern = r"[\'\"]"  # Matches either single or double quotes
    result_str = re.sub(pattern, "", input_str)
    return result_str


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
    """Resets the conversation back to bot-response number = n_current - n_rewind. If n_rewind == 1
    then conversation resets to the second to last bot-response, allowing you to investigate the
    bots behaviour given the chat up to that point. Useful for testing how likely the bot is to
    reproduce an error (such as forgetting an instruction) or a desired response, since you don't
    have to restart the conversation from scratch. Works by Identifing and deleting messages between
    the current message and the bot message you are resetting to, but does not nessecarily reset the
    overall conversation to the state it was in at the time that message was produced (for instance,
    the prompt might have been altered)."""
    assistant_indices = identify_assistant_responses(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def count_tokens_used_to_create_last_response(conversation) -> int:
    """Counts the number of tokens used to generate the last message in the conversation."""
    tokens_in = count_tokens(conversation[:-1])
    tokens_out = count_tokens(conversation[-1])
    return tokens_in + tokens_out


def calculate_cost_of_response(conversation):
    """Calculates the cost of generating the last repsonse (which is assumed to be from
    assistant)."""
    tokens_in = count_tokens(conversation[:-1])
    tokens_out = count_tokens(conversation[-1])
    dollars_tokens_in = tokens_in * SETTINGS["dollars_per_1k_input_token"] / 1000
    dollars_tokens_out = tokens_out * SETTINGS["dollars_per_1k_output_token"] / 1000
    kroners_total = (dollars_tokens_in + dollars_tokens_out) * SETTINGS[
        "kr_to_dollar_ratio"
    ]
    return kroners_total


def count_tokens(conversation) -> int:
    """Counts the number of tokens in a conversation. Uses token encoder
    https://github.com/openai/tiktoken/blob/main/tiktoken/model.py. Input argument can be either a
    list or a dictionary (for instance the last response in the conversation).
    """
    if isinstance(conversation, dict):
        # Ensure list format
        conversation = [conversation]
    encoding = tiktoken.encoding_for_model(MODEL_ID)
    num_tokens = 0
    for message in conversation:
        # "user: assistant:" corresponds to 4 tokens
        num_tokens += 4
        num_tokens += len(encoding.encode(message["content"]))
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


# ## Dealing with linebreak characters ##


def remove_superflous_linebreaks(message):
    """Removes all superflous linebreak characters that may arise after removing commands."""
    message_cleaned = remove_trailing_newlines(message)
    message_cleaned = remove_superflous_linebreaks_between_paragraphs(message_cleaned)
    return message_cleaned


def remove_trailing_newlines(text):
    """Removes trailing newline characters (may emerge after stripping away commands from bot
    messages)."""
    while text[-1] == " " or text[-1] == "\n":
        if text[-1] == " ":
            text = text.rstrip(" ")
        elif text[-1] == "\n":
            text = text.rstrip("\n")
    return text


def remove_superflous_linebreaks_between_paragraphs(text: str):
    """Replaces consecutive line breaks with just two line breaks (may emerge after stripping away
    commands from bot messages)."""
    cleaned_text = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned_text
