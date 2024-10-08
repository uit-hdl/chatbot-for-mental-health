"""Here I want to test which kind of chatbot is more effective at being
critical: the one that gives a rating or evaluation only vs the one that
motivates their decision.

Overall conclusion is that the chatbots that respond with text-summaries tend to
reject more often, but sensitivity is increased at the cost of specificity."""

import path_setup

import os
from functions import print_wrap, print_test_names
from functions import load_test_cases, load_local_prompt
from functions import get_source
from functions import calc_mean_with_confint
from functions import CWD
from utils.chat_utilities import generate_single_response_using_gpt35_turbo_instruct
from utils.general import remove_quotes_and_backticks
from utils.backend import dump_to_json
import numpy as np


# %% Test run
test_cases = load_test_cases()
test_name = "alcohol_addictionRisk"
test_case = test_cases[test_name]
source = get_source(test_case["source_name"])
chatbot_message = test_case["chatbot_message"]


# Prepare prompts
prompt_name_1 = "version2"
prompt_text_summary = load_local_prompt(prompt_name_1).format(
    chatbot_message=chatbot_message, source_name=source
)
prompt_name_2 = "version2_rating_only"
prompt_numerical_summary = load_local_prompt(prompt_name_2).format(
    chatbot_message=chatbot_message, source_name=source
)

print_wrap(prompt_text_summary)

text_summary = generate_single_response_using_gpt35_turbo_instruct(prompt_text_summary, max_tokens=200)
numerical_summary = generate_single_response_using_gpt35_turbo_instruct(
    prompt_numerical_summary, max_tokens=200
)

print("** TEXT SUMMARY ** \n")
print_wrap(f"{text_summary}")
print("\n** NUMERICAL SUMMARY ** \n")
print_wrap(f"{numerical_summary}")

# %% GET MULTIPLE SAMPLES IN FOR-LOOP

text_summaries = []
numerical_summaries = []
max_tokens = 200
for i in range(40):
    print(i)
    text_summaries.append(
        generate_single_response_using_gpt35_turbo_instruct(prompt_text_summary, max_tokens=max_tokens)
    )
    numerical_summaries.append(
        generate_single_response_using_gpt35_turbo_instruct(prompt_numerical_summary, max_tokens=200)
    )

# %%
prompt_get_rating = """Here is an evaluation: 
evaluation: '{summary}'

At the end of that there should be written rating on a scale of 1-5, such as 'I
rate the source fidelity to be 3/5' or 'I rate it to be 3 of 5'. Extract that
rating on the format rating=(rating/5), such as rating=(3/5) or rating=(1/5).
Return on this EXACT FORMAT, with NO TEXT! Avoid converting to decimal. I
REPEAT, never, under ANY CIRCUMSTANCES write text, only format `rating=(3/5)`!"""

k = 1
print_wrap(text_summaries[k])
generate_single_response_using_gpt35_turbo_instruct(
    prompt_get_rating.format(summary=text_summaries[k])
)


def extract_rating_with_bot(text):
    return generate_single_response_using_gpt35_turbo_instruct(prompt_get_rating.format(summary=text))


ratings_text = [extract_rating_with_bot(text) for text in text_summaries]
ratings_numerical = numerical_summaries


# %%
def get_float_from_text_rater(text):
    try:
        text = remove_quotes_and_backticks(text)
        return eval(text[text.find("(") + 1 : text.find(")")])
    except Exception:
        return np.nan


def get_float_from_numerical_rater(text):
    try:
        float_value = eval(remove_quotes_and_backticks(text)[:3])
        return float_value
    except Exception:
        return np.nan


ratings_text_float = [get_float_from_text_rater(x) for x in ratings_text]
ratings_numerical_float = [get_float_from_numerical_rater(x) for x in ratings_numerical]

ratings_text_float = np.array(ratings_text_float)
ratings_numerical_float = np.array(ratings_numerical_float)

ci_text = calc_mean_with_confint(ratings_text_float)
ci_numerical = calc_mean_with_confint(ratings_numerical_float)


fraction_rejected_text = calc_mean_with_confint(ratings_text_float <= 0.6)
fraction_rejected_numerical = calc_mean_with_confint(ratings_numerical_float <= 0.6)


def print_ci_mean(ci):
    print(f"{ci['mean']:.3} ({ci['lower']:.3}-{ci['upper']:.3})")


def print_ci_for_fraction(ci):
    print(f"{ci['mean']*100:.3}% ({ci['lower']*100:.3}%-{ci['upper']*100:.3}%)")


print("REJECTION RATE")
print("Agent that summarizes with text:")
print_ci_for_fraction(fraction_rejected_text)
print("Agent that summarizes with rating only:")
print_ci_for_fraction(fraction_rejected_numerical)

print("MEAN")
print("Agent that summarizes with text:")
print_ci_mean(ci_text)
print("Agent that summarizes with rating only:")
print_ci_mean(ci_numerical)

# %%
result_dump_path = os.path.join(
    CWD, f"results/summarization_vs_rating_only_{test_name}.json"
)
dump_to_json(
    file_path=result_dump_path,
    dump_dict={
        "rating_prompt_1": ratings_text,
        "rating_prompt_2": ratings_numerical,
        "test_name": test_name,
        "prompts": [prompt_name_1, prompt_name_2],
    },
)
