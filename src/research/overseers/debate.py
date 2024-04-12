"""Tried to create a debate, did not work out well..."""

# %%
import path_setup

from utils.chat_utilities import get_response_to_single_message_input
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import load_yaml_file
from utils.backend import load_textfile_as_string
from utils.backend import get_source_content_and_path

from functions import print_wrap
from functions import print_test_names
import os
import pandas as pd

# %% SETUP

# Dump paths
CWD = os.getcwd()


def load_test_cases():
    test_cases_path = os.path.join(CWD, "files/test_cases.yaml")
    return load_yaml_file(test_cases_path)


def load_local_prompt(prompt_name):
    return load_textfile_as_string(
        os.path.join(CWD, f"files/prompt-templates/{prompt_name}.md")
    )


test_cases = load_test_cases()


def insert_variables_into_prompt(source, chatbot_message, prompt_template):
    return prompt_template.format(source=source, chatbot_message=chatbot_message)


def get_source_and_chatbot_message(test_case_id):
    source = get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=test_cases[test_case_id]["source_id"],
    )[0]
    chatbot_message = test_cases[test_case_id]["bot_message"]
    return source, chatbot_message


def get_prompt(test_case_id, prompt_template, print_prompt=False):
    source = get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=test_cases[test_case_id]["source_id"],
    )[0]
    chatbot_message = test_cases[test_case_id]["bot_message"]
    prompt = insert_variables_into_prompt(source, chatbot_message, prompt_template)
    if print_prompt:
        print_wrap(prompt)

    return prompt


def get_gpt35_turbo_judge_evaluation(test_case_id, prompt, temperature=0.5):
    """Gets the evaluation of GPT-3.5-turbo. Returns dictionary with
    keys 'repsonse' and 'true_value'"""
    value = test_cases[test_case_id]["value"]
    evaluation = generate_and_add_raw_bot_response(
        initiate_conversation_with_prompt(prompt),
        deployment_name="gpt-35-turbo-test",
        temperature=temperature,
    )[-1]["content"]
    return {
        "evaluation": evaluation,
        "true_value": value,
    }


def evaluate_decision(result_dict):
    """Converts bot evaluation and ground truth to True/False. A positive (True)
    is defined as anything that is not 'ACCEPTED'."""
    decision_bot = "ACCEPTED" not in result_dict["evaluation"]
    true_value = "ACCEPTED" not in result_dict["true_value"]
    return decision_bot, true_value


# %% SIMPLE TESTS
# %% STARTING A SOCIAL MOVEMENT
source, chatbot_message = get_source_and_chatbot_message("starting_a_movement")
prompt_sceptic = load_local_prompt("version2").format(
    source=source, chatbot_message=chatbot_message
)


sceptic_message = get_gpt35_turbo_judge_evaluation(
    "starting_a_movement", prompt_sceptic, temperature=0.5
)
print_wrap(sceptic_message["evaluation"])
prompt_template_opponent_of_sceptic = load_local_prompt("version21").format(
    chatbot_message=chatbot_message, source=source, sceptic_message=sceptic_message
)
opponent_output = get_gpt35_turbo_judge_evaluation(
    "starting_a_movement", prompt_template_opponent_of_sceptic, temperature=0.5
)
print_wrap(opponent_output["evaluation"])


prompt_template_opponent_of_sceptic = load_local_prompt("version21").format(
    chatbot_message=chatbot_message, source=source, sceptic_message=opponent_output
)

# %%
print("** ANSWER ** \n")
print_wrap(output["evaluation"])
