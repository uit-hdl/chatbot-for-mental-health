"""Function that converts a conversation. in JSON format to a nicely formatted 
markdown file."""
import sys

from utils.general import silent_print
from utils.backend import dump_conversation_to_colorcoded_md_file
from utils.backend import load_json_from_path


def convert_json_chat_to_markdown(
    jsonfile_path="conversations/current/conversation.json",
    mdfile_path="conversations/formatted/conversation.md",
):
    """Converts the conversation in JSON format to an .md file."""
    conversation = load_json_from_path(jsonfile_path)
    dump_conversation_to_colorcoded_md_file(conversation, mdfile_path)
    silent_print(f"Dumped to conversation to {mdfile_path}")


if __name__ == "__main__":
    jsonfile_path="conversations/current/conversation.json"
    mdfile_path="conversations/formatted/conversation.md"
    if len(sys.argv) == 2:
        jsonfile_path = sys.argv[1]
    if len(sys.argv) == 3:
        mdfile_path = sys.argv[2]
    convert_json_chat_to_markdown(jsonfile_path, mdfile_path)
