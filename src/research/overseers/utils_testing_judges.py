"""Functions that tend to be reused across scripts."""

import path_setup

import os
from utils.backend import add_extension
from utils.backend import load_json_from_path
from utils.chat_utilities import generate_and_add_raw_bot_response

from utils_general import calc_mean_with_confint
from utils_general import get_hash_of_current_git_commit
from utils_general import fill_in_variables_in_prompt_template
from utils_general import dump_prompt_to_markdown_locally
from utils_general import dump_to_json_locally
from utils_general import load_local_prompt_template

from utils.backend import (
    get_source_content_and_path,
    load_yaml_file,
    load_textfile_as_string,
)

import pandas as pd

CWD = os.getcwd()


# %% AI RESPONSE GENERATION
def gen_llm_response(prompt=str, deployment_name="gpt-35-turbo-16k"):
    """Generates a response to the prompt using the specific LLM."""
    conversation = [{"role": "system", "content": prompt}]
    return generate_and_add_raw_bot_response(
        conversation, deployment_name=deployment_name
    )[-1]["content"]


# %% RUN EXPERIMENT
def f_correct_response(value: str):
    if value == "ACCEPTED":
        return lambda answer: True if "ACCEPTED" in answer else False
    else:
        return lambda answer: True if "ACCEPTED" not in answer else False


def run_experiment_general(
    prompt_variables: dict,
    prompt_template_path_relative="source_fidelity",
    f_get_response=gen_llm_response,
    f_correct_response=lambda answer: True if "ACCEPTED" in answer else False,
    n_exp=10,
    test_name=None,
):
    """Runs experiment that tests ability of AI-judges to correctly classify a
    labelled test-case as either ACCEPTED or REJECTED/WARNING. re-runs multiple
    times in order to get estimate likelihood of successful evaluation."""
    # Create prompt
    prompt_template = load_local_prompt_template(prompt_template_path_relative)
    prompt = fill_in_variables_in_prompt_template(prompt_template, prompt_variables)
    dump_prompt_to_markdown_locally(
        prompt, "files/prompt-completed/prompt_completed.md"
    )

    # Run trials
    responses = pd.DataFrame(
        [f_get_response(prompt=prompt) for i in range(n_exp)],
        columns=["response"],
    )

    # Analyze information
    responses["correct_judgement"] = responses["response"].apply(f_correct_response)
    responses = responses[["correct_judgement", "response"]]
    responses["correct_judgement"].mean()
    ci = calc_mean_with_confint(responses["correct_judgement"])

    print(f"\n** Results (test name: {test_name}) ** ")
    print(f"prompt: {prompt_template_path_relative}")
    print(f"Response function: {f_get_response.__name__}")
    print(ci)

    results = {
        "experiment_info": {
            "prompt_name": prompt_template_path_relative,
            "prompt_variables": prompt_variables,
            "git_commit_hash": get_hash_of_current_git_commit(),
            "response_generating_function": f_get_response.__name__,
        },
        "ci_success_rate": ci,
        "raw_data": {
            "response_is_correct": responses["correct_judgement"].values.tolist(),
            "response_raw": responses["response"].values.tolist(),
        },
    }

    dump_to_json_locally(results, f"results/current.json")

    return results


def run_experiment_for_test_case(
    f_get_response=gen_llm_response,
    n_exp=10,
    prompt_template_path_relative="swift_judge_source_fidelity_v1",
    test_case_name="starting_a_movement",
):
    """Runs experiment that tests ability of AI-judges to correctly classify a
    labelled test-case as either ACCEPTED or REJECTED/WARNING. re-runs multiple
    times in order to get estimate likelihood of successful evaluation."""
    # Create prompt-variables dictionary
    test_cases = load_test_cases()
    test_case = test_cases[test_case_name]
    if "source_name" in test_case.keys():
        test_case["source"] = get_source(test_case["source_name"])
        # test_case["source"] = remove_text_in_brackets(test_case["source"])

    if test_case["value"] == "ACCEPTED":
        f_correct_response = lambda answer: True if "ACCEPTED" in answer else False
    else:
        f_correct_response = lambda answer: True if "ACCEPTED" not in answer else False

    results = run_experiment_general(
        prompt_variables=test_case,
        prompt_template_path_relative=prompt_template_path_relative,
        f_correct_response=f_correct_response,
        f_get_response=f_get_response,
        n_exp=n_exp,
        test_name=test_case_name,
    )

    return results


# %% PROMPT GENERATION


def get_source(source_name: str) -> str:
    """Gets the content of the specified source."""
    return get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=source_name,
    )[0]


def load_test_cases() -> dict:
    """Loads test_cases.yaml, where each 'case' has a source_id, a bot_message,
    a user message and value such as `WARNING` or `ACCEPTED` indicating the
    label of chatbot message which the AI-judges should be outputting.

    Returns dictionary with fields: source_id, chatbot_message, user_message,
    and value."""
    test_cases_path = os.path.join(CWD, "files/test_cases.yaml")
    return load_yaml_file(test_cases_path)
