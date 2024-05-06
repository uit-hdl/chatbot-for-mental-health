# %%
import path_setup

from utils_judging_judges import run_experiment_for_test_case
from utils_judging_judges import load_local_prompt_template
from utils_judging_judges import load_test_cases
from utils_judging_judges import gen_llm_response
from utils_judging_judges import get_source

# %%
prompt_name = "swift_judge_source_fidelity"
test_case_name = "how_to_communicate"

prompt = load_local_prompt_template(prompt_name)
test_cases = load_test_cases()
test_case = test_cases[test_case_name]

test_case["source"] = get_source(test_case["source_name"])
prompt_completed = prompt.format(**test_cases[test_case_name])

run_experiment_for_test_case(
    f_get_response=gen_llm_response,
    n_exp=10,
    prompt_name=prompt_name,
    test_case_name=test_case_name,
)
