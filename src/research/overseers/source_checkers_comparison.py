# %%
import path_setup

from utils_testing_judges import run_experiment_for_test_case
from utils_testing_judges import run_experiment_general
from utils_testing_judges import load_local_prompt_template
from utils_testing_judges import load_test_cases
from utils_testing_judges import gen_llm_response
from utils_testing_judges import get_source
from utils_general import dump_to_json_locally

results_0 = []
results_1 = []
# %%
prompt_template_path_relative_0 = (
    "files/prompt-templates/source-fidelity/swift-judges/swift_judge_source_fidelity.md"
)
f_answer_is_rejected_0 = lambda answer: True if "REJECTED" in answer else False
f_answer_is_accepted_0 = lambda answer: not f_answer_is_rejected_0(answer)


prompt_template_path_relative_1 = "files/prompt-templates/source-fidelity/swift-judges/swift_judge_source_fidelity_chain_of_thought_v1.md"
f_answer_is_rejected_1 = lambda answer: True if "NOT_SUPPORTED" in answer else False
f_answer_is_accepted_1 = lambda answer: not f_answer_is_rejected_1(answer)

# %% IMPACT OF EXERCISE ON MOOD, SLEEP, AND WEIGHT
results_0.append(
    run_experiment_for_test_case(
        test_case_name="exercise_impOn_weight_mood_sleep",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="exercise_impOn_weight_mood_sleep",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_accepted_1,
        n_exp=10,
    )
)
# %% IMPACT OF EXERCISE WEIGHT 
results_0.append(
    run_experiment_for_test_case(
        test_case_name="alcohol_addictionRisk",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="alcohol_addictionRisk",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_accepted_1,
        n_exp=10,
    )
)
# %% LONG ANSWER ON EFFECTS OF EXERCISE ON SYMPTOMS
results_0.append(
    run_experiment_for_test_case(
        test_case_name="correct_answer_on_effect_of_pa_on_symptoms",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="correct_answer_on_effect_of_pa_on_symptoms",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_accepted_1,
        n_exp=10,
    )
)
# %% RAISING AWARENESS
results_0.append(
    run_experiment_for_test_case(
        test_case_name="raising_awareness",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="raising_awareness",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_accepted_1,
        n_exp=10,
    )
)
# %% CORRECTING IGNORANCE
results_0.append(
    run_experiment_for_test_case(
        test_case_name="correcting_ignorance",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_rejected_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="correcting_ignorance",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_rejected_1,
        n_exp=10,
    )
)

# %% STARTING A MOVEMENT
results_0.append(
    run_experiment_for_test_case(
        test_case_name="starting_a_movement",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_rejected_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="starting_a_movement",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_rejected_1,
        n_exp=10,
    )
)
# %% STARTING A MOVEMENT
results_0.append(
    run_experiment_for_test_case(
        test_case_name="body_language_tips",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_rejected_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="body_language_tips",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_rejected_1,
        n_exp=10,
    )
)

# %% STARTING A MOVEMENT
results_0.append(
    run_experiment_for_test_case(
        test_case_name="explaining_probabilities",
        prompt_template_path_relative=prompt_template_path_relative_0,
        f_correct_response=f_answer_is_accepted_0,
        n_exp=10,
    )
)
results_1.append(
    run_experiment_for_test_case(
        test_case_name="explaining_probabilities",
        prompt_template_path_relative=prompt_template_path_relative_1,
        f_correct_response=f_answer_is_accepted_1,
        n_exp=10,
    )
)

# %% COLLECT AND DUMP RESULTS

results = {"benchmark": results_0, "structured_reasoning": results_1}
dump_to_json_locally(
    results, "results/structured_reasoning_vs_benchmark_source_fidelity.json"
)

# %%

succes_rate_0 = []
succes_rate_1 = []

for result_0, result_1 in zip(results_0, results_1):
    succes_rate_0.append(result_0["ci_success_rate"]["mean"])
    succes_rate_1.append(result_1["ci_success_rate"]["mean"])


import matplotlib.pyplot as plt
import numpy as np

x_values = np.arange(len(succes_rate_0))

plt.plot(x_values, succes_rate_0, "-s", markersize=10)
plt.plot(x_values, succes_rate_1, "-o")
plt.ylim([0, 1.1])
plt.legend(["Not using structured reasoning", "Using structured reasoning"])
plt.xlabel("Benchmark")
# plt.xticks(
#     ticks=x_values,  # Set the positions of the ticks
#     labels=[
#         "bot_advice_sarcasm_and_bad_jokes",  # red
#         "chatbot_thinks_its_expert_on_jokes",  # red
#         "can_intelligence_be_measured",  # red
#         "chatbot_queries_for_clarification",  # green
#         "chatbot_offers_referral",  # green
#         "chatbot_helps_user_formulate_thoughts",  # green
#         "chatbot_explains_its_functionalities",  # green
#     ],
#     rotation=70,  # Rotate labels for better readability
# )

# # Define colors for each tick label
# colors = ["red", "red", "red", "green", "green", "green", "green"]

# # Apply colors to tick labels
# for label, color in zip(plt.gca().get_xticklabels(), colors):
#     label.set_color(color)

# plt.show()
