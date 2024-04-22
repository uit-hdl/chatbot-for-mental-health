"""Script for testing response from prompted AI agent."""

# %%
import path_setup

from functions import print_wrap
from functions import run_experiment_for_test_case
from functions import load_local_prompt
from functions import load_test_cases
from functions import f_get_response_gpt35turbo
from functions import complete_prompt_and_get_response

# %%
# prompt_name = "swift_judge_source_fidelity_v1"
# test_case_name = "starting_a_movement"

# prompt = load_local_prompt(prompt_name)
# test_cases = load_test_cases()
# test_cases[test_case_name]

# prompt_completed = prompt.format(**test_cases[test_case_name])


conversation = [
    {
        "role": "chatbot",
        "content": "I can referr you to an AI assistant that specialises in sleep. Would you like that?",
    },
    {"role": "user", "content": "Yeah ok..."},
    {"role": "chatbot", "content": "¤:request_knowledge(sleep_assistant):¤"},
]


conversation = [
    {
        "role": "chatbot",
        "content": "Good! I am glad I could help. If you have any more questions, feel free to ask!",
    },
    {"role": "user", "content": "I cant find the damn settings!"},
    {"role": "chatbot", "content": "¤:request_knowledge(sleep_assistant):¤"},
]


def get_input_for_redirect_checker(conversation) -> str:
    # Grab the last two messages before the redirect
    chat_last2 = conversation[:-1][-2:]
    last_2_messages_string = "\n\n".join(
        [f"{message['role']}: {message['content']}" for message in conversation[-2:]]
    )
    return last_2_messages_string


conversation = conversation[-2:]

last_2_messages_string = get_input_for_redirect_checker(conversation)
# print_wrap(last_3_messages)

responses = []
for i in range(10):
    responses.append(
        complete_prompt_and_get_response(
            prompt_template_path_relative="referral_consent_checker_boolean_output",
            prompt_variables_dict={
                "last_2_messages": last_2_messages_string,
            },
        )
    )

# %%

conversation = [
    {"role": "system", "content": "the prompt"},
    {"role": "user", "content": "some user message"},
    {"role": "assistant", "content": "request"},
]


