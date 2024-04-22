"""Functions that tend to be reused across scripts."""

import path_setup
import re
import os
from utils.console_chat_display import wrap_message
from utils.backend import dump_to_json
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import generate_single_response_using_gpt35_turbo_instruct
import numpy as np
import git

from utils.backend import (
    get_source_content_and_path,
    load_yaml_file,
    load_textfile_as_string,
    dump_python_variable_to_file,
    get_full_path_and_create_dir,
    create_directory,
)

import pandas as pd

CWD = os.getcwd()


# %% PRINT UTILITIES
def print_wrap(message, wrap_length=80):
    print(wrap_message(message, wrap_length))


def print_test_names(test_cases):
    print(pd.DataFrame(test_cases.keys()))


# %% GIT
def get_hash_of_current_git_commit():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


# %% AI RESPONSE GENERATION
def f_get_response_gpt35turbo(prompt=str, deployment_name="gpt-35-turbo-16k"):
    conversation = [{"role": "system", "content": prompt}]
    return generate_and_add_raw_bot_response(
        conversation, deployment_name=deployment_name
    )[-1]["content"]


def get_response_gpt_turbo_instruct(prompt=str):
    conversation = [{"role": "system", "content": prompt}]
    return generate_single_response_using_gpt35_turbo_instruct(conversation)


# %% RUN EXPERIMENT
def f_correct_response(value: str):
    if value == "ACCEPTED":
        return lambda answer: True if "ACCEPTED" in answer else False
    else:
        return lambda answer: True if "ACCEPTED" not in answer else False


def run_experiment(
    f_get_response=f_get_response_gpt35turbo,
    n_exp=10,
    prompt_name="swift_judge_source_fidelity_v1",
    test_case_name="starting_a_movement",
):
    """Tests the

    model: gpt-35-turbo-16k or gpt-instruct."""
    # Create prompt
    prompt = load_local_prompt(prompt_name)
    test_cases = load_test_cases()
    test_case = test_cases[test_case_name]
    prompt_completed = prompt.format(**test_case)
    dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

    # Run trials
    responses = pd.DataFrame(
        [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
        columns=["response"],
    )

    # Analyze information
    f_correct_answer = f_correct_response(test_case["value"])
    responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
    responses = responses[["correct_judgement", "response"]]
    responses["correct_judgement"].mean()
    ci = calc_mean_with_confint(responses["correct_judgement"])

    print(f"\n** Results for case {test_case_name} ** ")
    print(f"prompt: {prompt_name}")
    print(f"Response function: {f_get_response.__name__}")
    print(ci)

    results = {
        "experiment_info": {
            "prompt_name": prompt_name,
            "test_case_name": test_case_name,
            "git_commit_hash": get_hash_of_current_git_commit(),
            "response_generating_function": f_get_response.__name__,
        },
        "ci_success_rate": ci,
        "raw_data": {
            "response_is_correct": responses["correct_judgement"].values.tolist(),
            "response_raw": responses["response"].values.tolist(),
        },
    }

    # Dump results
    dump_to_json_locally(results, f"results/current.json")

    return ci


# %% PROMPT GENERATION
def get_prompt(test_case: dict, prompt_template: str, print_prompt=False):
    source = get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=test_case["source_name"],
    )[0]
    chatbot_message = test_case["chatbot_message"]
    prompt = insert_variables_into_prompt(source, chatbot_message, prompt_template)
    if print_prompt:
        print_wrap(prompt)

    return prompt


def insert_variables_into_prompt(source, chatbot_message, prompt_template):
    return prompt_template.format(source_name=source, chatbot_message=chatbot_message)


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


def load_summarized_source(source_name):
    """Loads prompt from files/prompts/prompt_name"""
    return load_textfile_as_string(
        os.path.join(CWD, f"files/sources-summarized/{source_name}.md")
    )


def get_prompt(test_case, prompt_template, print_prompt=False):
    source = get_source(test_case["source_name"])
    chatbot_message = test_case["chatbot_message"]
    prompt = insert_variables_into_prompt(source, chatbot_message, prompt_template)
    if print_prompt:
        print_wrap(prompt)

    return prompt


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
        return {
            "mean": avg * scaler,
            "lower": ci_lower * scaler,
            "upper": ci_upper * scaler,
        }
    return avg


# %% OTHER DUMPING AND LOADING
def dump_string_locally(dump_object, filepath_relative):
    """Ex. are file/prompt-completed/promptie.txt or whatever.md"""
    filepath = os.path.join(CWD, filepath_relative)
    dump_python_variable_to_file(dump_object, filepath)


def dump_prompt_to_markdown(string, filepath_relative):
    """Dumps string to a textfile to .md file. Include extension in path."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)
        print(f"Prompt dumped to {full_path}")


def dump_string_locally(string, filepath_relative):
    """Dumps string to a textfile to .md file."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)


def dump_to_json_locally(variable, filepath_relative):
    full_path = os.path.join(CWD, filepath_relative)
    dump_to_json(dump_dict=variable, file_path=full_path)
    print(f"Result dumped to {full_path}")
