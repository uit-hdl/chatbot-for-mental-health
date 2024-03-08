"""Functions (non-essential) used to calculate various metrics related to use of tokens. """

import tiktoken

from utils.backend import SETTINGS
from utils.backend import MODEL_ID
from utils.backend import TOKEN_USAGE_DUMP_PATH
from utils.backend import load_json_from_path
from utils.backend import dump_to_json


def reset_chat_consumption():
    """Resets chat_consumption.json which tracks the resource consumption (tokens and cost
    in kr) of a chat. This function is executed at the start of each new conversation.
    """
    dump_to_json(
        {"token_usage_total": 0, "chat_cost_kr_total": 0}, TOKEN_USAGE_DUMP_PATH
    )


def update_chats_total_consumption(conversation, model_id):
    """Loads and updates the json file that tracks the cumulative cost of the
    current chat in terms of tokens and cost in NOK."""
    chat_consumption = load_json_from_path(TOKEN_USAGE_DUMP_PATH)
    chat_consumption["token_usage_total"] += count_tokens_used_to_create_last_response(
        conversation
    )
    chat_consumption["chat_cost_kr_total"] += calculate_cost_of_response(
        conversation, model_id
    )
    dump_to_json(chat_consumption, TOKEN_USAGE_DUMP_PATH)


def count_tokens_used_to_create_last_response(conversation) -> int:
    """Counts the number of tokens used to generate the last message in the conversation."""
    tokens_in = count_tokens_in_chat(conversation[:-1])
    tokens_out = count_tokens_in_chat(conversation[-1:])
    return tokens_in + tokens_out


def count_tokens_in_chat(conversation: list) -> int:
    """Counts the number of tokens in a conversation using token encoder
    https://github.com/openai/tiktoken/blob/main/tiktoken/model.py.
    """
    num_tokens = 0
    for message in conversation:
        # "user: assistant:" corresponds to 4 tokens
        num_tokens += 4
        num_tokens += count_tokens_in_message(message["content"], MODEL_ID)
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def count_tokens_in_message(message: str, model_id):
    """Counts the number of tokens in a single message."""
    encoding = tiktoken.encoding_for_model(model_id)
    return len(encoding.encode(message))


def calculate_cost_of_response(conversation, model_id):
    """Calculates the cost of generating the last repsonse (which is assumed to be from
    assistant)."""
    tokens_in = count_tokens_in_chat(conversation[:-1])
    tokens_out = count_tokens_in_chat(conversation[-1:])
    cost_per_1k_input_tokens = SETTINGS["dollars_per_1k_token"][model_id]["input"]
    cost_per_1k_output_tokens = SETTINGS["dollars_per_1k_token"][model_id]["output"]
    # Calculate cost in Dollars
    dollars_tokens_in = tokens_in * cost_per_1k_input_tokens / 1000
    dollars_tokens_out = tokens_out * cost_per_1k_output_tokens / 1000
    dollars_total = dollars_tokens_in + dollars_tokens_out
    # Convert to NOK
    kroners_total = dollars_total * SETTINGS["nok_per_dollar"]
    return kroners_total
