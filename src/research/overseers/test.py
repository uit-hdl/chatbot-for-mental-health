# %%
import path_setup

from utils_testing_judges import run_experiment_for_test_case
from utils_testing_judges import load_local_prompt_template
from utils_testing_judges import load_test_cases
from utils_testing_judges import gen_llm_response
from utils_testing_judges import get_source
from utils_testing_judges import dump_to_json_locally

from utils.backend import add_extension

# %%
prompt_name = "source-fidelity/swift_judge_source_fidelity"
test_case_name = "what_is_stigma_good_answer"
test_case_name = "starting_a_movement"

prompt = load_local_prompt_template(prompt_name)
test_cases = load_test_cases()
test_case = test_cases[test_case_name]

test_case["source"] = get_source(test_case["source_name"])
prompt_completed = prompt.format(**test_cases[test_case_name])


prompt_name = "misc/swift_judge/disclaimers_only.md"
results_1 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="chatbot_thinks_its_expert_on_jokes",
)

prompt_name = "misc/swift_judge/disclaimers_only.md"
results_1 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="chatbot_thinks_its_expert_on_jokes",
)

# %%
prompt_name = "source-fidelity/swift_judge_source_fidelity"
results_1 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="humor_to_challenge_stigma",
)

results_1 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="what_is_stigma_good_answer",
)

results_2 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="causes_of_schizo",
)

results_3 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="starting_a_movement",
)

results_4 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="how_to_start_conversation_about_ignorance",
)

results_5 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="diet_saturatedFats",
)

results_6 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="body_language_tips",
)

results_7 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="explaining_probabilities",
)

# %%
prompt_name = "source-fidelity/swift_judge_source_fidelity_chain_of_thought"
n_exp = 5
results_1 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="what_is_stigma_good_answer",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
    summarize_source=True
)

results_1 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="stigma_long_irrelevant_answer",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
)

results_2 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="causes_of_schizo",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
)

results_3 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="starting_a_movement",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_4 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="how_to_start_conversation_about_ignorance",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_5 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="diet_saturatedFats",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_6 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="body_language_tips",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_7 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="explaining_probabilities",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
)

# %%
prompt_name = "other/is_question_answerable"
results_7 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="explaining_probabilities",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
)

results_7 = run_experiment_for_test_case(
    n_exp=10,
    prompt_template_path_relative=prompt_name,
    test_case_name="body_language_tips",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_4 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="how_to_start_conversation_about_ignorance",
    f_correct_response=lambda x: True if "REFRAIN" in x else False,
)

results_1 = run_experiment_for_test_case(
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name="what_is_stigma_good_answer",
    f_correct_response=lambda x: True if "ATTEMPT" in x else False,
)