"""Functions for making it convenient to manipulating the conversation list object and
chatbot. conversation is a list of dictionaries, each of which have keys 'role' and
'content' (the message) such as identifying responses of a specified role."""

import openai
from openai.error import RateLimitError
import re
import time

import copy
from utils.general import message_is_readable
from utils.general import list_intersection
from utils.backend import CHATBOT_CONFIG
from utils.backend import API_KEY
from utils.backend import AZURE_CONFIG
from utils.consumption_of_tokens import update_chats_total_consumption

openai.api_key = API_KEY
openai.api_type = AZURE_CONFIG["api_type"]
openai.api_base = AZURE_CONFIG["api_base"]
openai.api_version = AZURE_CONFIG["api_version"]


def generate_and_add_raw_bot_response(
    conversation,
    model="gpt-4",
    calc_tokens=True,
    max_tokens=CHATBOT_CONFIG["max_tokens_chat_completion"],
    temperature=None,
):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history. Does not interpret bot response.
    Model can be gpt-4 or gpt-35-turbo-16k."""
    conversation = copy.deepcopy(conversation)
    while True:
        try:
            response = get_chat_completion(conversation, model, max_tokens, temperature)
            break
        except RateLimitError as e:
            wait_time = extract_wait_time(e)
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    conversation.append(
        {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content.strip(),
        }
    )
    if calc_tokens:
        update_chats_total_consumption(conversation, model)
    return conversation


def get_chat_completion(conversation, model, max_tokens=None, temperature=None):
    """Get chat-completion using openai API."""
    deployment = AZURE_CONFIG["model_to_deployment_map"][model]
    return openai.ChatCompletion.create(
        messages=conversation,
        engine=deployment,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def extract_wait_time(error):
    """Extracts the wait time from RateLimitError message."""
    error_message = str(error)
    match = re.search(r"Retry after (\d+) seconds", error_message)
    if match:
        wait_time = int(match.group(1))
        return wait_time
    else:
        # Default wait time if unable to extract from error message
        return 20


def generate_single_response_to_prompt(prompt, model):
    """Used when a single response to a single prompt is all that is wanted, not
    a conversation. model is either gpt-4 or gpt-35-turbo-16k."""
    # Create conversation object with just one message (the prompt)
    conversation = initiate_conversation_with_prompt(prompt)
    # Get response
    conversation = generate_and_add_raw_bot_response(conversation, model)
    return conversation[-1]["content"]


def initiate_conversation_with_prompt(
    prompt: str, system_message: str = None
) -> list[str]:
    """Initiates a conversation in the openAI list format with the the initial
    prompt as the first message."""
    conversation = [{"role": "system", "content": prompt}]
    if system_message:
        conversation.append({"role": "system", "content": system_message})
    return conversation


def grab_last_response(conversation: list) -> str:
    """Grab content of the last chat message. Convenience function."""
    return conversation[-1]["content"]


def grab_last_assistant_response(conversation: list) -> str:
    """Grab the latest assistant response string."""
    index_assistant_messages = index_of_assistant_responses(conversation)
    if index_assistant_messages:
        return conversation[index_assistant_messages[-1]]["content"]
    else:
        print("WARNING: no assistant messages to grab.")


def identify_system_responses(conversation) -> list[int]:
    """Gets the index/indices for system responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "system"]


def index_of_assistant_responses(conversation) -> list[int]:
    """Gets the index/indices for assistant responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "assistant"]


def identify_user_messages(conversation) -> list[int]:
    """Gets the index/indices for `assistant` responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "user"]


def grab_last_user_message(conversation: list) -> str:
    """Grab the latest message string from user."""
    index_user_messages = identify_user_messages(conversation)
    if index_user_messages:
        return conversation[index_user_messages[-1]]["content"]


def replace_last_assistant_response(conversation, subsitute_message: str) -> list:
    """Substitutes the last assistant response with a new message."""
    index_assistant_messages = index_of_assistant_responses(conversation)
    conversation[index_assistant_messages[-1]]["content"] = subsitute_message
    return conversation


def remove_system_messages_following_last_assistant_response(conversation) -> list:
    """Removes all system messages following the last assistant response."""
    index_last_assistant_message = index_of_assistant_responses(conversation)[-1]
    index_system_messages = identify_system_responses(conversation)
    subsequent_system_messages = [
        i for i in index_system_messages if i > index_last_assistant_message
    ]
    if subsequent_system_messages:
        del conversation[subsequent_system_messages[0] :]
    return conversation


def index_of_assistant_responses_visible_to_user(conversation) -> list[int]:
    """Finds indices of assistant messages that are intended to be seen
    by the user (ignores messages for backend)."""
    idx_visible_messages = get_index_of_visible_messages(conversation)
    idx_assistant_messages = index_of_assistant_responses(conversation)
    # Grab assistent messages that are visible to user
    idx_visible_assistant_responses = list_intersection(
        idx_assistant_messages, idx_visible_messages
    )
    idx_visible_assistant_responses = sorted(idx_visible_assistant_responses)
    return idx_visible_assistant_responses


def get_index_of_visible_messages(conversation) -> list[int]:
    """Gets the index of messages that are visible in the chat to the user,
    i.e., not backend messages."""
    index_visible_messages = []
    for i, message in enumerate(conversation):
        if message_is_readable(message["content"]) and message["role"] != "system":
            index_visible_messages.append(i)
    return index_visible_messages


def append_system_messages(conversation, system_messages: list[str]) -> list:
    """Appends each message in a list of system messages to the conversation
    under the role of system."""
    if isinstance(system_messages, str):
        system_messages = [system_messages]
    for message in system_messages:
        conversation.append({"role": "system", "content": message})
    return conversation


def delete_last_bot_response(conversation) -> list:
    """Identifies which responses are from the assistant, and deletes the last
    response from the conversation. Used when the bot response has broken some
    rule, and we want it to create a new response."""
    assistant_indices = index_of_assistant_responses(conversation)
    del conversation[assistant_indices[-1]]
    return conversation
