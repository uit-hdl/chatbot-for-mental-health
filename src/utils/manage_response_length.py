"""Functions responsible for keeping the response length below a desired length,
and generate feedback to incentivice the chatbot to keep its messages short. If
response exceeds maximum allowed length it gets summarized by AI-agent."""

from utils.general import silent_print
from utils.chat_utilities import generate_single_response_to_prompt
from utils.chat_utilities import grab_last_assistant_response
from utils.consumption_of_tokens import count_tokens_in_message
from utils.process_syntax import get_commands
from utils.process_syntax import insert_commands
from utils.backend import MODEL_ID
from utils.backend import SYSTEM_MESSAGES
from utils.backend import SETTINGS
from utils.backend import PROMPTS
from utils.backend import PRE_SUMMARY_DUMP_PATH
from utils.backend import dump_file


def manage_length_of_chatbot_response(conversation) -> list:
    """Appends system warning to chat if message is too long. Very long messages
    get summarized."""
    bot_response = grab_last_assistant_response(conversation)
    response_length = count_tokens_in_message(bot_response, MODEL_ID)
    warning = None

    if response_length >= SETTINGS["max_tokens_before_summarization"]:
        silent_print("Response exceeds max length, shortening message with GPT-3.5...")
        conversation = summarize_if_response_too_long(conversation)
        warning = SYSTEM_MESSAGES["max_tokens_before_summarization"]

    elif response_length > SETTINGS["limit_2_tokens_per_message"]:
        silent_print(f"Response has length {response_length} tokens...")
        warning = SYSTEM_MESSAGES["limit_2_tokens_per_message"]

    elif response_length > SETTINGS["limit_1_tokens_per_message"]:
        silent_print(f"Response has length {response_length} tokens...")
        warning = SYSTEM_MESSAGES["limit_1_tokens_per_message"]

    if warning:
        conversation.append({"role": "system", "content": warning})

    return conversation


def summarize_if_response_too_long(
    conversation,
    prompt=PROMPTS["message_summarizer"],
    model="gpt-35-turbo-16k",
    max_tokens_per_message=SETTINGS["max_tokens_chat_completion"],
) -> list:
    """Chatbot responsible for summarizing messages that are too long. Returns
    the conversation with a trimmed version of the last assistant message."""
    chatbot_message = grab_last_assistant_response(conversation)
    dump_file(chatbot_message, PRE_SUMMARY_DUMP_PATH)
    commands = get_commands(chatbot_message)
    # Insert variables into prompt
    prompt_completed = prompt.format(
        max_tokens=max_tokens_per_message, chatbot_message=chatbot_message
    )
    shortened_message = generate_single_response_to_prompt(
        prompt_completed,
        model,
    )
    # Re-insert commands
    shortened_message = insert_commands(commands, shortened_message)
    # Replace with original message with shortened message
    conversation[-1]["content"] = shortened_message
    return conversation
