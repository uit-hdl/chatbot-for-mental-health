"""Functions involved in the process of presenting the chat in the console and making it look nice
to humans."""

from utils.general import remove_code_syntax_from_message
from utils.general import contains_only_whitespace
from utils.general import wrap_and_print_message


def display_last_response(conversation):
    """Displays the last response of the conversation (removes syntax)."""
    display_message_without_syntax(message_dict=conversation[-1])


def display_message_without_syntax(message_dict: dict):
    """Takes a message in dictionary form, removes the code syntax, and prints
    it in the console."""
    role = message_dict["role"].strip()
    message = message_dict["content"].strip()
    message_cleaned = remove_code_syntax_from_message(message)
    if not contains_only_whitespace(message_cleaned):
        wrap_and_print_message(role, message_cleaned)
