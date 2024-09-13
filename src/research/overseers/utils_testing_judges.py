"""Functions that tend to be reused across scripts."""

import path_setup

import os
from utils.general import silent_print
from utils.backend import add_extension
from utils.backend import load_json_from_path
from utils.overseers import extract_verdict
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import generate_single_response_to_prompt

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
def gen_llm_response(prompt=str, model="gpt-35-turbo-16k", max_tokens=400):
    """Generates a response to the prompt using the specific LLM. Model can be
    gpt-35-turbo-16k or gpt-4"""
    conversation = [{"role": "system", "content": prompt}]
    return generate_and_add_raw_bot_response(
        conversation,
        model=model,
        max_tokens=max_tokens,
    )[-1]["content"]


# %% RUN EXPERIMENT
def f_correct_response(value: str):
    if value == "ACCEPTED":
        return lambda answer: True if "ACCEPTED" in answer else False
    else:
        return lambda answer: True if "ACCEPTED" not in answer else False


def run_experiment_general(
    prompt_variables: dict,
    prompt_template_path_relative="files/prompt-templates/source-fidelity/swift_judge_source_fidelity.md",
    model="gpt-35-turbo-16k",
    verdict_map={"AGREE": "ACCEPT", "DENY": "REJECT"},
    correct_verdict="ACCEPT",
    n_exp=10,
    test_name=None,
    print_results=True,
):
    """Runs experiment that tests ability of AI-judges to correctly classify a
    labelled test-case as either ACCEPTED or REJECTED/WARNING. re-runs multiple
    times in order to get estimate likelihood of successful evaluation."""
    # Create prompt
    prompt_template = load_local_prompt_template(prompt_template_path_relative)
    prompt_filled = fill_in_variables_in_prompt_template(
        prompt_template, prompt_variables
    )
    f_llm_response = lambda prompt: gen_llm_response(prompt, model)
    f_check_response = lambda response: is_verdict_correct(
        response, verdict_map, correct_verdict
    )

    responses = []
    for i in range(n_exp):
        response = f_llm_response(prompt=prompt_filled)
        responses.append(response)
        if print_results:
            print(f"RESPONSE:\n{response}")
            print(f"VERDICT: {extract_verdict(response, verdict_map)}")

    responses = pd.DataFrame({"response": responses})
    
    # Analyze information
    responses["correct_verdict"] = responses["response"].apply(f_check_response)
    responses = responses[["correct_verdict", "response"]]
    ci = calc_mean_with_confint(responses["correct_verdict"])

    print(f"\n** Results (test name: {test_name}) ** ")
    print(f"prompt: {prompt_template_path_relative}")
    print(f"Response function: {f_llm_response.__name__}")
    print(ci)

    results = {
        "experiment_info": {
            "prompt_name": prompt_template_path_relative,
            "prompt_variables": prompt_variables,
            "git_commit_hash": get_hash_of_current_git_commit(),
            "llm": model,
            "test_name": test_name,
        },
        "ci_success_rate": ci,
        "raw_data": {
            "response_is_correct": responses["correct_verdict"].values.tolist(),
            "response_raw": responses["response"].values.tolist(),
        },
    }

    dump_to_json_locally(results, f"results/current.json")

    return results


def run_experiment_for_test_case(
    model="gpt-35-turbo-16k",
    n_exp=10,
    prompt_template_path_relative="swift_judge_source_fidelity_v1",
    test_case_name="starting_a_movement",
    verdict_map={"AGREE": "ACCEPT", "DENY": "REJECT"},
    summarize_source=False,
):
    """Runs experiment that tests ability of AI-judges to correctly classify a
    labelled test-case as either ACCEPTED or REJECTED/WARNING. re-runs multiple
    times in order to get estimate likelihood of successful evaluation."""

    test_case = prepare_test_case(test_case_name, summarize_source)
    correct_verdict = test_case["correct_verdict"]

    silent_print(f"** Benchmark: {test_case_name} **")
    silent_print(f"Correct verdict: {correct_verdict}")

    results = run_experiment_general(
        prompt_variables=test_case,
        prompt_template_path_relative=prompt_template_path_relative,
        model=model,
        verdict_map=verdict_map,
        correct_verdict=correct_verdict,
        n_exp=n_exp,
        test_name=test_case_name,
    )

    dump_to_json_locally(results, "results/current_result.json")

    return results


def is_verdict_correct(
    response,
    verdict_map={"AGREE": "ACCEPT", "DENY": "REJECT"},
    correct_verdict="ACCEPT",
) -> bool:
    verdict = extract_verdict(response, verdict_map)
    # Convert to binary: 1 <--> REJECT or WARNING, 0 otherwhise
    verdict = (verdict == "REJECT" or verdict == "WARNING") * 1
    correct_verdict = (correct_verdict == "REJECT" or correct_verdict == "WARNING") * 1
    verdict_is_correct = verdict == correct_verdict
    return verdict_is_correct


def prepare_test_case(test_case_name, summarize_source=False):
    test_cases = load_test_cases()
    test_case = test_cases[test_case_name]
    test_case = update_with_sources(test_case, summarize_source)
    return test_case


def update_with_sources(test_case, summarize_source=False):
    if "source_name" in test_case.keys():
        test_case["source"] = get_source(test_case["source_name"])
        if summarize_source:
            print("Summarizing source ...")
            test_case["source"] = gen_llm_response(
                load_local_prompt_template("other/source_summarizer.md").format(
                    source_content=test_case["source"]
                )
            )
    return test_case


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
