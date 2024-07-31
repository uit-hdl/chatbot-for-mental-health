import copy
from utils.chat_utilities import message_is_readable
from utils.chat_utilities import message_is_readable
from utils.console_chat_display import remove_syntax_from_message
from utils.chat_utilities import index_of_assistant_responses
from utils.general import list_intersection
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.create_chatbot_response import respond_to_user
from utils.chat_utilities import openai
from utils.backend import AZURE_CONFIG
from utils.backend import CHATBOT_CONFIG


def generate_single_response_using_gpt35_turbo_instruct(
    prompt: str,
    model_id="gpt-3.5-turbo-instruct",
    deployment_name=AZURE_CONFIG["deployment_name_single_response"],
    max_tokens=CHATBOT_CONFIG["max_tokens_turbo_instruct"],
    temperature=None,
    return_everything=False,
):
    """Provides a chat completion to a single message input. `Completion` is
    optimized for cases where only a single response is desired, rather than a
    conversation. Note: GPT-3.5-turbo-instruct is fine tuned for this task."""
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


def load_summarized_source(source_name):
    """Loads prompt from files/prompts/prompt_name"""
    return load_textfile_as_string(
        os.path.join(CWD, f"files/sources-summarized/{source_name}.md")
    )


def get_response_gpt_turbo_instruct(prompt=str):
    """Generates response using GPT3.5 Turbo"""
    conversation = [{"role": "system", "content": prompt}]
    return generate_single_response_using_gpt35_turbo_instruct(conversation)


def remove_text_in_brackets(text):
    """Removes text which is in brackets []."""
    return re.sub(r"\[.*?\]", "", text)


def strip_system_messages(chat):
    return [message for message in chat if message["role"] != "system"]


def add_initial_prompt(chat, prompt):
    chat = copy(chat)
    return [{"role": "system", "content": prompt}] + chat


def remove_invisible_part_of_conversation(chat):
    chat = copy(chat)
    chat = [message for message in chat if message_is_readable(message["content"])]
    for i, message in enumerate(chat):
        chat[i]["content"] = remove_syntax_from_message(message["content"])
    return chat


def flip_user_and_assistant_role(chat):
    chat = copy(chat)
    user_messages = [i for i, message in enumerate(chat) if message["role"] == "user"]
    assistant_messages = [
        i for i, message in enumerate(chat) if message["role"] == "assistant"
    ]
    for i, message in enumerate(chat):
        if i in user_messages:
            chat[i]["role"] = "assistant"
        elif i in assistant_messages:
            chat[i]["role"] = "user"

    return chat


def grab_last_response_intended_for_user(chat) -> int:
    """Returns the list index of the last message that was intended to be read
    by the user."""
    index_assistant = index_of_assistant_responses(chat)
    index_intended_for_user = [
        i for i, msg in enumerate(chat) if message_is_readable(msg["content"])
    ]
    responses_for_user = list_intersection(index_assistant, index_intended_for_user)
    if not responses_for_user:
        print("There are no assistant messages for user")
    else:
        return responses_for_user[-1]


def delete_last_message(chat) -> list:
    """Deletes the last message in the chat."""
    del chat[-1]
    return chat


def adversary_responds_to_assistant(
    chat_assistant,
    chat_adversary,
    reminder_message=None,
    deployment_name="gpt-35-turbo-16k",
):
    """Takes the chat from the assistnats point of view, generates a response to
    its last message, and finally adds that response to the chat from the
    adversaries point of view. Note: from the adversaries point of view, IT is
    the assistant, and the assistant is the user."""
    # Update conversations
    idx = grab_last_response_intended_for_user(chat_assistant)
    chat_adversary.append(
        {
            "role": "user",
            "content": remove_syntax_from_message(chat_assistant[idx]["content"]),
        }
    )
    if reminder_message:
        chat_adversary.append({"content": reminder_message, "role": "system"})
    # Generate adversary message
    chat_adversary = generate_and_add_raw_bot_response(
        chat_adversary, deployment_name=deployment_name
    )
    return chat_adversary


def assistant_responds_to_adversary(
    chat_assistant, message_adversary, system_message=None
):
    chat_assistant.append(
        {
            "role": "user",
            "content": message_adversary,
        }
    )
    if system_message:
        chat_assistant.append(
            {
                "role": "system",
                "content": system_message,
            }
        )
    # GENERATE ASSISTANTS RESPONSE
    chat_assistant, _ = respond_to_user(chat_assistant, chatbot_id="mental_health")

    return chat_assistant
