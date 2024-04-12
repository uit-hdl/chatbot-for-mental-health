"""Functions that tend to be reused across scripts."""

import path_setup
from utils.console_chat_display import wrap_message
from utils.backend import get_source_content_and_path

import pandas as pd


# %% PRINT UTILITIES
def print_wrap(message, wrap_length=80):
    print(wrap_message(message, wrap_length))


def print_test_names(test_cases):
    print(pd.DataFrame(test_cases.keys()))


# %% PROMPT GENERATION
def get_prompt(test_case: dict, prompt_template: str, print_prompt=False):
    source = get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=test_case["source_id"],
    )[0]
    chatbot_message = test_case["bot_message"]
    prompt = insert_variables_into_prompt(source, chatbot_message, prompt_template)
    if print_prompt:
        print_wrap(prompt)

    return prompt


def insert_variables_into_prompt(source, chatbot_message, prompt_template):
    return prompt_template.format(source=source, chatbot_message=chatbot_message)
