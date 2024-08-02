"""Here I test the effect of summarizing a source before inserting it into the
prompt of the fact-checjer. The conclusion is that it makes the fact-checker
overall more likely to reject; higher sensitivity at the cost of lower
specificity.

In general, this failed. I simply get higher false rejection rates.
"""

import path_setup

from functions import load_test_cases
from functions import load_local_prompt
from functions import get_source
from functions import get_prompt_arguments
from functions import print_wrap
from functions import dump_prompt_to_markdown
from functions import calc_mean_with_confint
from functions import load_summarized_source
from functions import dump_to_json_locally
from utils.chat_utilities import generate_single_response_using_gpt35_turbo_instruct

import numpy as np
import pandas as pd

# %% WARM UP
# create prompt
prompt = load_local_prompt("swift_judge_source_fidelity")
test_cases = load_test_cases()
# run get_prompt_arguments(prompt) to see prompt-arguments

test = test_cases["alcohol_addictionRisk"]
prompt_completed = prompt.format(
    chatbot_message=test["chatbot_message"], source_name=get_source(test["source_name"])
)

dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

generate_single_response_using_gpt35_turbo_instruct(prompt=prompt_completed)


# %% STATISTICS
def get_prompt(test_name, prompt_template):
    test = test_cases[test_name]
    return prompt_template.format(
        chatbot_message=test["chatbot_message"], source_name=get_source(test["source_name"])
    )


def get_evaluation(test_name, prompt):
    ground_truth = test_cases[test_name]["correct_verdict"]
    response = generate_single_response_using_gpt35_turbo_instruct(prompt=prompt)
    if "ACCEPTED" in response:
        return "ACCEPTED", ground_truth, response
    else:
        return "REJECTED", ground_truth, response


# %% SOURCE SUMMARIZER

test_name = "correct_answer_on_effect_of_pa_on_symptoms"
source_id = test_cases[test_name]["source_name"]
source = get_source(source_id)
prompt_completed = load_local_prompt("source_summarizer").format(source_name=source)
source_summarized = generate_single_response_using_gpt35_turbo_instruct(
    prompt=prompt_completed, max_tokens=400
)
print_wrap(source_summarized)

if 0 == 1:
    dump_prompt_to_markdown(
        source_summarized, f"files/sources-summarized/{source_id}.md"
    )

# %% PREPARE EXPERIMENT
test_case = test_cases[test_name]
chatbot_message = test_case["chatbot_message"]
source = get_source(test_case["source_name"])
source_summarized = load_summarized_source(test_case["source_name"])

prompt_template_v0 = load_local_prompt("swift_judge_source_fidelity")
prompt_template_v1 = load_local_prompt("swift_judge_source_fidelity_v1")

# Insert parameters into prompt templates
prompt_v0 = prompt_template_v0.format(
    chatbot_message=chatbot_message, source_name=source
)
prompt_v1 = prompt_template_v1.format(
    chatbot_message=chatbot_message, source_name=source_summarized
)
print_wrap(prompt_v0)
n_trials = 40

# %% V0
results_v0 = []
for i in range(n_trials):
    print(i)
    results_v0.append(get_evaluation(test_name, prompt_v0))

# %% V1
results_v1 = []
for i in range(n_trials):
    print(i)
    results_v1.append(get_evaluation(test_name, prompt_v1))
    # results_v1.append(get_evaluation(test_name, prompt_v1))

# %% PROCESS & ANALYSE
df_0 = pd.DataFrame(results_v0, columns=["evaluation", "truth", "response"])
df_1 = pd.DataFrame(results_v1, columns=["evaluation", "truth", "response"])
df_0["evaluation"] == df_0["truth"]


def get_accuracy_with_ci(df):
    return calc_mean_with_confint(df["evaluation"] == df["truth"], scaler=100)


calc_mean_with_confint(df_0["evaluation"] == df_0["truth"])
ci_acc_v0 = get_accuracy_with_ci(df_0)
ci_acc_v1 = get_accuracy_with_ci(df_1)

print(f"RESULTS")
print(f"V0: {ci_acc_v0}")
print(f"V1: {ci_acc_v1}")

# %% DUMP RESULTS
description = """I tested if the chatbot that receives a summarized version of
the source produces false positives. It definately does..."""
results = [
    ci_acc_v0,
    ci_acc_v1,
    {"description": description},
]
# About 30% accuracy for test `diet_saturatedFats`
dump_to_json_locally(
    filepath_relative="results/summarizing_source_exercise_before_eval.json", variable=results
)
