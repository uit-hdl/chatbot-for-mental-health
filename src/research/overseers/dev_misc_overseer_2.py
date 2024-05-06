"""Here I develop and test the swift-judge for catching other the chatbot in
misc mode from acting unproffesionally or failing to refer."""

# %%
import path_setup

from utils_judging_judges import run_experiment_general
from utils_judging_judges import run_experiment_for_test_case
from utils_judging_judges import load_local_prompt_template
from utils_judging_judges import load_test_cases
from utils_judging_judges import gen_llm_response
from utils_judging_judges import get_source

# %% BASIC PIPELINE

prompt_path = "misc/swift_judge/unstable_user_and_role_limitation"
test_case_name = "laughing_to_make_ppl_like_me"

test_cases = load_test_cases()
test_case = test_cases[test_case_name]
prompt_variables = {
    "chatbot_message": test_case["chatbot_message"],
    "user_message": test_case["user_message"],
}

run_experiment_for_test_case(
    prompt_variables=prompt_variables,
    prompt_template_path_relative=prompt_path,
    test_case_name=test_case_name,
    n_exp=10,
)


# %% CHATBOT THINKS IT IS THERAPIST:
run_experiment_for_test_case(
    prompt_template_path_relative=prompt_path,
    test_case_name="chatbot_thinks_it_is_therapist",
    n_exp=10,
)

# %% CHATBOT GIVES AN OK ANSWER WITH DISCLAIMER:
result = run_experiment_for_test_case(
    prompt_template_path_relative=prompt_path,
    test_case_name="can_intelligence_be_measured_with_disclaimer",
    n_exp=5,
)
# %% CHATBOT THINKS IT IS THERAPIST:
run_experiment_for_test_case(
    prompt_template_path_relative=prompt_path,
    test_case_name="chatbot_queries_user_to_establish_relevance",
    n_exp=10,
)
# %% CHATBOT THINKS IT IS THERAPIST:
run_experiment_for_test_case(
    prompt_template_path_relative=prompt_path,
    test_case_name="chatbot_attemtps_to_assist_unstable_user",
    n_exp=20,
)

# 100% success at not rejecting 'can_intelligence_be_measured_with_disclaimer'
# 100% success at not rejecting 'can_intelligence_be_measured_with_disclaimer'
