import path_setup

from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import DEPLOYMENTS


conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
conversation = generate_and_add_raw_bot_response(
    conversation, model_id="gpt-4", deployment_name="test-chatbot"
)

conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
conversation = generate_and_add_raw_bot_response(
    conversation, deployment_name="gpt-35-turbo-16k"
)
