# %%
import path_setup

from utils_autochat import adversary_responds_directly_from_prompt
from utils_autochat import adversarial_nudger_has_conversation_with_chatbot
from utils_autochat import load_chat_and_prompt_for_roleplay_test
from utils_general import print_last_assistent_response
from utils_general import print_last_user_message
from utils_general import dump_to_json_locally
import time


from utils.backend import PROMPTS
from utils.backend import dump_chat_to_markdown
from utils.create_chatbot_response import respond_to_user
from utils.create_chatbot_response import respond_to_user

# %% Manual iteration
trickster_tests = {
    "social_interaction_expert": {
        "initial_chat_path": "results/chat-dumps/start_of_social_expert/conversation.json",
        "prompt_path": "files/prompt-templates/adverseries/social_interaction_nudger.md",
    },
    "social_activist": {
        "initial_chat_path": "results/chat-dumps/start_of_social_activist/conversation.json",
        "prompt_path": "files/prompt-templates/adverseries/social_movement_nudger.md",
    },
    "dietary_expert": {
        "initial_chat_path": "results/chat-dumps/start_of_dietary_expert/conversation.json",
        "prompt_path": "files/prompt-templates/adverseries/dietary_nudger.md",
    },
}

target_role = "social_interaction_expert"


# %% INITIATE CONVERSATION FROM CHECKPOINT
target_role = "social_interaction_expert"
chat, prompt_template = load_chat_and_prompt_for_roleplay_test(
    trickster_tests, target_role
)
chat[0]["content"] = PROMPTS["mental_health"]

# %% Initiate counter
counter = 0
cooldown_time = 10

# %% Manually run cycle
response = adversary_responds_directly_from_prompt(
    chat, prompt_template, deployment_name="gpt-35-turbo-16k"
)
chat.append({"role": "user", "content": response})
dump_to_json_locally(
    chat,
    "files/chat_current.json",
)

time.sleep(cooldown_time)

print_last_user_message(response)

chat, _ = respond_to_user(chat, "mental_health")
print_last_assistent_response(chat)
dump_to_json_locally(
    chat,
    "files/chat_current.json",
)
time.sleep(cooldown_time)

counter += 1
