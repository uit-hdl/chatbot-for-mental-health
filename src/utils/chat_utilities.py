"""Simple utilities for working with the conversation, which are lists of dictionaries, each of
which have keys 'role' and 'content' (the message) such as identifying responses of a specified
role."""
import openai
from utils.general import message_is_intended_for_user
from utils.general import list_intersection
from utils.consumption_of_tokens import count_tokens_in_message
from utils.backend import MODEL_ID
from utils.backend import SETTINGS
from utils.console_chat_display import silent_print


def check_length_of_chatbot_response(conversation):
    """Appends system warning to chat if message is long."""
    bot_response = grab_last_assistant_response(conversation)
    response_length = count_tokens_in_message(bot_response, MODEL_ID)
    warning_message = []
    status = "OK"
    if response_length > SETTINGS["max_tokens_per_message"]:
        silent_print("Response exceeds lenght...")
        warning_message = {
            "role": "system",
            "content": f"Your response was {response_length} tokens, which is too long!",
        }
        status = "REDO"
    if response_length > SETTINGS["warning_limit_tokens_per_message"]:
        silent_print("Response exceeds lenght...")
        warning_message = {
            "role": "system",
            "content": f"Your response was {response_length} tokens, careful!",
        }
        status = "WARNING"
    return warning_message, status


def generate_raw_bot_response(conversation, config: dict):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history. Does not interpret bot response."""
    response = openai.ChatCompletion.create(
        model=config["model_id"],
        messages=conversation,
        engine=config["deployment_name"],
    )
    conversation.append(
        {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content.strip(),
        }
    )
    return conversation


def initiate_prompt_engineered_ai_agent(
    prompt: str, system_message: str = None
) -> list[str]:
    """Creates an chatbot assistent by starting a conversation in the openAI list format with the
    the initial prompt as the first message."""
    conversation = [{"role": "system", "content": prompt}]
    if system_message:
        conversation.append({"role": "system", "content": system_message})
    return conversation


def grab_last_response(conversation: list) -> str:
    """Grab the last response. Convenience function for better code-readability."""
    return conversation[-1]["content"]


def grab_last_assistant_response(conversation: list) -> str:
    """Grab the latest assistant response."""
    index_assistant_messages = identify_assistant_responses(conversation)
    return conversation[index_assistant_messages[-1]]["content"]


def identify_assistant_responses(conversation) -> list[int]:
    """Gets the index/indices for `assistant` responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "assistant"]


def rewind_chat_by_n_assistant_responses(n_rewind: int, conversation: list) -> list:
    """Resets the conversation back to bot-response number = n_current - n_rewind. If n_rewind == 1
    then conversation resets to the second to last bot-response, allowing you to investigate the
    bots behaviour given the chat up to that point. Useful for testing how likely the bot is to
    reproduce an error (such as forgetting an instruction) or a desired response, since you don't
    have to restart the conversation from scratch. Works by Identifing and deleting messages between
    the current message and the bot message you are resetting to, but does not nessecarily reset the
    overall conversation to the state it was in at the time that message was produced (for instance,
    the prompt might have been altered)."""
    assistant_indices = identify_responses_intended_for_user(conversation)
    n_rewind = min([n_rewind, len(assistant_indices) - 1])
    index_reset = assistant_indices[-(n_rewind + 1)]
    return conversation[: index_reset + 1]


def identify_responses_intended_for_user(conversation) -> list[int]:
    """Finds assistant responses (list of indeces) that are contain human readable text, and not
    just commands for the backend."""
    responses_with_text = [
        i
        for (i, message) in enumerate(conversation)
        if message_is_intended_for_user(message["content"])
    ]
    assistant_messages = identify_assistant_responses(conversation)
    responses_intended_for_user = sorted(
        list_intersection(assistant_messages, responses_with_text)
    )
    return responses_intended_for_user


def append_system_messages(conversation, system_messages: list[str]) -> list:
    """Appends each message in a list of system messages to the conversation under the role of
    system."""
    for message in system_messages:
        conversation.append({"role": "system", "content": message})
    return conversation


def delete_last_bot_response(conversation) -> list:
    """Identifies which responses are from the assistant, and deletes the last
    response from the conversation. Used when the bot response has broken some
    rule, and we want it to create a new response."""
    assistant_indices = identify_assistant_responses(conversation)
    del conversation[assistant_indices[-1]]
    return conversation
