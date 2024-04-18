"""Here I test how good GPT-turbo-instuct fact checker is for two different
bots/prompts: bot that returns summary of why it rejects vs bot that only
returns a numerical rating of source fidelity."""

# %%
import path_setup

from utils.console_chat_display import wrap_message
from utils.chat_utilities import get_response_to_single_message_input
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import load_yaml_file
from utils.backend import load_textfile_as_string
from utils.backend import get_source_content_and_path
from utils.backend import dump_to_json
from utils.backend import load_json_from_path

from functions import print_wrap
import os
from pprint import pprint
import pandas as pd
import time

# %% SETUP

# Dump paths
CWD = os.getcwd()

test_cases_path = os.path.join(CWD, "files/test_cases.yaml")
prompt_template0_path = os.path.join(CWD, "files/prompt-templates/version0.md")

test_cases = load_yaml_file(test_cases_path)
test_names = test_cases.keys()
prompt_template_v0 = load_textfile_as_string(prompt_template0_path)


def print_test_names():
    print(pd.DataFrame(test_cases.keys()))


def insert_variables_into_prompt(source, chatbot_message, prompt_template):
    return prompt_template.format(source=source, chatbot_message=chatbot_message)


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


def get_swift_judge_evaluation(test_case_id, prompt_template, temperature=0.5):
    """Gets the evaluation of the Turbo instruct model. Returns dictionary with
    c keys 'repsonse' and 'true_value'"""
    prompt = get_prompt(test_case_id=test_case_id, prompt_template=prompt_template)
    value = test_cases[test_case_id]["value"]
    return {
        "evaluation": get_response_to_single_message_input(
            prompt, temperature=temperature
        ),
        "true_value": value,
    }


def get_gpt35_turbo_judge_evaluation(test_case_id, prompt_template, temperature=0.5):
    """Gets the evaluation of GPT-3.5-turbo. Returns dictionary with
    keys 'repsonse' and 'true_value'"""
    prompt = get_prompt(test_case_id=test_case_id, prompt_template=prompt_template)
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


def run_experiment_comparing_models(
    test_name: str,
    prompt_template: str,
    results_turboInstruct: dict[dict],
    results_gpt35: dict[dict],
):
    """Gets the evaluation, true value, and time to generate response for turbo
    instruct and GPT-3.5 from a single experiment run."""

    # GPT-turbo instruct
    t1 = time.time()
    result_dict = get_swift_judge_evaluation(test_name, prompt_template)
    results_turboInstruct[test_name]["outcomes"].append(evaluate_decision(result_dict))
    results_turboInstruct[test_name]["responses"].append(result_dict["evaluation"])
    t2 = time.time()
    results_turboInstruct[test_name]["times"].append(t2 - t1)

    # GPT-3.5 turbo
    t1 = time.time()
    result_dict = get_gpt35_turbo_judge_evaluation(test_name, prompt_template)
    results_gpt35[test_name]["outcomes"].append(evaluate_decision(result_dict))
    results_gpt35[test_name]["responses"].append(result_dict["evaluation"])
    t2 = time.time()
    results_gpt35[test_name]["times"].append(t2 - t1)

    return results_turboInstruct, results_gpt35


# %% COMPARE GPT-3.5-Turbo to GPT-3.5-Turbo instruct
results_gpt35 = {
    name: {"times": [], "outcomes": [], "responses": []} for name in test_names
}
results_turboInstruct = {
    name: {"times": [], "outcomes": [], "responses": []} for name in test_names
}
test_name = "exercise_impOn_weight_mood_sleep"

n_exp_per_test = 5

for test_name in test_names:
    print(f"test: {test_name}")

    for i in range(n_exp_per_test):
        print(f"iteration {i}")
        results_turboInstruct, results_gpt35 = run_experiment_comparing_models(
            test_name=test_name,
            prompt_template=prompt_template_v0,
            results_turboInstruct=results_turboInstruct,
            results_gpt35=results_gpt35,
        )

result_dump_path = os.path.join(CWD, "results/instruct_vs_gpt35.json")
dump_to_json(
    {
        "results_turboInstruct": results_turboInstruct,
        "results_gpt35": results_gpt35,
    },
    os.path.join(CWD, "results/instruct_vs_gpt35.json"),
)


# %% ANALYSE RESULTS

if True == False:
    results = load_json_from_path(result_dump_path)
    results_turboInstruct = results["results_turboInstruct"]
    results_gpt35 = results["results_gpt35"]


def generate_dataframe(results_dict, test_name):
    """Collects data for the test-dictionary in a dataframe, which is more"""
    df = pd.DataFrame(
        {
            "time": results_dict[test_name]["times"],
            "evaluation": [x[0] for x in results_dict[test_name]["outcomes"]],
            "ground_truth": [x[1] for x in results_dict[test_name]["outcomes"]],
            "response": results_dict[test_name]["responses"],
        }
    )
    df["correct"] = df["evaluation"] == df["ground_truth"]
    # Missed offender here is the the same as a false negative
    df["missed_offender"] = (df["evaluation"] == False) & (df["ground_truth"] == True)
    df["falsely_accused"] = (df["evaluation"] == True) & (df["ground_truth"] == False)
    return df


def get_statistics_df(df, test_name):
    statistics_columns = ["correct", "missed_offender", "falsely_accused", "time"]
    df_statistics = pd.DataFrame(
        df[statistics_columns].mean().values * 100, columns=["mean"]
    )
    df_statistics.index = statistics_columns
    df_statistics["test_name"] = test_name
    df_statistics = pd.concat(
        [df_statistics[["test_name"]], df_statistics[["mean"]]], axis=1
    )

    return df_statistics


dfs_gpt35TI = {}
dfs_gpt35T = {}

statistics_gpt35TI = []
statistics_gpt35T = []


for test_name in test_names:
    dfs_gpt35TI[test_name] = generate_dataframe(results_turboInstruct, test_name)
    dfs_gpt35T[test_name] = generate_dataframe(results_gpt35, test_name)

    statistics_gpt35TI.append(get_statistics_df(dfs_gpt35TI[test_name], test_name))
    statistics_gpt35T.append(get_statistics_df(dfs_gpt35T[test_name], test_name))

statistics_gpt35TI

df_statistics_gpt35TI = pd.concat(statistics_gpt35TI).rename(
    columns={"mean": "mean_gpt35TI"}
)
df_statistics_gpt35T = pd.concat(statistics_gpt35T).rename(
    columns={"mean": "mean_gpt35T"}
)

df_statistics = pd.concat(
    [df_statistics_gpt35TI, df_statistics_gpt35T["mean_gpt35T"]], axis=1
)


df_statistics[df_statistics.index == "correct"]
df_statistics[df_statistics.index == "missed_offender"]
