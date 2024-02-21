"""Function that converts a conversation. in JSON format to a nicely formatted 
markdown file."""

import sys

from utils.general import silent_print
from utils.backend import get_full_path_and_create_dir
from utils.backend import load_json_from_path


def convert_json_chat_to_markdown(
    jsonfile_path="conversations/current/conversation.json",
    mdfile_path="conversations/formatted/conversation.md",
    color_code=False,
):
    """Converts the conversation in JSON format to an .md file."""
    conversation = load_json_from_path(jsonfile_path)
    dump_conversation_to_markdown_file(conversation, mdfile_path, color_code)
    silent_print(f"Dumped to conversation to {mdfile_path}")


def dump_conversation_to_markdown_file(
    conversation: list, filepath: str, color_code=True
):
    """Dumps a conversation to a Markdown file with color-coded roles."""
    full_path = get_full_path_and_create_dir(filepath)

    with open(full_path, "w") as file:
        for i, message in enumerate(conversation):
            role = message["role"]
            content = message["content"]
            if color_code:
                colored_role, content = color_code_role_and_content(role, content, i)
            else:
                colored_role = role

            if i == 1:
                header = "\n\n# Conversation \n\n"
                formatted_message = f"{header}{colored_role}: {content}  \n\n"
            else:
                formatted_message = f"\n{colored_role}: {content}  \n\n"

            file.write(formatted_message)


def color_code_role_and_content(role: str, content: str, message_index: int):
    """Color codes the role and content of the message."""
    if role == "assistant":
        colored_role = '**<font color="#44cc44">assistant</font>**'
    elif role == "user":
        colored_role = '**<font color="#3399ff">user</font>**'
    elif role == "system":
        if message_index > 0:
            content = f'<font color="#999999">{content}</font>'
        colored_role = '**<font color="#999999">system</font>**'
    else:
        colored_role = role
    return colored_role, content


if __name__ == "__main__":
    jsonfile_path = "conversations/current/conversation.json"
    mdfile_path = "conversations/formatted/conversation.md"
    color_code = False
    if len(sys.argv) == 2:
        jsonfile_path = sys.argv[1]
    if len(sys.argv) == 3:
        mdfile_path = sys.argv[2]
    if len(sys.argv) == 4:
        color_code = sys.argv[3]
    convert_json_chat_to_markdown(jsonfile_path, mdfile_path, color_code)
