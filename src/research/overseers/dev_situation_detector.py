import path_setup
from utils_testing_judges import run_experiment_for_test_case


verdict_map = {"UNSUITABLE_FOR_AI": "REJECT", "SUPPORTED": "SUITABLE_FOR_AI"}

prompt_name = "files/prompt-templates/other/high_stakes_detector.md"

results_1 = run_experiment_for_test_case(
    n_exp=10,
    verdict_map=verdict_map,
    prompt_template_path_relative=prompt_name,
    test_case_name="bot_advices_how_to_start_conversations",
    # model="gpt-4",
)
