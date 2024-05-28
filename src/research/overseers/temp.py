import path_setup

from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import generate_and_add_raw_bot_response
from utils.chat_utilities import get_chat_completion


conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
response = get_chat_completion(conversation, model="gpt-35-turbo-16k")
response.model
conversation = generate_and_add_raw_bot_response(
    conversation, model_id="gpt-4", model_llm="gpt-35-turbo-16k"
)

conversation = [
    {
        "role": "system",
        "content": "You are a polite chatbot who communicates only in brief polite sentences.",
    },
    {"role": "user", "content": "hello! How are you?"},
]
conversation = generate_and_add_raw_bot_response(
    conversation, model_llm="gpt-35-turbo-16k"
)
