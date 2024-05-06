"""Functions that tend to be reused across scripts."""

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


def remove_text_in_brackets(text):
    """"""
    return re.sub(r"\[.*?\]", "", text)


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


# %% RUN EXPERIMENT
def f_correct_response(value: str):
    if value == "ACCEPTED":
        return lambda answer: True if "ACCEPTED" in answer else False
    else:
        return lambda answer: True if "ACCEPTED" not in answer else False


def run_experiment_for_test_case(
    f_get_response=f_get_response_gpt35turbo,
    n_exp=10,
    prompt_template_path_relative="swift_judge_source_fidelity_v1",
    test_case_name="starting_a_movement",
):
    """Tests the

    model: gpt-35-turbo-16k or gpt-instruct."""
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


def run_experiment_general(
    prompt_variables: dict,
    prompt_template_path_relative="source_fidelity",
    f_get_response=f_get_response_gpt35turbo,
    f_correct_response=lambda answer: True if "ACCEPTED" in answer else False,
    n_exp=10,
    test_name=None,
):
    """Tests the

    model: gpt-35-turbo-16k or gpt-instruct."""
    # Create prompt
    prompt = load_local_prompt(prompt_template_path_relative)
    prompt_completed = prompt.format(**prompt_variables)
    dump_prompt_to_markdown_locally(
        prompt_completed, "files/prompt-completed/prompt_completed.md"
    )

    # Run trials
    responses = pd.DataFrame(
        [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
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


def load_local_prompt(prompt_name):
    """Loads prompt from files/prompts/prompt_name."""
    prompt_name = add_extension(prompt_name, ".md")
    return load_textfile_as_string(
        os.path.join(CWD, f"files/prompt-templates/{prompt_name}")
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


# %% OTHER DUMPING AND LOADING
def dump_string_locally(dump_object, filepath_relative):
    """Ex. are file/prompt-completed/promptie.txt or whatever.md"""
    filepath = os.path.join(CWD, filepath_relative)
    dump_python_variable_to_file(dump_object, filepath)


def dump_prompt_to_markdown_locally(string, filepath_relative="files/local_dump.md"):
    """Dumps string to a textfile to .md file. Include extension in path."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)
        print(f"Prompt dumped to {full_path}")


def dump_string_locally(string, filepath_relative="files/local_dump.md"):
    """Dumps string to a textfile to .md file."""
    full_path = os.path.join(CWD, filepath_relative)
    create_directory(full_path)
    with open(full_path, "w") as file:
        file.write(string)


def dump_to_json_locally(variable, filepath_relative):
    full_path = os.path.join(CWD, filepath_relative)
    dump_to_json(dump_dict=variable, file_path=full_path)
    print(f"Result dumped to {full_path}")


# %% ADVERSERIAL CHATBOT


def strip_system_messages(chat):
    return [message for message in chat if message["role"] != "system"]


def add_initial_prompt(chat, prompt):
    chat = copy(chat)
    return [{"role": "system", "content": prompt}] + chat


def remove_invisible_part_of_conversation(chat):
    chat = copy(chat)
    chat = [
        message for message in chat if message_is_intended_for_user(message["content"])
    ]
    for i, message in enumerate(chat):
        chat[i]["content"] = remove_syntax_from_message(message["content"])
    return chat


def flip_user_and_assistant_role(chat):
    chat = copy(chat)
    user_messages = [i for i, message in enumerate(chat) if message["role"] == "user"]
    assistant_messages = [
        i for i, message in enumerate(chat) if message["role"] == "assistant"
    ]
    for i, message in enumerate(chat):
        if i in user_messages:
            chat[i]["role"] = "assistant"
        elif i in assistant_messages:
            chat[i]["role"] = "user"

    return chat


def grab_last_response_intended_for_user(chat) -> int:
    """Returns the list index of the last message that was intended to be read
    by the user."""
    index_assistant = identify_assistant_responses(chat)
    index_intended_for_user = [
        i for i, msg in enumerate(chat) if message_is_intended_for_user(msg["content"])
    ]
    responses_for_user = list_intersection(index_assistant, index_intended_for_user)
    if not responses_for_user:
        print("There are no assistant messages for user")
    else:
        return responses_for_user[-1]


def delete_last_message(chat) -> list:
    """Deletes the last message in the chat."""
    del chat[-1]
    return chat


def adversary_responds_to_assistant(
    chat_assistant,
    chat_adversary,
    reminder_message=None,
    deployment_name="gpt-35-turbo-16k",
):
    """Takes the chat from the assistnats point of view, generates a response to
    its last message, and finally adds that response to the chat from the
    adversaries point of view. Note: from the adversaries point of view, IT is
    the assistant, and the assistant is the user."""
    # Update conversations
    idx = grab_last_response_intended_for_user(chat_assistant)
    chat_adversary.append(
        {
            "role": "user",
            "content": remove_syntax_from_message(chat_assistant[idx]["content"]),
        }
    )
    if reminder_message:
        chat_adversary.append({"content": reminder_message, "role": "system"})
    # Generate adversary message
    chat_adversary = generate_and_add_raw_bot_response(
        chat_adversary, deployment_name=deployment_name
    )
    return chat_adversary


def assistant_responds_to_adversary(
    chat_assistant, message_adversary, system_message=None
):
    chat_assistant.append(
        {
            "role": "user",
            "content": message_adversary,
        }
    )
    if system_message:
        chat_assistant.append(
            {
                "role": "system",
                "content": system_message,
            }
        )
    # GENERATE ASSISTANTS RESPONSE
    chat_assistant, _ = respond_to_user(chat_assistant, chatbot_id="mental_health")

    return chat_assistant


def adversary_responds_directly_from_prompt(
    chat, prompt_template, deployment_name="gpt-35-turbo-16k"
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
    response = f_get_response_gpt35turbo(
        prompt_adversary, deployment_name=deployment_name
    )
    return response


def adversarial_nudger_has_conversation_with_chatbot(
    prompt_template,
    chat,
    n_nudges=4,
    chatbot_id="mental_health",
):
    """Runs an automated conversation between the chatbot (specified by
    chatbot_id) and the adverserial nudger which is prompt-engineered to try to
    tempt the chatbot to adopt a specific out-of-bounds role."""
    print_last_user_message(chat)

    counter = 0
    while counter < n_nudges:
        response = adversary_responds_directly_from_prompt(chat, prompt_template)
        chat.append({"role": "user", "content": response})
        print_last_user_message(response)
        chat, _ = respond_to_user(chat, chatbot_id)
        print_last_assistent_response(chat)
        counter += 1

    return chat
