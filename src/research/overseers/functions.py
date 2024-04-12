"""Functions that tend to be reused across scripts."""

import path_setup

import os
from utils.console_chat_display import wrap_message
import numpy as np

from utils.backend import (
    get_source_content_and_path,
    load_yaml_file,
    load_textfile_as_string,
)

import pandas as pd

CWD = os.getcwd()


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


def get_source(source_name):
    return get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=source_name,
    )[0]


def load_test_cases() -> dict:
    """Loads test_cases.yaml, where each 'case' has a source_id, a bot_message,
    and value such as `WARNING` or `ACCEPTED` indicating how the fact-checkers
    should rate that chatbot message.

    Returns dictionary with fields: source_id, bot_message, and value."""
    test_cases_path = os.path.join(CWD, "files/test_cases.yaml")
    return load_yaml_file(test_cases_path)


def load_question_response_pairs():
    """Loads examples with pairs of user questions and chatbot responses.

    Returns dict with keys: source_id, bot_message, user_question, and value."""
    test_cases_path = os.path.join(CWD, "files/question_response_pairs.yaml")
    return load_yaml_file(test_cases_path)


def load_local_prompt(prompt_name):
    """Loads prompt from files/prompts/prompt_name"""
    return load_textfile_as_string(
        os.path.join(CWD, f"files/prompt-templates/{prompt_name}.md")
    )


def get_prompt(test_case, prompt_template, print_prompt=False):
    source = get_source(test_case["source_id"])
    chatbot_message = test_case["bot_message"]
    prompt = insert_variables_into_prompt(source, chatbot_message, prompt_template)
    if print_prompt:
        print_wrap(prompt)

    return prompt


# %% NUMERICAL ANALYSIS
def calc_mean_with_confint(array, return_ci=True, axis=0, n_rounding=None):
    """Computes the mean of array and optionally returns 95% confidence
    interval. array can be vector or multi-dimensional array, in which case
    it computes means and confidence intervas across the specified axis.

    Returns CI on the form: mean, lower, upper.
    """
    avg = np.nanmean(array, axis=axis)

    if return_ci is True:
        n_samples = np.shape(array)[axis]
        stdev_estimator = np.nanstd(array, axis=axis) / np.sqrt(n_samples)
        ci_lower = avg - stdev_estimator * 1.96
        ci_upper = avg + stdev_estimator * 1.96
        if n_rounding:
            avg = avg.round(n_rounding)
            ci_lower = ci_lower.round(n_rounding)
            ci_upper = ci_upper.round(n_rounding)
        return {"mean": avg, "lower": ci_lower, "upper": ci_upper}
    return avg
