import path_setup

from functions import run_experiment
from functions import load_local_prompt
from functions import load_test_cases
from functions import f_get_response_gpt35turbo

prompt_name = "swift_judge_source_fidelity"
test_case_name = "how_to_start_conversation_about_ignorance"

# prompt = load_local_prompt(prompt_name)
# test_cases = load_test_cases()
# test_case = test_cases[test_case_name]

# test_case["source"] = get_source
# prompt_completed = prompt.format(**test_cases[test_case_name])

run_experiment(
    f_get_response=f_get_response_gpt35turbo,
    n_exp=10,
    prompt_name=prompt_name,
    test_case_name=test_case_name,
)
