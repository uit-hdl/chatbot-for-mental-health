# %%
import path_setup

from functions import load_local_prompt
from functions import print_wrap
from utils.backend import load_json_from_path
from utils.backend import load_json_from_path
from utils.chat_utilities import message_is_intended_for_user
from utils.chat_utilities import index_of_assistant_responses_intended_for_user
from utils.chat_utilities import append_system_messages
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import openai
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.create_chatbot_response import respond_to_user
from utils.console_chat_display import print_whole_conversation_with_backend_info
from utils.console_chat_display import remove_syntax_from_message
from utils.console_interactions import rewind_chat_by_n_user_messages
from copy import copy

# %%

chat_0 = load_json_from_path(
    "results/chat-dumps/ai_thinks_it_is_socialisation_expert/conversation_full.json"
)

prompt_adversary = load_local_prompt("other/social_interaction_nudger")

user_messages = [i for i, message in enumerate(chat_0) if message["role"] == "user"]


def strip_system_messages(chat):
    return [message for message in chat if message["role"] != "system"]


def add_initial_prompt(chat, prompt):
    chat = copy(chat)
    return [{"role": "system", "content": prompt}] + chat


def remove_invisible_part_of_conversation(chat):
    chat = copy(chat)
    chat = [
        message for message in chat if message_is_intended_for_user(message["content"])
    ]
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


index_start = user_messages[4]
chat_reset = chat_0[2:index_start]

chat_adversary = copy(chat_reset)
chat_chatbot = copy(chat_reset)

chat_adversary = strip_system_messages(chat_adversary)
chat_adversary = remove_invisible_part_of_conversation(chat_adversary)
chat_adversary = flip_user_and_assistant_role(chat_adversary)
chat_adversary = add_initial_prompt(chat_adversary, prompt_adversary)

print_whole_conversation_with_backend_info(chat_adversary)

# print_whole_conversation_with_backend_info(chat_adversary)
# %%

chat_adversary = generate_and_add_raw_bot_response(
    chat_adversary
)

print_whole_conversation_with_backend_info(chat_adversary)
# %%
chat = copy(chat_adversary)

response = openai.ChatCompletion.create(
    messages=chat,
    engine="gpt-35-turbo-16k",
)

# conversation.append(
#     {
#         "role": response.choices[0].message.role,
#         "content": response.choices[0].message.content.strip(),
#     }
# )
# %%
conversation

index_of_assistant_responses_intended_for_user(conversation)


print_whole_conversation_with_backend_info(chat_adversary)
# print_wrap(conversation)

# %%
remove_syntax_from_message
