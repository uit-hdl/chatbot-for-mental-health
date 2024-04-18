"""Here the goal is to determine which prompt is most effective at creating
effective fact-checkers."""

# %%
import path_setup

from utils.chat_utilities import get_response_to_single_message_input
from utils.chat_utilities import initiate_conversation_with_prompt
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import load_yaml_file
from utils.backend import load_textfile_as_string
from utils.backend import get_source_content_and_path
from utils.backend import dump_to_json
from utils.backend import load_json_from_path

from functions import print_wrap
from functions import print_test_names
import os
import pandas as pd
import time

# %% SETUP

# Dump paths
CWD = os.getcwd()


def load_test_cases():
    test_cases_path = os.path.join(CWD, "files/test_cases.yaml")
    return load_yaml_file(test_cases_path)


def load_question_response_pairs():
    """Loads examples with pairs of user questions and chatbot responses."""
    test_cases_path = os.path.join(CWD, "files/question_response_pairs.yaml")
    return load_yaml_file(test_cases_path)


def load_local_prompt(prompt_name):
    """Loads prompt from files/prompts/prompt_name"""
    return load_textfile_as_string(
        os.path.join(CWD, f"files/prompt-templates/{prompt_name}.md")
    )


prompt_template0_path = os.path.join(CWD, "files/prompt-templates/version0.md")
prompt_template1_path = os.path.join(CWD, "files/prompt-templates/version1.md")
prompt_template2_path = os.path.join(CWD, "files/prompt-templates/version2.md")
prompt_template_sentiment_analysis = load_textfile_as_string(
    os.path.join(CWD, "files/prompt-templates/sentiment_analysis.md")
)

test_names = [
    "diet_saturatedFats",
    "exercise_impOn_weight_mood_sleep",
    "starting_a_movement",
    "alcohol_addictionRisk",
    "exercies_frameOfMind_sleep",
]
prompt_template0 = load_textfile_as_string(prompt_template0_path)
prompt_template1 = load_textfile_as_string(prompt_template1_path)
prompt_template2 = load_textfile_as_string(prompt_template1_path)

test_cases = load_test_cases()
print_test_names(test_cases)


def insert_variables_into_prompt(source, chatbot_message, prompt_template):
    return prompt_template.format(source=source, chatbot_message=chatbot_message)


def get_source(source_name):
    return get_source_content_and_path(
        chatbot_id="mental_health",
        source_name=source_name,
    )[0]


def get_prompt(test_case_id, prompt_template, print_prompt=False):
    source = get_source(test_cases[test_case_id]["source_id"])
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


def run_experiment_comparing_prompts(
    test_name: str,
    prompt_template0: str,
    prompt_template1: str,
    results_prompt0: dict[dict],
    results_prompt1: dict[dict],
):
    """Gets the evaluation, true value, and time to generate response for turbo
    instruct and GPT-3.5 from a single experiment run."""

    # Prompt 0
    result_dict = get_swift_judge_evaluation(test_name, prompt_template0)
    results_prompt0[test_name]["outcomes"].append(evaluate_decision(result_dict))
    results_prompt0[test_name]["responses"].append(result_dict["evaluation"])

    # Prompt 1
    result_dict = get_swift_judge_evaluation(test_name, prompt_template1)
    results_prompt1[test_name]["outcomes"].append(evaluate_decision(result_dict))
    results_prompt1[test_name]["responses"].append(result_dict["evaluation"])

    return results_prompt0, results_prompt1


# %% SIMPLE TESTS
print_test_names(test_cases)
prompt_template = load_textfile_as_string(
    os.path.join(CWD, "files/prompt-templates/version2.md")
)
prompt_template_sentiment_analysis = load_textfile_as_string(
    os.path.join(CWD, "files/prompt-templates/sentiment_analysis.md")
)


# %% STARTING A SOCIAL MOVEMENT
prompt_template = load_local_prompt("version2")
prompt_template_rating = load_local_prompt("version2_rating_only")
test_case = load_test_cases()["starting_a_movement"]
source = get_source("13_stigma")
test_name = "starting_a_movement"

prompt = prompt_template.format(chatbot_message=test_case["bot_message"], source=source)
prompt_rate = prompt_template_rating.format(
    chatbot_message=test_case["bot_message"], source=source
)
print_wrap(prompt)

output = get_response_to_single_message_input(prompt)
output_rating_only = get_response_to_single_message_input(prompt_rate)


print("** ANSWER ** \n")
print_wrap(output)
print("\n** RATING ONLY ** \n")
print_wrap(output_rating_only)


# %% HOW TO TALK TO OTHERS ABOUT STIGMA AND MYTHS
prompt_template = load_local_prompt("version2")
test_case = load_test_cases()["how_to_communicate"]
source = get_source(test_case["source_id"])

prompt = prompt_template.format(
    chatbot_message=test_case["bot_message"],
    source=source,
)
print_wrap(f"** PROMPT ** \n\n{prompt}\n\n")
evaluation = get_response_to_single_message_input(
    prompt=prompt,
    max_tokens=400,
)

print("** ANSWER ** \n")
print_wrap(evaluation)

# %% SATURATED FATS
prompt_template = load_local_prompt("version2")

output = get_gpt35_turbo_judge_evaluation("diet_saturatedFats", prompt_template)

print("** ANSWER ** \n")
print_wrap(output["evaluation"])
print("\n** SENTIMENT ANALYSIS ** \n")

# %% EXERCISE DIRECT QUOTE
prompt_template = load_local_prompt("version2")

output = get_gpt35_turbo_judge_evaluation("exercise_quote", prompt_template)


print("** ANSWER ** \n")
print_wrap(output["evaluation"])

# %% EXERCISE EFFECT ON SYMPTOMS
test_cases = load_test_cases()
prompt_template = load_local_prompt("version2")

output = get_gpt35_turbo_judge_evaluation(
    "correct_answer_on_effect_of_pa_on_symptoms", prompt_template
)

print("** ANSWER ** \n")
print_wrap(output["evaluation"])

# %% RESPONSE RELEVANCE ANALYSIS
prompt_template = load_local_prompt("relevance_checker")
test_case = load_question_response_pairs()["stigma_long_answer"]

prompt = prompt_template.format(
    chatbot_message=test_case["bot_message"],
    user_question=test_case["user_question"],
)
print_wrap(f"** PROMPT ** \n\n{prompt}\n\n")
evaluation = get_response_to_single_message_input(
    prompt=prompt,
)

print("** ANSWER ** \n")
print_wrap(evaluation)

# %% COMPARE GPT-3.5-Turbo to GPT-3.5-Turbo instruct
results_prompt0 = {
    name: {"times": [], "outcomes": [], "responses": []} for name in test_names
}
results_prompt1 = {
    name: {"times": [], "outcomes": [], "responses": []} for name in test_names
}
test_name = "exercise_impOn_weight_mood_sleep"

n_exp_per_test = 10

for test_name in test_names:
    print(f"test: {test_name}")

    for i in range(n_exp_per_test):
        print(f"iteration {i}")
        results_prompt0, results_prompt1 = run_experiment_comparing_prompts(
            test_name=test_name,
            prompt_template0=prompt_template0,
            prompt_template1=prompt_template1,
            results_prompt0=results_prompt0,
            results_prompt1=results_prompt1,
        )

result_dump_path = os.path.join(CWD, "results/instruct_vs_gpt35.json")

if True == False:
    dump_to_json(
        {
            "results_prompt0": results_prompt0,
            "results_prompt1": results_prompt1,
        },
        os.path.join(CWD, "results/promptv0_vs_promptv1.json"),
    )


# %% ANALYSE RESULTS

if True == False:
    results = load_json_from_path(result_dump_path)
    results_turboInstruct = results["results_version0"]
    results_gpt35 = results["results_version1"]


def generate_dataframe(results_dict, test_name):
    """Collects data for the test-dictionary in a dataframe, which is more"""
    df = pd.DataFrame(
        {
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
    statistics_columns = ["correct", "missed_offender", "falsely_accused"]
    df_statistics = pd.DataFrame(
        df[statistics_columns].mean().values * 100, columns=["mean"]
    )
    df_statistics.index = statistics_columns
    df_statistics["test_name"] = test_name
    df_statistics = pd.concat(
        [df_statistics[["test_name"]], df_statistics[["mean"]]], axis=1
    )

    return df_statistics


dfs_version0 = {}
dfs_version1 = {}

statistics_version0 = []
statistics_version1 = []


for test_name in test_names:
    dfs_version0[test_name] = generate_dataframe(results_turboInstruct, test_name)
    dfs_version1[test_name] = generate_dataframe(results_gpt35, test_name)

    statistics_version0.append(get_statistics_df(dfs_version0[test_name], test_name))
    statistics_version1.append(get_statistics_df(dfs_version1[test_name], test_name))

statistics_version0

df_statistics_version0 = pd.concat(statistics_version0).rename(
    columns={"mean": "mean_version0"}
)
df_statistics_version1 = pd.concat(statistics_version1).rename(
    columns={"mean": "mean_version1"}
)

df_statistics = pd.concat(
    [df_statistics_version0, df_statistics_version1["mean_version1"]], axis=1
)


df_statistics[df_statistics.index == "correct"]
df_statistics[df_statistics.index == "missed_offender"]
