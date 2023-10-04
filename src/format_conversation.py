"""This script takes a conversation in conversations/raw and prints it to text file that is
dumped in conversations/formatted."""

import datetime
import sys

from utils.backend import load_json_from_path
from utils.backend import add_extension
from utils.backend import CONVERSATIONS_DIR
from utils.backend import get_full_path_and_create_dir
from utils.backend import CONVERSATIONS_RAW_DIR


def format_conversation(filename, output_filename):
    """Loads a the conversation (in json format) and prints it to a text file in conversation/formatted."""
    filename = add_extension(f"{CONVERSATIONS_RAW_DIR}/{filename}", ".json")
    conversation = load_json_from_path(filename)
    dump_conversation_with_timestamp(conversation, output_filename)


def dump_conversation_with_timestamp(conversation, filename):
    """Dumps the chatbot conversation in conversations/ with the date of the
    conversation in the name. The name can be given a more descriptive name
    through the 'label' argument."""
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{filename}_{formatted_datetime}"
    filename = add_extension(filename, ".txt")
    dump_conversation_to_textfile(filename, conversation)
    print(f"Conversation stored in {filename}")


def dump_conversation_to_textfile(filename, conversation):
    """Dumps a conversation to a textfile."""
    path_relative = f"{CONVERSATIONS_DIR}/formatted/{filename}"
    full_path = get_full_path_and_create_dir(path_relative)
    # Remove the initial prompt
    conversation = conversation[1:]
    with open(full_path, "w") as file:
        for message in conversation:
            role = message["role"]
            content = message["content"]
            file.write(f"{role.capitalize()}: {content}\n\n")
            

if __name__  ==  "__main__":
    filename = "conversation"
    filename_output = "conversation"

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    if len(sys.argv) > 2:
        filename_output = sys.argv[2]

    format_conversation(filename, filename_output)