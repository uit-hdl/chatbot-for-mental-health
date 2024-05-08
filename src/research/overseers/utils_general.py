import path_setup

import re
import os
from utils.console_chat_display import wrap_message
from utils.backend import dump_to_json
from utils.backend import add_extension
from utils.general import list_intersection

from utils.create_chatbot_response import respond_to_user
from utils.console_chat_display import print_message_without_syntax
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import message_is_intended_for_user
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import grab_last_user_message
from utils.chat_utilities import identify_assistant_responses
from utils.chat_utilities import grab_last_user_message
from utils.console_chat_display import remove_syntax_from_message
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


# %% PRINT UTILITIES
def print_last_assistent_response(chat):
    """Prints last assistant response without syntax."""
    print_message_without_syntax(
        {"content": grab_last_assistant_response(chat), "role": "assistant"}
    )


def print_last_user_message(message: str):
    """Prints last user message."""
    print_message_without_syntax({"content": message, "role": "user"})


def print_wrap(message: str, wrap_length=80):
    """Prints text in interactive window."""
    print(wrap_message(message, wrap_length))


def print_test_names(test_cases):
    """Prints names that are"""
    print(pd.DataFrame(test_cases.keys()))


# %% GIT
def get_hash_of_current_git_commit():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


def fill_in_variables_in_prompt_template(
    prompt_template,
    prompt_variables: dict,
):
    """Example input arguments:
    prompt_template = "{var1}, is your name {var2}?"
    prompt_variables = {"var1": "Hello!", "var2": "John"}."""
    prompt_completed = prompt_template.format(**prompt_variables)
    return prompt_completed


def get_prompt_arguments(prompt):
    """Gets the name of the placeholders in the string which are referenced in
    the .format() method."""
    return re.findall(r"\{([^{}]+)\}(?![^{}]*\})", prompt)


# %% NUMERICAL ANALYSIS
def calc_mean_with_confint(array, return_ci=True, axis=0, n_rounding=None, scaler=1.0):
    """Computes the mean of array and optionally returns 95% confidence
    interval. array can be vector or multi-dimensional array, in which case it
    computes means and confidence intervas across the specified axis. `scaler`
    muliplies the result in case you want to change units to percentage.

    Returns CI on the form: mean, lower, upper."""
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
        return {
            "mean": avg * scaler,
            "lower": ci_lower * scaler,
            "upper": ci_upper * scaler,
        }
    return avg


def delete_last_message(chat) -> list:
    """Deletes the last message in the chat."""
    del chat[-1]
    return chat


# %% OTHER DUMPING AND LOADING
def dump_string_locally(dump_object, filepath_relative):
    """Ex. are file/prompt-completed/promptie.txt or whatever.md"""
    filepath = os.path.join(CWD, filepath_relative)
    dump_python_variable_to_file(dump_object, filepath)


def dump_prompt_to_markdown_locally(string, filepath_relative="files/local_dump.md"):
    """Dumps string to a textfile to .md file in the location given by:
    src/research/overseers/<filepath_relative>."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)
        print(f"Prompt dumped to {full_path}")


def dump_string_locally(string, filepath_relative="files/local_dump.md"):
    """Dumps string to a textfile to .md file in location given by
    src/research/overseers/<filepath_relative>."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)


def dump_to_json_locally(variable, filepath_relative):
    """Dumps variable to json file in location given by relative path:
    src/research/overseers/<filepath_relative>."""
    full_path = os.path.join(CWD, filepath_relative)
    dump_to_json(dump_dict=variable, file_path=full_path)
    print(f"Result dumped to {full_path}")


def load_local_prompt_template(prompt_template_name):
    """Loads prompt from:
    src/research/overseers/files/prompts/<prompt_template_name>."""
    prompt_template_name = add_extension(prompt_template_name, ".md")
    return load_textfile_as_string(
        os.path.join(CWD, f"files/prompt-templates/{prompt_template_name}")
    )
