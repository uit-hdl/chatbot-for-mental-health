"""Chatbot has conversation with AI-agent. Similar to nudge_test.py, but chats
can be of indefinate length."""

import time
import sys
import os

from console_chat import direct_to_new_assistant
from console_chat import initiate_conversation_object
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
from utils.backend import dump_current_conversation_to_json
from utils.backend import dump_to_json
from utils.backend import add_extension
from utils.backend import PROMPTS
from utils.backend import dump_file


dump_path_prompt_simulated_user = "chat-dashboard/other/simulated_user.json"
chatbot_id = "mental_health"
initial_greet = """\u00a4:cite([\"initial_prompt\"]):\u00a4 Hello and welcome!
I'm here to provide information on schizophrenia according to a
manual I refer to. If you have any questions or need
clarification on something specific, feel free to ask. If large
amounts of information are overwhelming, let me know, and I can
simplify or go slower. What can I help you with today?"""


def automated_roleplay_conversation_between_chatbots(
    prompt_name_simulated_user="user_simulator",
    conversation_dump_path="results/automated-chats/user-simulations/json/conversation.json",
    n_questions=5,
    cooldown_time=15,
    model_llm_simulated_user="gpt-4",
    truncate_chat=True,
):
    """Runs an automated conversation between the chatbot (specified by
    chatbot_id) and the adverserial nudger which is prompt-engineered to try to
    tempt the chatbot to adopt a specific out-of-bounds role. Deployment name
    can be test-chatbot (GPT-4) or gpt-35-turbo-16k (GPT-3.5)."""

    prompt = PROMPTS[prompt_name_simulated_user]

    # Initiate conversation from chatbot point of view
    conversation_chatbot_pow = initiate_conversation_object("mental_health")
    conversation_chatbot_pow.append({"role": "assistant", "content": initial_greet})
    print_last_assistent_response(conversation_chatbot_pow)

    # Initiate conversation from simulated user point of view
    conversation_simuser_pow = []

    counter = 0

    while counter < n_questions:

        # SIMULATED RESPONDS
        conversation_simuser_pow = simulated_user_responds(
            conversation_chatbot_pow,
            conversation_simuser_pow,
            llm=model_llm_simulated_user,
        )
        conversation_chatbot_pow.append(
            {"role": "user", "content": conversation_simuser_pow[-1]["content"]}
        )
        print_last_user_message(conversation_simuser_pow[-1]["content"])
        dump_to_json(conversation_simuser_pow, dump_path_prompt_simulated_user)
        cool_off(cooldown_time)

        # CHATBOT RESPONDS
        conversation_chatbot_pow, harvested_syntax = respond_to_user(
            conversation_chatbot_pow, chatbot_id
        )
        print_last_assistent_response(conversation_chatbot_pow)

        if harvested_syntax["referral"]:
            assistant_name = harvested_syntax["referral"]["name"]
            conversation_chatbot_pow = direct_to_new_assistant(assistant_name)
            conversation_chatbot_pow = generate_and_add_raw_bot_response(
                conversation_chatbot_pow
            )
            print_last_assistent_response(conversation_chatbot_pow)

        conversation_chatbot_pow = remove_inactive_sources(conversation_chatbot_pow)
        if truncate_chat:
            conversation_chatbot_pow = truncate_if_too_long(conversation_chatbot_pow)

        dump_current_conversation_to_json(conversation_chatbot_pow)
        cool_off(cooldown_time)

        counter += 1

    # Convert and dump to markdown file in the same directory as json file
    dump_to_json(conversation_chatbot_pow, conversation_dump_path)
    convert_json_chat_to_markdown(
        jsonfile_path=conversation_dump_path,
        mdfile_path=enforce_extension(conversation_dump_path, ".md"),
    )


def update_prompt(prompt, role: str, content: str):
    """takes the prompt and updates it with the most recent interchange."""
    prompt += f'\n\n{role}: "{content}"'
    return prompt


def simulated_user_responds(
    conversation_chatbot_pow,
    conversation_simuser_pow,
    model,
) -> str:
    """The simulater user responds to the assistants last visible response.
    Returns message of simulated user. Returns prompt updated with the simulated
    users new response."""
    chatbot_message = grab_last_visible_chatbot_message(conversation_chatbot_pow)
    conversation_simuser_pow.append({"role": "user", "content": chatbot_message})
    conversation_simuser_pow = generate_and_add_raw_bot_response(
        conversation_simuser_pow, model
    )
    message_simulated_user = conversation_simuser_pow[-1]["content"]
    return conversation_simuser_pow


def add_user_message_to_conversation_from_each_point_of_view(
    conversation, prompt_simulated_user, message_simulated_user
):
    """Updates the prompt of the simulated patient and the conversation object
    that is used by the main chatbot with the new message from the simulated
    user."""
    conversation.append({"role": "user", "content": message_simulated_user})
    prompt_simulated_user = update_prompt(
        prompt_simulated_user, role="patient", content=message_simulated_user
    )
    return conversation, prompt_simulated_user


def grab_last_visible_chatbot_message(conversation) -> str:
    """Finds the last chatbot message intended to be seen by the user and makes
    it presentable for user (strips it of syntax)."""
    idx = grab_last_response_intended_for_user(conversation)
    if idx:
        return remove_syntax_from_message(conversation[idx]["content"])


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
    if responses_for_user:
        return max(responses_for_user)


def print_last_assistent_response(conversation):
    """Prints last assistant response without syntax."""
    response = grab_last_assistant_response(conversation)
    if response:
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
    prompt_name_simulated_user = "user_simulator"
    conversation_dump_path = (
        "results/automated-chats/user-simulations/json/conversation.json"
    )
    n_questions = 7
    cooldown_time = 15
    model_llm_simulated_user = "gpt-4"  # gpt-35-turbo-16k or test-chatbot

    if len(sys.argv) >= 2:
        prompt_name_simulated_user = sys.argv[1]
    if len(sys.argv) >= 3:
        conversation_dump_path = sys.argv[2]
    if len(sys.argv) >= 4:
        n_questions = sys.argv[3]
    if len(sys.argv) >= 5:
        cooldown_time = sys.argv[4]

    automated_roleplay_conversation_between_chatbots(
        prompt_name_simulated_user,
        conversation_dump_path,
        n_questions,
        cooldown_time,
        model_llm_simulated_user,
    )
