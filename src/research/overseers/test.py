# %%
import path_setup

from functions import run_experiment_for_test_case
from functions import load_local_prompt
from functions import load_test_cases
from functions import f_get_response_gpt35turbo
from functions import get_source

# %%
prompt_name = "swift_judge_source_fidelity"
test_case_name = "how_to_communicate"

prompt = load_local_prompt(prompt_name)
test_cases = load_test_cases()
test_case = test_cases[test_case_name]

test_case["source"] = get_source(test_case["source_name"])
prompt_completed = prompt.format(**test_cases[test_case_name])

run_experiment_for_test_case(
    f_get_response=f_get_response_gpt35turbo,
    n_exp=10,
    prompt_name=prompt_name,
    test_case_name=test_case_name,
)
# %%
from functions import run_experiment_general
from functions import f_get_response_gpt35turbo

prompt_name = "swift_judge_source_fidelity_v3"

test_case_name = "how_to_communicate"
test_case_name = "correct_answer_on_effect_of_pa_on_symptoms"
test_case_name = "alcohol_addictionRisk"
test_case_name = "diet_saturatedFats"

prompt = load_local_prompt(prompt_name)
test_cases = load_test_cases()
test_case = test_cases[test_case_name]

test_case["source"] = get_source(test_case["source_name"])
prompt_completed = prompt.format(**test_cases[test_case_name])


def f_response(prompt):
    return f_get_response_gpt35turbo(prompt, "test-chatbot")


results = run_experiment_general(
    prompt_variables=test_case,
    prompt_template_path_relative=prompt_name,
    # f_get_response=f_response,
    n_exp=10,
    f_correct_response=lambda answer: True if "ACCEPTED" not in answer else False,
)

