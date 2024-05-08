# %%
import path_setup

from utils_autochat import adversary_responds_directly_from_prompt
from utils_autochat import adversarial_nudger_has_conversation_with_chatbot
from utils_autochat import load_chat_and_prompt_for_roleplay_test
from utils_general import print_last_assistent_response
from utils_general import print_last_user_message
from utils_general import dump_to_json_locally

from utils.backend import dump_chat_to_markdown
from utils.create_chatbot_response import respond_to_user

# %% Manual iteration
trickster_tests = {
    "social_interaction_expert": {
        "initial_chat_path": "results/chat-dumps/start_of_social_expert/conversation.json",
        "prompt_path": "adverseries/social_interaction_nudger.md",
    },
    "social_activist": {
        "initial_chat_path": "results/chat-dumps/start_of_social_activist/conversation.json",
        "prompt_path": "adverseries/social_movement_nudger.md",
    },
    "dietary_expert": {
        "initial_chat_path": "results/chat-dumps/start_of_dietary_expert/conversation.json",
        "prompt_path": "adverseries/dietary_nudger.md",
    },
}

target_role = "social_interaction_expert"


# %% Using function
target_role = "social_interaction_expert"

for trial in range(5):
    chat, prompt_template = load_chat_and_prompt_for_roleplay_test(
        trickster_tests, target_role
    )
    print(f"TRIAL NUMBER: {trial}")
    chat = adversarial_nudger_has_conversation_with_chatbot(
        prompt_template,
        chat,
        n_nudges=5,
        cooldown_time=15,
        deployment_name_adversary="test-chatbot",
    )
    dump_chat_to_markdown(
        chat, f"results/automated-chats/nudge-tests/md/{target_role}_withjudges_{trial}.md"
    )
    dump_to_json_locally(chat, f"results/nudge-tests/json/{target_role}_withjudges_{trial}.json")

# %% Manually run cycle
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
    print(counter)
    response = adversary_responds_directly_from_prompt(
        chat, prompt_template, deployment_name="gpt-35-turbo-16k"
    )
    print_last_user_message(response)
    chat.append({"role": "user", "content": response})
    chat, _ = respond_to_user(chat, "mental_health")
    print_last_assistent_response(chat)
    counter += 1

dump_chat_to_markdown(chat, "chat_ex.md")
