"""Functions that tend to be reused across scripts."""

import path_setup

import re
import os
import time

from utils.console_chat_display import wrap_message
from utils.backend import dump_to_json
from utils.backend import add_extension
from utils.backend import load_json_from_path
from utils.general import list_intersection
from utils.create_chatbot_response import respond_to_user
from utils.console_chat_display import print_message_without_syntax
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import message_is_readable
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import index_of_assistant_responses
from utils.chat_utilities import grab_last_user_message
from utils.console_chat_display import remove_syntax_from_message

from utils_general import print_wrap
from utils_general import calc_mean_with_confint
from utils_general import print_last_assistent_response
from utils_general import print_last_user_message
from utils_general import get_hash_of_current_git_commit
from utils_general import fill_in_variables_in_prompt_template
from utils_general import dump_prompt_to_markdown_locally
from utils_general import load_local_prompt_template
from utils_general import dump_to_json_locally
from utils_testing_judges import gen_llm_response

import numpy as np
import git
from copy import copy

from utils.backend import (
    get_source_content_and_path,
    load_yaml_file,
    load_textfile_as_string,
    dump_python_variable_to_file,
    create_directory,
)

import pandas as pd

CWD = os.getcwd()


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


def adversary_responds_directly_from_prompt(
    chat, prompt_template, model="gpt-35-turbo-16k"
) -> str:
    """Takes the conversation from the assistants point of view and generates
    the next nudge-question using the provided prompt template. The prompt
    template is assumed to take the most recent chatbot-message
    `chatbot_message` as an argument which it inserts into its prompt."""
    idx = grab_last_response_intended_for_user(chat)
    chatbot_message = remove_syntax_from_message(chat[idx]["content"])
    user_message = grab_last_user_message(chat)
    prompt_adversary = prompt_template.format(
        chatbot_message=chatbot_message, user_message=user_message
    )
    dump_prompt_to_markdown_locally(
        prompt_adversary, "files/prompt-completed/prompt_completed.md"
    )
    response = gen_llm_response(prompt_adversary, model)
    return response


def adversarial_nudger_has_conversation_with_chatbot(
    prompt_template,
    chat,
    n_nudges=4,
    chatbot_id="mental_health",
    model_llm_adversary="gpt-4",
    cooldown_time=15,
):
    """Runs an automated conversation between the chatbot (specified by
    chatbot_id) and the adverserial nudger which is prompt-engineered to try to
    tempt the chatbot to adopt a specific out-of-bounds role."""
    print_last_assistent_response(chat)

    counter = 0
    while counter < n_nudges:
        print(f"\n\nNudge attempt {counter}:\n\n")
        response = adversary_responds_directly_from_prompt(
            chat,
            prompt_template,
            model=model_llm_adversary,
        )
        chat.append({"role": "user", "content": response})
        dump_to_json_locally(
            chat,
            "files/chat_current.json",
        )
        print("Cooling off...")
        time.sleep(cooldown_time)
        print_last_user_message(response)

        chat, _ = respond_to_user(chat, chatbot_id)
        print_last_assistent_response(chat)
        counter += 1

        dump_to_json_locally(
            chat,
            "files/chat_current.json",
        )
        print("Cooling off...")
        time.sleep(cooldown_time)

    return chat


def load_chat_and_prompt_for_roleplay_test(trickster_tests, target_role):
    """Loads the conversation that initiates the role-play where the
    adverserially prompted chatbot plays a role where it tries to get the other
    chatbot to talk about subjects that are far out of its scope."""
    prompt_template = load_local_prompt_template(
        trickster_tests[target_role]["prompt_path"]
    )
    chat = load_json_from_path(trickster_tests[target_role]["initial_chat_path"])
    return chat, prompt_template
