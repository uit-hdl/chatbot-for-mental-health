"""Functions for making it convenient to manipulating the conversation list object and
chatbot. conversation is a list of dictionaries, each of which have keys 'role' and
'content' (the message) such as identifying responses of a specified role."""

import openai
from openai.error import RateLimitError
import re
import time

import copy
from utils.general import message_is_intended_for_user
from utils.general import list_intersection
from utils.backend import SETTINGS
from utils.backend import API_KEY
from utils.backend import SETTINGS
from utils.backend import CONFIG
from utils.consumption_of_tokens import update_chats_total_consumption

openai.api_key = API_KEY
openai.api_type = CONFIG["api_type"]
openai.api_base = CONFIG["api_base"]
openai.api_version = CONFIG["api_version"]


def generate_and_add_raw_bot_response(
    conversation,
    model_id=CONFIG["model_id"],
    deployment_name=CONFIG["deployment_name"],
    calc_tokens=True,
    max_tokens=SETTINGS["max_tokens_chat_completion"],
    temperature=None,
):
    """Takes the conversation log, and updates it with the response of the
    chatbot as a function of the chat history. Does not interpret bot
    response."""
    conversation = copy.deepcopy(conversation)

    while True:
        try:
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=conversation,
                engine=deployment_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )
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
        update_chats_total_consumption(conversation, model_id)
    return conversation


def generate_single_response_using_gpt35_turbo_instruct(
    prompt: str,
    model_id="gpt-3.5-turbo-instruct",
    deployment_name=CONFIG["deployment_name_single_response"],
    max_tokens=SETTINGS["max_tokens_turbo_instruct"],
    temperature=None,
    return_everything=False,
):
    """Provides a chat completion to a single message input. `Completion` is
    optimized for cases where only a single response is desired, rather than a
    conversation. Note: GPT-3.5-turbot-instruct is fine tuned for this task."""
    response = openai.Completion.create(
        model=model_id,
        prompt=prompt,
        engine=deployment_name,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if return_everything:
        return response
    else:
        return_string = response.choices[0]["text"]
        return return_string.replace("\n", "").replace(" .", ".").strip()


def generate_single_response_to_prompt(
    prompt, deployment_name=CONFIG["deployment_name"]
):
    """Used when a single response to a single prompt is all that is wanted, not
    a conversation. Uses GPT-3.5 or 4. GPT-3.5-turbo instruct uses a different
    setup, and has its own function."""
    # Create conversation object with just one message (the prompt)
    conversation = initiate_conversation_with_prompt(prompt)
    # Get response
    conversation = generate_and_add_raw_bot_response(
        conversation, deployment_name=deployment_name
    )
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
    index_assistant_messages = identify_assistant_responses(conversation)
    return conversation[index_assistant_messages[-1]]["content"]


def identify_system_responses(conversation) -> list[int]:
    """Gets the index/indices for system responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "system"]


def identify_assistant_responses(conversation) -> list[int]:
    """Gets the index/indices for assistant responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "assistant"]


def replace_last_assistant_response(conversation, replacement_content: str) -> list:
    """Substitutes the last assistant response with a new message."""
    index_assistant_messages = identify_assistant_responses(conversation)
    conversation[index_assistant_messages[-1]]["content"] = replacement_content
    return conversation


def remove_system_messages_following_last_assistant_response(conversation) -> list:
    """Removes all system messages following the last assistant response."""
    index_last_assistant_message = identify_assistant_responses(conversation)[-1]
    index_system_messages = identify_system_responses(conversation)
    subsequent_system_messages = [
        i for i in index_system_messages if i > index_last_assistant_message
    ]
    if subsequent_system_messages:
        del conversation[subsequent_system_messages[0]:]
    return conversation


def grab_last_user_message(conversation: list) -> str:
    """Grab the latest message string from user."""
    index_user_messages = identify_user_messages(conversation)
    if index_user_messages:
        return conversation[index_user_messages[-1]]["content"]
    else:
        return None


def identify_user_messages(conversation) -> list[int]:
    """Gets the index/indices for `assistant` responses."""
    return [i for i, d in enumerate(conversation) if d.get("role") == "user"]


def index_of_assistant_responses_intended_for_user(conversation) -> list[int]:
    """Finds indices assistant messages that are contain human readable
    text (not just commands for the backend)."""
    # Get index of a
    responses_with_readable_text = [
        i
        for (i, message) in enumerate(conversation)
        if message_is_intended_for_user(message["content"])
    ]
    assistant_messages = identify_assistant_responses(conversation)
    idx_responses_intended_for_user = list_intersection(
        assistant_messages, responses_with_readable_text
    )
    idx_responses_intended_for_user = sorted(idx_responses_intended_for_user)

    return idx_responses_intended_for_user


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
    assistant_indices = identify_assistant_responses(conversation)
    del conversation[assistant_indices[-1]]
    return conversation


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
