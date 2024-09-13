# %%
import path_setup

from utils_testing_judges import run_experiment_for_test_case


# %% Testing Judge that Fact checks
prompt_name = (
    "files/prompt-templates/source-fidelity/swift-judges/swift_judge_source_fidelity.md"
)

# Insert the name of a test case from files/test_cases.yaml
test_case_name = "diet_saturatedFats"
# Specify how many experiments you want to run
n_exp = 1
# verdict_map determines which of the verdicts of the judge get mapped to the
# decisions ACCEPT and REJECT. Note: the decision gets checked against the
# correct_verdict parameter for associated dictionary in test_cases.yaml
verdict_map = {"SUPPORTED": "ACCEPT", "UNSUPPORTED": "REJECT"}

# Select which LLM to use
model = "gpt-35-turbo-16k"

results_source_fidelity_test = run_experiment_for_test_case(
    model=model,
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name=test_case_name,
    verdict_map=verdict_map,
)


# %% Example of testing Default Mode Judge
prompt_name = (
    "files/prompt-templates/default/swift-judges/swift_judge_disclaimer_check.md"
)

# Insert the name of a test case from files/test_cases.yaml
test_case_name = "chatbot_thinks_its_expert_on_jokes"
# Specify how many experiments you want to run

n_exp = 1
# verdict_map determines which of the verdicts of the judge get mapped to the
# decisions ACCEPT and REJECT. Note: the decision gets checked against the
# correct_verdict parameter for associated dictionary in test_cases.yaml
verdict_map = {"AGREE": "ACCEPT", "DENY": "REJECT"}

# Select which LLM to use
model = "gpt-35-turbo-16k"

results_source_fidelity_test = run_experiment_for_test_case(
    model=model,
    n_exp=n_exp,
    prompt_template_path_relative=prompt_name,
    test_case_name=test_case_name,
    verdict_map=verdict_map,
)
