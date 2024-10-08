"""Functions that are related to processing of commands made by the bot, i.e. substrings
of the form '¤:command_name(argument):¤'. Extracts substrings that contain command syntax,
separates the name of the command from the argument of the command, and collects
information in a managable format. The main output (from process_syntax_of_bot_response)
is 

1. Dictionary 'harvested_syntax' wich collects the information on which commands are
   called, which files are requested, and the availability status of these files.

2. a list of system warning messages that are produced whenever an error is detected, such
   as when the bot requests a non-existant file."""

import re
import os

from typing import List
from typing import Dict
from typing import Tuple

from utils.chat_utilities import grab_last_assistant_response
from utils.general import remove_quotes_and_backticks
from utils.general import parse_literal
from utils.backend import IMAGES_DIR
from utils.backend import VIDEOS_DIR
from utils.backend import LIBRARY_DIR
from utils.backend import LOGGER
from utils.backend import PROMPTS_DIR
from utils.backend import HARVESTED_SYNTAX_DUMP_PATH
from utils.backend import load_textfile_as_string
from utils.backend import get_subfolder_of_assistant
from utils.backend import dump_to_json
from utils.backend import get_file_names_in_directory
from utils.backend import get_file_paths_in_directory
from utils.backend import remove_extension


def process_syntax_of_bot_response(conversation, chatbot_id) -> Tuple[dict, List[str]]:
    """Scans the response for symbols ¤: and :¤ and extracts the name of the
    commands and their arguments in two separate lists `commands` and `arguments`. Returns
    a dictionary with keys being the command types, with each type containing the
    information collected for that command type. Commands are 'referral',
    'request_knowledge', 'display_image', 'play_video', and 'show_sources'. Dumps the
    resulting dictionary to chat-info/harvested_syntax.json.

    Format of output:

    {
        "knowledge_extensions": list[
            {
                "content": str,
                "file_exists": bool,
                "name": str,
                "type": "knowledge_extension" | "referral"
            }
        ],
        "referral": list[str],
        "citations": list[str],
        "images": list[
            {
                "file_exists": true,
                "name": str,
                "path": str
            }
        ],
        "videos": list[
            {
                "file_exists": true,
                "name": str,
                "path": str
            }
        ],
    }

    Lists are empty if the associated commands are not detected
    """

    available_files = get_available_files(chatbot_id)

    chatbot_response = grab_last_assistant_response(conversation)
    commands, arguments = extract_command_names_and_arguments(chatbot_response)
    harvested_syntax = process_and_organize_commands_and_arguments(
        commands, arguments, available_files
    )

    dump_to_json(harvested_syntax, HARVESTED_SYNTAX_DUMP_PATH)

    return harvested_syntax


def get_available_files(chatbot_id: str) -> dict:
    """Finds and organizes all files (names and paths) associated with the
    chatbot-ID."""
    subfolder = get_subfolder_of_assistant(chatbot_id)

    available_files = {
        "sources": {
            "name": get_file_names_in_directory(os.path.join(LIBRARY_DIR, subfolder)),
            "path": get_file_paths_in_directory(os.path.join(LIBRARY_DIR, subfolder)),
        },
        "assistants": {
            "name": get_file_names_in_directory(os.path.join(PROMPTS_DIR, subfolder)),
            "path": get_file_paths_in_directory(os.path.join(PROMPTS_DIR, subfolder)),
        },
        "images": {
            "name": get_file_names_in_directory(os.path.join(IMAGES_DIR, subfolder)),
            "path": get_file_paths_in_directory(os.path.join(IMAGES_DIR, subfolder)),
        },
        "videos": {
            "name": get_file_names_in_directory(os.path.join(VIDEOS_DIR, subfolder)),
            "path": get_file_paths_in_directory(os.path.join(VIDEOS_DIR, subfolder)),
        },
    }

    return available_files


def extract_command_names_and_arguments(chatbot_response: str) -> Tuple[List, List]:
    """Takes a response, identifies substrings of the form ¤:command_name(argument):¤, and
    extracts command names and command arguments, which are returned as two synchronized
    lists: commands and arguments.
    """
    command_strings = get_commands(chatbot_response)
    commands = []
    arguments = []
    for command_string in command_strings:
        open_parenthesis_index = command_string.find("(")
        command_name = command_string[:open_parenthesis_index]
        argument = extract_command_argument(command_string)
        commands.append(command_name)
        arguments.append(argument)
    return commands, arguments


def get_commands(chatbot_response: str) -> list[str]:
    """Extracts commands from chatbot message as a list of strings."""
    chatbot_response_without_newlines = chatbot_response.replace("\n", "")
    command_pattern = r"¤:(.*?):¤"
    commands = re.findall(command_pattern, chatbot_response_without_newlines)
    return commands


def extract_command_argument(command_string: str) -> str:
    """Extract command argument from strings. E.g. 'play_video(video_name)' ->
    'video_name'."""
    arg = re.search(r"\((.*?)\)", command_string)
    if arg:
        return arg.group(1)


def process_and_organize_commands_and_arguments(
    commands: list, arguments: list, available_files: dict
):
    """Processes the list of commands and associated arguments, and organizes this
    information in a dictionary."""
    harvested_syntax = {}
    harvested_syntax["knowledge_extensions"], harvested_syntax["referral"] = (
        get_knowledge_requests(commands, arguments, available_files)
    )
    harvested_syntax["citations"] = get_assistant_citations(commands, arguments)
    harvested_syntax["images"] = get_image_requests(
        commands, arguments, available_files
    )
    harvested_syntax["videos"] = get_video_requests(
        commands, arguments, available_files
    )
    return harvested_syntax


def get_knowledge_requests(
    commands: list, arguments: list, available_files: dict
) -> List[Dict]:
    """Checks commands for requests to build knowledge or refer to new
    assistant. If these commands are found, gets the associated information."""
    knowledge_extensions = []
    referral = []
    names_of_available_assistants = available_files["assistants"]["name"]
    names_of_available_sources = available_files["sources"]["name"]

    if not commands:
        return knowledge_extensions, referral

    for command, argument in zip(commands, arguments):
        if command == "request_knowledge":
            knowledge_request_id = standardize_string_argument(argument)
            LOGGER.info(f"Bot requests knowledge {argument}")

            knowledge_request_dict = get_knowledge_request_details(
                knowledge_request_id,
                names_of_available_assistants,
                names_of_available_sources,
                available_files,
            )
            if knowledge_request_dict["type"] == "referral":
                referral = knowledge_request_dict
            else:
                knowledge_extensions.append(knowledge_request_dict)

    return knowledge_extensions, referral


def get_knowledge_request_details(
    knowledge_request_id: str,
    names_of_available_assistants: list[str],
    names_of_available_sources: list[str],
    available_files: dict,
):
    """Takes the id of the requested knowledge (points to an assistant or
    source, such as "13_stigma" or "sleep_assistant"), determines if it is a
    source or an assistant. Collects information pertaining to the request in a
    dictionary."""
    knowledge_request_dict = []

    if knowledge_request_id in names_of_available_assistants:
        # Referral requested
        knowledge_request_dict = {
            "name": knowledge_request_id,
            "content": None,
            "type": "referral",
            "file_exists": True,
        }
    elif knowledge_request_id in names_of_available_sources:
        # Knowledge insertion requested
        path = available_files["sources"]["path"][
            available_files["sources"]["name"].index(knowledge_request_id)
        ]
        knowledge_request_dict = {
            "name": knowledge_request_id,
            "content": load_textfile_as_string(path),
            "type": "knowledge_extension",
            "file_exists": True,
        }
    else:
        # Requests for non-existing files are arbitrarily treated as insertions
        knowledge_request_dict = {
            "name": knowledge_request_id,
            "content": None,
            "type": "knowledge_extension",
            "file_exists": False,
        }

    return knowledge_request_dict


def get_assistant_citations(
    commands: list,
    arguments: list,
) -> list[str]:
    """Get citations for sources in the bot response. Example output ["source_a",
    "source_b"]."""
    citations = []
    for command, argument in zip(commands, arguments):
        if command == "cite":
            citations = argument
            if argument is None:
                LOGGER.info("Empty citation argument.")
            else:
                citations = parse_literal(argument)

    return citations


def get_image_requests(commands, arguments, available_files) -> list[dict]:
    """Finds file paths, file name, and checks if requested files exists. Returns list
    with dictionary for each requested video, containing the name of the video, status for
    its existance, and file path.
    """
    images = []
    for command, argument in zip(commands, arguments):
        if command == "display_image":
            name = standardize_string_argument(argument)

            if name in available_files["images"]["name"]:
                path = available_files["images"]["path"][
                    available_files["images"]["name"].index(name)
                ]
                image = {"name": name, "path": path, "file_exists": True}
            else:
                image = {"name": name, "path": None, "file_exists": False}

            images.append(image)

    return images


def get_video_requests(commands, arguments, available_files) -> list[dict]:
    """(similar to get_image_requests) Finds file paths, file name, and checks if
    requested files exists. Returns list with dictionary for each requested video,
    indicating the name of the video, status for its existance, and file path."""
    videos = []
    for command, argument in zip(commands, arguments):
        if command == "play_video":
            name = standardize_string_argument(argument)

            if name in available_files["videos"]["name"]:
                path = available_files["videos"]["path"][
                    available_files["videos"]["name"].index(name)
                ]
                video = {"name": name, "path": path, "file_exists": True}
            else:
                video = {"name": name, "path": None, "file_exists": False}

            videos.append(video)

    return videos


def standardize_string_argument(name: str):
    """Standardized the filename that has been extracted from
    ¤:command(filename):¤ by removing extra strings and backticks."""
    name_standardized = remove_quotes_and_backticks(name)
    name_standardized = remove_extension(name_standardized)
    return name_standardized


def insert_commands(commands_list: list[str], message: str):
    """Inserts a list of commands into the start of the message, enclosing them with :¤ and :¤."""
    inserted_commands = " ".join([f"¤:{s}:¤" for s in commands_list])
    return f"{inserted_commands} {message}"
