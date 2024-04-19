# %%
import path_setup

from functions import load_question_response_pairs
from functions import load_local_prompt
from functions import load_test_cases
from functions import get_source
from functions import get_prompt_arguments
from functions import print_wrap
from functions import dump_prompt_to_markdown
from functions import calc_mean_with_confint
from functions import dump_to_json_locally
from functions import f_get_response
from utils.chat_utilities import get_response_to_single_message_input

import numpy as np
import pandas as pd

# %% IQ-CLAIMS WITH DISCLAIMER
# %% WARM UP
# create prompt
prompt_name = "swift_judge_source_fidelity_v1"
prompt = load_local_prompt(prompt_name)
test_cases = load_test_cases()

# run get_prompt_arguments(prompt) to see prompt-arguments
test_case_name = "alcohol_addictionRisk"
f_correct_answer = lambda answer: True if "ACCEPTED" in answer else False
test = test_cases[test_case_name]
prompt_completed = prompt.format(
    chatbot_message=test["chatbot_message"], source_name=get_source(test["source_name"])
)
dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

# response_turboI = get_response_to_single_message_input(prompt=prompt_completed)
response = f_get_response(prompt_completed)
print_wrap(response)

# %% STATISTICS
n_exp = 10
responses = pd.DataFrame(
    [f_get_response(prompt=prompt_completed) for i in range(n_exp)],
    columns=["response"],
)
# %% ANALYZE
responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
responses = responses[["correct_judgement", "response"]]
responses["correct_judgement"].mean()
ci = calc_mean_with_confint(responses["correct_judgement"])
print(ci)
dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")


# %%
def run_experiment(
    get_response=f_get_response,
    n_exp=10,
    prompt_name="swift_judge_source_fidelity_v1",
    test_case_name="can_intellegence_be_measured_with_disclaimer",
    should_accept=False,
):
    """Tests the

    model: gpt-35-turbo-16k or gpt-instruct."""
    prompt = load_local_prompt(prompt_name)
    test_cases = load_test_cases()
    if should_accept:
        f_correct_answer = lambda answer: True if "ACCEPTED" in answer else False
    else:
        f_correct_answer = lambda answer: True if "ACCEPTED" not in answer else False

    test = test_cases[test_case_name]
    prompt_completed = prompt.format(
        chatbot_message=test["chatbot_message"], source_name=get_source(test["source_name"])
    )

    dump_prompt_to_markdown(prompt_completed, "files/prompt-completed/prompt_completed.md")

    # Run trials
    responses = pd.DataFrame(
        [get_response(prompt=prompt_completed) for i in range(n_exp)],
        columns=["response"],
    )

    # Analyze information
    responses["correct_judgement"] = responses["response"].apply(f_correct_answer)
    responses = responses[["correct_judgement", "response"]]
    responses["correct_judgement"].mean()
    ci = calc_mean_with_confint(responses["correct_judgement"])
    print(f"\n** Results for case {test_case_name} ** ")
    print(f"prompt: {prompt_name} & model: {f_get_response}")
    print(ci)
    # Dump results
    dump_to_json_locally(ci, f"results/{prompt_name}/{test_case_name}.json")

    return ci


# %%
run_experiment(
    get_response=get_response_to_single_message_input,
    n_exp=2,
    prompt_name="swift_judge_source_fidelity_v1",
    test_case_name="starting_a_movement",
    should_accept=False,
)

# %% TURBO-INSTRUCT + ORIGINAL SOURCE FIDELITY PROMPT
CIs_gpt35_16k = {}
n_exp = 20
prompt_name = "swift_judge_source_fidelity"
model = f_get_response
# SHOULD ACCEPT
CIs_gpt35_16k["causes_of_schizo"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="causes_of_schizo",
    should_accept=True,
)
CIs_gpt35_16k["alcohol_addictionRisk"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="alcohol_addictionRisk",
    should_accept=True,
)
CIs_gpt35_16k["exercies_frameOfMind_sleep"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="exercies_frameOfMind_sleep",
    should_accept=True,
)
# SHOULD REJECT
CIs_gpt35_16k["starting_a_movement"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="starting_a_movement",
    should_accept=False,
)
CIs_gpt35_16k["how_to_communicate"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="how_to_communicate",
    should_accept=False,
)
CIs_gpt35_16k["diet_saturatedFats"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="diet_saturatedFats",
    should_accept=False,
)
average_success_rate = np.mean([value["mean"] for value in CIs_gpt35_16k.values()])
print(average_success_rate)

# %% TURBO-INSTRUCT + ORIGINAL SOURCE FIDELITY PROMPT
CIs_instruct = {}
n_exp = 20
prompt_name = "swift_judge_source_fidelity"
model = get_response_to_single_message_input
# SHOULD ACCEPT
CIs_instruct["causes_of_schizo"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="causes_of_schizo",
    should_accept=True,
)
CIs_instruct["alcohol_addictionRisk"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="alcohol_addictionRisk",
    should_accept=True,
)
CIs_instruct["exercies_frameOfMind_sleep"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="exercies_frameOfMind_sleep",
    should_accept=True,
)
# SHOULD REJECT
CIs_instruct["starting_a_movement"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="starting_a_movement",
    should_accept=False,
)
CIs_instruct["how_to_communicate"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="how_to_communicate",
    should_accept=False,
)
CIs_instruct["diet_saturatedFats"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="diet_saturatedFats",
    should_accept=False,
)


accuracy_rates = np.array([value["mean"] for value in CIs_instruct.values()])
average_success_rate_good_messages = accuracy_rates[:3].mean()
average_success_rate_bad_messages = accuracy_rates[3:].mean()
print(f"On all messages {accuracy_rates.mean():.3}")
print(f"On good messages {average_success_rate_good_messages:.3}")
print(f"On bad messages {average_success_rate_bad_messages:.3}")

# %% CONCLUSION: 52.5% SR (Instruct) VS 78.3% SR (3.5-16k)
# %% TURBO-INSTRUCT + ORIGINAL SOURCE FIDELITY PROMPT
CIs_gpt35_16k = {}
n_exp = 20
prompt_name = "swift_judge_source_fidelity"
model = f_get_response
# SHOULD ACCEPT
CIs_gpt35_16k["causes_of_schizo"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="causes_of_schizo",
    should_accept=True,
)
CIs_gpt35_16k["alcohol_addictionRisk"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="alcohol_addictionRisk",
    should_accept=True,
)
CIs_gpt35_16k["exercies_frameOfMind_sleep"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="exercies_frameOfMind_sleep",
    should_accept=True,
)
# SHOULD REJECT
CIs_gpt35_16k["starting_a_movement"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="starting_a_movement",
    should_accept=False,
)
CIs_gpt35_16k["how_to_communicate"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="how_to_communicate",
    should_accept=False,
)
CIs_gpt35_16k["diet_saturatedFats"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="diet_saturatedFats",
    should_accept=False,
)


accuracy_rates = np.array([value["mean"] for value in CIs_gpt35_16k.values()])
average_success_rate_good_messages = accuracy_rates[:3].mean()
average_success_rate_bad_messages = accuracy_rates[3:].mean()
print(f"On all messages {accuracy_rates.mean():.3}")
print(f"On good messages {average_success_rate_good_messages:.3}")
print(f"On bad messages {average_success_rate_bad_messages:.3}")


# %% TURBO-INSTRUCT + MODIFIED SOURCE FIDELITY PROMPT
CIs_gpt35_16k = {}
n_exp = 20
prompt_name = "swift_judge_source_fidelity_v1"
model = f_get_response
# SHOULD ACCEPT
CIs_gpt35_16k["causes_of_schizo"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="causes_of_schizo",
    should_accept=True,
)
CIs_gpt35_16k["alcohol_addictionRisk"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="alcohol_addictionRisk",
    should_accept=True,
)
CIs_gpt35_16k["exercies_frameOfMind_sleep"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="exercies_frameOfMind_sleep",
    should_accept=True,
)
# SHOULD REJECT
CIs_gpt35_16k["starting_a_movement"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="starting_a_movement",
    should_accept=False,
)
CIs_gpt35_16k["how_to_communicate"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="how_to_communicate",
    should_accept=False,
)
CIs_gpt35_16k["diet_saturatedFats"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="diet_saturatedFats",
    should_accept=False,
)


accuracy_rates = np.array([value["mean"] for value in CIs_gpt35_16k.values()])
average_success_rate_good_messages = accuracy_rates[:3].mean()
average_success_rate_bad_messages = accuracy_rates[3:].mean()
print(f"On all messages {accuracy_rates.mean():.3}")
print(f"On good messages {average_success_rate_good_messages:.3}")
print(f"On bad messages {average_success_rate_bad_messages:.3}")


# %% TURBO-INSTRUCT + MODIFIED SOURCE FIDELITY PROMPT
CIs_gpt35_16k = {}
n_exp = 20
prompt_name = "swift_judge_source_fidelity_v1"
model = get_response_to_single_message_input
# SHOULD ACCEPT
CIs_gpt35_16k["causes_of_schizo"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="causes_of_schizo",
    should_accept=True,
)
CIs_gpt35_16k["alcohol_addictionRisk"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="alcohol_addictionRisk",
    should_accept=True,
)
CIs_gpt35_16k["exercies_frameOfMind_sleep"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="exercies_frameOfMind_sleep",
    should_accept=True,
)
# SHOULD REJECT
CIs_gpt35_16k["starting_a_movement"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="starting_a_movement",
    should_accept=False,
)
CIs_gpt35_16k["how_to_communicate"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="how_to_communicate",
    should_accept=False,
)
CIs_gpt35_16k["diet_saturatedFats"] = run_experiment(
    get_response=model,
    n_exp=n_exp,
    prompt_name=prompt_name,
    test_case_name="diet_saturatedFats",
    should_accept=False,
)


accuracy_rates = np.array([value["mean"] for value in CIs_gpt35_16k.values()])
average_success_rate_good_messages = accuracy_rates[:3].mean()
average_success_rate_bad_messages = accuracy_rates[3:].mean()
print(f"On all messages {accuracy_rates.mean():.3}")
print(f"On good messages {average_success_rate_good_messages:.3}")
print(f"On bad messages {average_success_rate_bad_messages:.3}")