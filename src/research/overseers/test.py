import path_setup

from functions import run_experiment
from functions import load_local_prompt
from functions import load_test_cases
from functions import f_get_response_gpt35turbo

prompt_name = "swift_judge_source_fidelity_v1"
test_case_name = "starting_a_movement"

prompt = load_local_prompt(prompt_name)
test_cases = load_test_cases()
test_cases[test_case_name]

prompt_completed = prompt.format(**test_cases[test_case_name])

run_experiment(
    f_get_response=f_get_response_gpt35turbo,
    n_exp=3,
    prompt_name="swift_judge_misc_disclaimers_only",
    test_case_name="can_intelligence_be_measured_with_disclaimer",
)
