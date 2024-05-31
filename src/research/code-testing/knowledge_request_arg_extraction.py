import path_setup

from utils.process_syntax import extract_command_names_and_arguments
from utils.process_syntax import extract_command_argument
from utils.process_syntax import process_syntax_of_bot_response

conversation = [
    {
        "content": """¤:request_knowledge(["1_what_is_schizophrenia"]):¤""",
        "role": "assistant",
    }
]

process_syntax_of_bot_response(conversation, "mental_health")
