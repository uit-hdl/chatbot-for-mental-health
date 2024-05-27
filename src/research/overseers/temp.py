import path_setup

from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.backend import MODEL_TO_DEPLOYMENT_MAP


conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
conversation = generate_and_add_raw_bot_response(
    conversation, model_id="gpt-4", model="gpt-4"
)

conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
conversation = generate_and_add_raw_bot_response(
    conversation, model="gpt-35-turbo-16k"
)
