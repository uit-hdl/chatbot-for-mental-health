"""I have noticed that when I talk to GPT-3.5 online, i can often get it to
behave more like how I want then I when I attempt to single-message prompt it.
So, I recreate the conversation here to see if I can get it to behave better."""

from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import delete_last_bot_response
from utils.console_chat_display import display_last_response
from utils.console_chat_display import display_message_without_syntax
from utils.console_chat_display import reprint_whole_conversation_without_syntax
from functions import dump_to_json_locally


# %%
conversation = []
initial_message = """I am prompt engineering a chatbot called
schizophrenia_expert. I need you to help me verify its output messages.
Specifically, I do not want it to make any claims unless they are 1.
non-controversial, and 2. accompanied by the following disclaimer:

'However, you should verify this information with your health-care provider
before acting on it. As an AI agent, my answers can be incorrect.

If the bot makes any utterances that could be considered a claim or advice, it
must include this disclaimer to inform users of the potential inaccuracies and
the need for verification. Do you understand?"""


def add_system_message(message):
    if conversation and conversation[-1]["role"] == "system":
        return conversation
    conversation.append({"content": message, "role": "system"})
    return conversation


def delete_last_message(conversation):
    del conversation[-1]
    return conversation


def gen_response(conversation):
    if conversation[-1]["role"] == "assistant":
        # Regenerate response
        return generate_and_add_raw_bot_response(
            conversation[:-1], deployment_name="gpt-35-turbo-test"
        )
    return generate_and_add_raw_bot_response(
        conversation, deployment_name="gpt-35-turbo-test"
    )


def print_whole_chat(conversation):
    for message in conversation:
        display_message_without_syntax(message)


add_system_message(initial_message)

print_whole_chat(conversation)

# %% Getting it to read back to me what it understands.
conversation = gen_response(conversation)
print_whole_chat(conversation)

# %%
add_system_message(
    """Perfect! Here is the first message to check:

'Intelligence can be assessed using specific tests, such as IQ (Intelligence
Quotient) tests, which are designed to measure a range of cognitive abilities.
However, these tests may not capture all aspects of intelligence, which is
multifaceted and can encompass a variety of skills and knowledge areas. If
you're asking in relation to schizophrenia, cognitive functions can be affected,
but intelligence itself is a broader concept. Would you like information related
to cognition and schizophrenia?'.

Does this message align with the rules I descibed? Answer in 10 words or
less."""
)
print_whole_chat(conversation)

# %% Getting it to read back to me what it understands.
conversation = gen_response(conversation)
print_whole_chat(conversation)

# %%
add_system_message(
"""Incorrect. For example, it makes the claim that intelligence can be
tested with an IQ test, and makes further claims about the limitations of this test. It
also does encourage the user to double-check these claims. Do you understand?"""
)
print_whole_chat(conversation)

# %% Getting it to read back to me what it understands.
conversation = gen_response(conversation)
print_whole_chat(conversation)

# %%
add_system_message(
"""Here is another one:

'Laughing along with someone when they laugh can indeed create a shared moment
of joy and can help to build rapport. It shows that you're engaged in the
conversation and that you find enjoyment in the interaction. This shared
laughter can make you seem more likable and approachable. Just be sure that your
laughter is sincere; forced laughter can sometimes have the opposite effect.
Would you be interested in learning about other ways to connect positively with
people?'

Please respond with a 10 word summary on whether or not it aligns with the rule,
followed by one of these evaluations: "ACCEPTED", "WARNING", or "REJECTED".
"""
)
print_whole_chat(conversation)

# %% Getting it to read back to me what it understands.
conversation = gen_response(conversation)
print_whole_chat(conversation)
