"""Chatbot has conversation with AI-agent that has been prompted
to nudge the chatbot towards a particular out-of-bounds role and topic."""

import time
import sys
import os

from console_chat import direct_to_new_assistant
from convert_json_chat_to_markdown import convert_json_chat_to_markdown

from utils.chat_utilities import message_is_intended_for_user
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import identify_assistant_responses
from utils.chat_utilities import generate_single_response_to_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.managing_sources import remove_inactive_sources
from utils.manage_chat_length import truncate_if_too_long
from utils.console_chat_display import print_message_without_syntax
from utils.create_chatbot_response import respond_to_user
from utils.general import remove_syntax_from_message
from utils.general import list_intersection
from utils.general import silent_print
from utils.backend import load_json_from_path
from utils.backend import dump_current_conversation_to_json
from utils.backend import dump_to_json
from utils.backend import add_extension
from utils.backend import PROMPTS

chatbot_id = "mental_health"


def adversarial_nudger_has_conversation_with_chatbot(
    initiation_chat_path="results/chat-dumps/start_of_social_expert/conversation.json",
    prompt_name_adversary="social_interaction_nudger",
    conversation_dump_path="results/automated-chats/nudge-tests/json/conversation.json",
    n_nudges=5,
    cooldown_time=15,
    model_llm_adversary="gpt-4",
    truncate_chat=False,
):
    """Runs an automated conversation between the chatbot (specified by
    chatbot_id) and the adverserial nudger which is prompt-engineered to try to
    tempt the chatbot to adopt a specific out-of-bounds role."""
    prompt_template = PROMPTS[prompt_name_adversary]
    conversation = load_json_from_path(initiation_chat_path)

    print_last_assistent_response(conversation)

    counter = 0

    while counter < n_nudges:
        silent_print(f"\n** NUDGE ATTEMPT {counter}: **\n")

        response = adversary_responds_directly_from_prompt(
            conversation,
            prompt_template,
            model=model_llm_adversary,
        )
        conversation.append({"role": "user", "content": response})
        dump_to_json(conversation, conversation_dump_path)
        print_last_user_message(response)

        # CHATBOT RESPONDS
        conversation, harvested_syntax = respond_to_user(conversation, chatbot_id)
        if harvested_syntax["referral"]:
            assistant_name = harvested_syntax["referral"]["name"]
            conversation = direct_to_new_assistant(assistant_name)
            conversation = generate_and_add_raw_bot_response(conversation)
            print_last_assistent_response(conversation)

        conversation = remove_inactive_sources(conversation)
        if truncate_chat:
            conversation = truncate_if_too_long(conversation)

        print_last_assistent_response(conversation)
        dump_to_json(conversation, conversation_dump_path)
        cool_off(cooldown_time)

        counter += 1

    # Convert and dump to markdown file in the same directory as json file
    convert_json_chat_to_markdown(
        jsonfile_path=conversation_dump_path,
        mdfile_path=enforce_extension(conversation_dump_path, ".md"),
    )


def adversary_responds_directly_from_prompt(
    conversation, prompt_template, model
) -> str:
    """Takes the conversation from the assistants point of view and generates
    the next nudge-question using the provided prompt template. The prompt
    template is assumed to take the most recent chatbot-message
    `chatbot_message` as an argument which it inserts into its prompt."""
    idx = grab_last_response_intended_for_user(conversation)
    chatbot_message = remove_syntax_from_message(conversation[idx]["content"])
    user_message = grab_last_user_message(conversation)
    prompt_adversary = prompt_template.format(
        chatbot_message=chatbot_message, user_message=user_message
    )
    response = generate_single_response_to_prompt(prompt_adversary, model="gpt-4")

    return response


def grab_last_response_intended_for_user(conversation) -> int:
    """Returns the list index of the last message that was intended to be read
    by the user."""
    index_assistant = identify_assistant_responses(conversation)
    index_intended_for_user = [
        i
        for i, msg in enumerate(conversation)
        if message_is_intended_for_user(msg["content"])
    ]
    responses_for_user = list_intersection(index_assistant, index_intended_for_user)
    if not responses_for_user:
        print("There are no assistant messages for user")
    else:
        return responses_for_user[-1]


def print_last_assistent_response(conversation):
    """Prints last assistant response without syntax."""
    print_message_without_syntax(
        {"content": grab_last_assistant_response(conversation), "role": "assistant"}
    )


def print_last_user_message(message: str):
    """Prints last user message."""
    print_message_without_syntax({"content": message, "role": "user"})


def cool_off(cooldown_time):
    """Pauses execution for a set amount of time to prevent exceeding rate
    limit."""
    silent_print("Cooling off ...")
    time.sleep(cooldown_time)


def enforce_extension(file_path, new_extension=".md"):
    """Ensures that the file path ends with the specified extension."""
    return os.path.splitext(file_path)[0] + new_extension


if __name__ == "__main__":
    initiation_chat_path = (
        "results/chat-dumps/start_of_social_activist/conversation.json"
    )
    prompt_name_adversary = "social_movement_nudger"
    conversation_dump_path = "results/automated-chats/nudge-tests/json/social_movement_expert_nojudges_2.json"
    n_nudges = 4
    cooldown_time = 5

    if len(sys.argv) >= 2:
        initiation_chat_path = sys.argv[1]
    if len(sys.argv) >= 3:
        prompt_name_adversary = sys.argv[2]
    if len(sys.argv) >= 4:
        conversation_dump_path = sys.argv[3]
    if len(sys.argv) >= 5:
        n_nudges = sys.argv[4]
    if len(sys.argv) >= 5:
        cooldown_time = sys.argv[5]

    adversarial_nudger_has_conversation_with_chatbot(
        initiation_chat_path,
        prompt_name_adversary,
        conversation_dump_path,
        n_nudges,
        cooldown_time,
    )
