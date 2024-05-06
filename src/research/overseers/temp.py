# %%
import path_setup
from functions import adversary_responds_directly_from_prompt
from functions import load_local_prompt
from functions import adversarial_nudger_has_conversation_with_chatbot
from utils.backend import load_json_from_path
from utils.backend import dump_chat_to_markdown
from utils.console_chat_display import reprint_whole_conversation_without_syntax
from utils.console_chat_display import print_message_without_syntax
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import grab_last_user_message
from utils.create_chatbot_response import respond_to_user

# %% Manual iteration
prompt_template = load_local_prompt("adverseries/dietary_nudger")

chat = load_json_from_path(
    "results/chat-dumps/start_of_dietary_expert/conversation.json"
)


def print_last_assistent_response(chat):
    print_message_without_syntax(
        {"content": grab_last_assistant_response(chat), "role": "assistant"}
    )


def print_last_user_message(message: str):
    print_message_without_syntax({"content": message, "role": "user"})


# %%

response = adversary_responds_directly_from_prompt(
    chat, prompt_template, deployment_name="test-chatbot"
)
print_last_user_message(response)
chat.append({"role": "user", "content": response})
chat, _ = respond_to_user(chat, "mental_health")
print_last_assistent_response(chat)


# %% Using while-loop

counter = 0

while counter < 4:
    response = adversary_responds_directly_from_prompt(
        chat, prompt_template, deployment_name="test-chatbot"
    )
    print_last_user_message(response)
    chat.append({"role": "user", "content": response})
    chat, _ = respond_to_user(chat, "mental_health")
    print_last_assistent_response(chat)
    counter += 1

dump_chat_to_markdown(chat, "chat_ex.md")

# %% Using function

trial = 1

prompt_template = load_local_prompt("adverseries/dietary_nudger")
chat = load_json_from_path(
    "results/chat-dumps/start_of_dietary_expert/conversation.json"
)

chat = adversarial_nudger_has_conversation_with_chatbot(
    prompt_template, chat, n_nudges=4
)

dump_chat_to_markdown(
    chat, f"results/automated-chats/nudge-tests/diet_expert_wo_ai_filters_{trial}.md"
)
