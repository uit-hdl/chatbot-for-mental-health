# %%
import path_setup

from utils_testing_judges import run_experiment_for_test_case
from utils_testing_judges import run_experiment_general
from utils_testing_judges import load_local_prompt_template
from utils_testing_judges import load_test_cases
from utils_testing_judges import gen_llm_response
from utils_testing_judges import get_source
from utils_general import dump_to_json_locally
import matplotlib.pyplot as plt
import numpy as np

# %%
test_prompt_0 = False
test_prompt_1 = True
reset_experiment = False
if reset_experiment:
    results_0 = {}
    results_1 = {}

prompt_template_path_relative_0 = (
    "files/prompt-templates/source-fidelity/swift-judges/swift_judge_source_fidelity.md"
)
f_answer_is_rejected_0 = lambda answer: True if "REJECTED" in answer else False
f_answer_is_accepted_0 = lambda answer: not f_answer_is_rejected_0(answer)


prompt_template_path_relative_1 = "files/prompt-templates/source-fidelity/swift-judges/swift_judge_source_fidelity_chain_of_thought_v21.md"
f_answer_is_rejected_1 = lambda answer: True if "NOT_SUPPORTED" in answer else False
f_answer_is_accepted_1 = lambda answer: not f_answer_is_rejected_1(answer)

test_cases = [
    {"name": "exercise_impOn_weight_mood_sleep", "color": "green"},
    {"name": "alcohol_addictionRisk", "color": "green"},
    {"name": "correct_answer_on_effect_of_pa_on_symptoms", "color": "green"},
    {"name": "explaining_probabilities", "color": "green"},
    {"name": "correcting_ignorance", "color": "red"},
    {"name": "starting_a_movement", "color": "red"},
    {"name": "body_language_tips", "color": "red"},
    {"name": "bot_advices_how_to_start_conversations", "color": "red"},
]


test_cases = [
    {"name": "exercise_impOn_weight_mood_sleep", "color": "green"},
    {"name": "alcohol_addictionRisk", "color": "green"},
    {"name": "correct_answer_on_effect_of_pa_on_symptoms", "color": "green"},
    {"name": "explaining_probabilities", "color": "green"},
    {"name": "correcting_ignorance", "color": "red"},
    {"name": "starting_a_movement", "color": "red"},
    {"name": "body_language_tips", "color": "red"},
    {"name": "bot_advices_how_to_start_conversations", "color": "red"},
]
# %% exercise_impOn_weight_mood_sleep
test_case_name = "exercise_impOn_weight_mood_sleep"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_accepted_1,
    n_exp=10,
)

# %% alcohol_addictionRisk
test_case_name = "alcohol_addictionRisk"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_accepted_1,
    n_exp=10,
)
# %% correct_answer_on_effect_of_pa_on_symptoms
test_case_name = "correct_answer_on_effect_of_pa_on_symptoms"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_accepted_1,
    n_exp=10,
)
# %% explaining_probabilities
test_case_name = "explaining_probabilities"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_accepted_1,
    n_exp=10,
)
# %% correcting_ignorance
test_case_name = "correcting_ignorance"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_rejected_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_rejected_1,
    n_exp=15,
)

# %% starting_a_movement
test_case_name = "starting_a_movement"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_rejected_1,
    n_exp=10,
)
# %% body_language_tips
test_case_name = "body_language_tips"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_rejected_1,
    n_exp=10,
)
# %% bot_advices_how_to_start_conversations
test_case_name = "bot_advices_how_to_start_conversations"
if test_prompt_0:
    results_0[test_case_name] = run_experiment_for_test_case(
        test_case_name=test_case_name,
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_rejected_0,
        n_exp=10,
    )
results_1[test_case_name] = run_experiment_for_test_case(
    test_case_name=test_case_name,
    prompt_template_path_relative=prompt_template_path_relative_1,
    f_correct_response=f_answer_is_rejected_1,
    n_exp=10,
)


# %% COLLECT AND DUMP RESULTS

results = {"benchmark": results_0, "structured_reasoning": results_1}
dump_to_json_locally(
    results, "results/structured_reasoning_vs_benchmark_source_fidelity.json"
)

# %% PLOT RESULTS

succes_rate_0 = []
succes_rate_1 = []

for test_name in results_0:
    succes_rate_0.append(results_0[test_name]["ci_success_rate"]["mean"])
for test_name in results_1:
    succes_rate_1.append(results_1[test_name]["ci_success_rate"]["mean"])


x_values = np.arange(len(succes_rate_0))

plt.plot(x_values, succes_rate_0, "-s", markersize=10)
plt.plot(x_values, succes_rate_1, "-o")
plt.ylim([0, 1.1])
plt.legend(["Not using structured reasoning", "Using structured reasoning"])
plt.xlabel("Benchmark")

plt.xticks(
    ticks=x_values,  # Set the positions of the ticks
    labels=[test_case["name"] for test_case in test_cases],
    rotation=70,  # Rotate labels for better readability
)

# Define colors for each tick label
colors = [test_case["color"] for test_case in test_cases]

# Apply colors to tick labels
for label, color in zip(plt.gca().get_xticklabels(), colors):
    label.set_color(color)

plt.show()
