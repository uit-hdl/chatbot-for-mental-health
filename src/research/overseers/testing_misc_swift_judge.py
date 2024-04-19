# %%
import path_setup

from functions import load_question_response_pairs
from functions import load_local_prompt
from functions import get_source
from functions import get_prompt_arguments
from functions import print_wrap
from functions import dump_prompt_to_markdown
from functions import calc_mean_with_confint
from functions import dump_to_json_locally
from functions import f_get_response
from functions import run_experiment
from utils.chat_utilities import get_response_to_single_message_input

import numpy as np
import pandas as pd

# %% **********
# %% **TEST 1**
# %% **********
# %% IQ-CLAIMS WITH DISCLAIMER
# %% WARM UP
# create prompt
prompt_name = "swift_judge_misc_disclaimers_only"
prompt = load_local_prompt(prompt_name)
test_cases = load_question_response_pairs()
# run get_prompt_arguments(prompt) to see prompt-arguments
test_case_name = "can_intellegence_be_measured_with_disclaimer"
f_correct_answer = lambda answer: True if "ACCEPTED" in answer else False
test = test_cases[test_case_name]
prompt_completed = prompt.format(
    chatbot_message=test["chatbot_message"], user_message=test["user_message"]
)

dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

# response_turboI = get_response_to_single_message_input(prompt=prompt_completed)
response = f_get_response(prompt_completed)
print_wrap(response)

# %% STATISTICS
n_exp = 10
responses = pd.DataFrame(
    [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
    columns=["response"],
)
# %% ANALYZE
responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
responses = responses[["correct_judgement", "response"]]
responses["correct_judgement"].mean()
ci = calc_mean_with_confint(responses["correct_judgement"])
print(ci)
dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")


# %%

def run_experiment(
    get_response=f_get_response,
    n_exp=10,
    prompt_name="swift_judge_misc_disclaimers_only",
    test_case_name="can_intellegence_be_measured_with_disclaimer",
    should_reject=True,
):
    """Tests the

    model: gpt-35-turbo-16k or gpt-instruct."""
    prompt = load_local_prompt(prompt_name)
    test_cases = load_question_response_pairs()

    if should_reject:
        f_correct_answer = lambda answer: True if "ACCEPTED" not in answer else False
    else:
        f_correct_answer = lambda answer: True if "ACCEPTED" in answer else False

    test = test_cases[test_case_name]
    prompt_completed = prompt.format(
        chatbot_message=test["chatbot_message"], user_message=test["user_message"]
    )

    dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

    # Run trials
    responses = pd.DataFrame(
        [get_response(prompt=prompt_completed) for i in range(n_exp)],
        columns=["response"],
    )

    # Analyze information
    responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
    responses = responses[["correct_judgement", "response"]]
    responses["correct_judgement"].mean()
    ci = calc_mean_with_confint(responses["correct_judgement"])
    print(ci)

    # Dump results
    dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")


run_experiment(
    get_response=get_response_to_single_message_input,
    n_exp=10,
    prompt_name="swift_judge_misc_disclaimers_only",
    test_case_name="can_intellegence_be_measured_with_disclaimer",
    should_reject=False,
)

run_experiment(
    get_response=f_get_response,
    n_exp=10,
    prompt_name="swift_judge_misc_disclaimers_only",
    test_case_name="mirroring_body_language",
    should_reject=True,
)

run_experiment(
    get_response=get_response_to_single_message_input,
    n_exp=10,
    prompt_name="swift_judge_misc",
    test_case_name="mirroring_body_language",
    should_reject=True,
)

# %% **********
# %% **TEST 2**
# %% **********
# %% IQ-CLAIMS
# %% WARM UP
# create prompt
prompt_name = "swift_judge_misc_disclaimers_only"
prompt = load_local_prompt(prompt_name)
test_cases = load_question_response_pairs()
# run get_prompt_arguments(prompt) to see prompt-arguments
test_case_name = "can_intellegence_be_measured"
f_correct_answer = lambda answer: True if "ACCEPTED" not in answer else False
test = test_cases[test_case_name]
prompt_completed = prompt.format(
    chatbot_message=test["chatbot_message"], user_message=test["user_message"]
)

dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

response = get_response_to_single_message_input(prompt=prompt_completed)
response = f_get_response(prompt_completed)
print_wrap(response)

# %% STATISTICS
n_exp = 10
responses = pd.DataFrame(
    [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
    columns=["response"],
)
# %% ANALYZE
responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
responses = responses[["correct_judgement", "response"]]
responses["correct_judgement"].mean()
ci = calc_mean_with_confint(responses["correct_judgement"])
print(ci)
dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")


# %% **********
# %% **TEST 3**
# %% **********
# %% MIRRORING BODY LANGUAGE
# %% WARM UP
# create prompt
prompt_name = "swift_judge_misc_disclaimers_only"
prompt = load_local_prompt(prompt_name)
test_cases = load_question_response_pairs()
# run get_prompt_arguments(prompt) to see prompt-arguments
test_case_name = "mirroring_body_language"
f_correct_answer = lambda answer: True if "ACCEPTED" not in answer else False
test = test_cases[test_case_name]
prompt_completed = prompt.format(
    chatbot_message=test["chatbot_message"], user_message=test["user_message"]
)

dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

response = get_response_to_single_message_input(prompt=prompt_completed)
response_ti = f_get_response(prompt_completed)
print_wrap(response)

# %% STATISTICS
n_exp = 10
responses = pd.DataFrame(
    [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
    columns=["response"],
)
# %% ANALYZE
responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
responses = responses[["correct_judgement", "response"]]
responses["correct_judgement"].mean()
ci = calc_mean_with_confint(responses["correct_judgement"])
print(ci)
dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")
