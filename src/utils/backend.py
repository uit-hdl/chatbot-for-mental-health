import yaml
import json
import os
import pathlib
import yaml
from typing import Tuple

from utils.logging import setup_logging

# Directory paths
ROOT_DIR = pathlib.Path(__file__).parents[2]
API_DIR = os.path.join(pathlib.Path(__file__).parents[3], "api-keys")
CONVERSATIONS_DIR = os.path.join(ROOT_DIR, "conversations")
CONVERSATIONS_CURRENT_DIR = os.path.join(ROOT_DIR, "conversations/current")
CONVERSATIONS_RAW_DIR = os.path.join(CONVERSATIONS_DIR, "raw")
CONVERSATIONS_FORMATTED_DIR = os.path.join(CONVERSATIONS_DIR, "formatted")
USER_DATA_DIR = os.path.join(ROOT_DIR, "user-data")
IMAGES_DIR = os.path.join(ROOT_DIR, "media/images")
VIDEOS_DIR = os.path.join(ROOT_DIR, "media/videos")
LIBRARY_DIR = os.path.join(ROOT_DIR, "library")
PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts")
CHAT_INFO_DIR = os.path.join(ROOT_DIR, "chat-info")

# Configuration file paths
CONFIG_PATH = os.path.join(ROOT_DIR, "config/config.yaml")
API_KEY_PATH = os.path.join(API_DIR, "insomnia_bot_azure.yaml")
SETTINGS_PATH = os.path.join(ROOT_DIR, "config/settings.yaml")
URL_MAP_PATH = os.path.join(ROOT_DIR, "config/url.yaml")

# File-dump paths
LOGFILE_DUMP_PATH = os.path.join(CHAT_INFO_DIR, "chat.log")
LOGFILE_REJECTED_RESPONSES_DUMP_PATH = os.path.join(
    CHAT_INFO_DIR, "rejected_responses.log"
)
TRUNCATION_INFO_DUMP_PATH = os.path.join(CHAT_INFO_DIR, "truncated_message.json")
OVERSEER_DUMP_PATH = os.path.join(CHAT_INFO_DIR, "overseer_chat.json")
HARVESTED_SYNTAX_DUMP_PATH = os.path.join(CHAT_INFO_DIR, "harvested_syntax.json")
TOKEN_USAGE_DUMP_PATH = os.path.join(CHAT_INFO_DIR, "token-usage/chat_consumption.json")

LOGGER, LOGGER_REJECTED_RESPONSES = setup_logging(
    LOGFILE_DUMP_PATH, LOGFILE_REJECTED_RESPONSES_DUMP_PATH
)


def convert_json_string_to_dict(json_data: str) -> dict:
    """Converts json file content extracted from a string into a dictionary."""
    # Ensure proper JSON format (deal with special characters)
    json_data = json_data.replace("\n", "")
    json_string_valid_format = json.dumps(json_data)
    try:
        # To string (dont know why this works...)
        python_string = json.loads(json_string_valid_format)
        dictionary = json.loads(python_string)  # To dictionary
    except json.JSONDecodeError as e:
        print(f"Warning: error decoding JSON string: {e}")
        dictionary = None
    return dictionary


def get_file_names_in_directory(directory_path):
    """Retrieve the names of all files (without extensions) within the specified directory
    and its subdirectories."""
    file_names = []
    full_directory_path = get_full_path(directory_path)
    for _, _, files in os.walk(full_directory_path):
        for file in files:
            file_name, _ = os.path.splitext(file)
            file_names.append(file_name)
    return file_names


def load_textfile_as_string(file_path, extension=None) -> str:
    """Loads a text file and returns the contents as a string."""
    if extension:
        file_path = add_extension(file_path, extension)
    file_path = get_full_path(file_path)
    with open(file_path, "r") as file:
        file_string = file.read()
    return file_string


def load_yaml_file(file_path) -> dict:
    file_path = add_extension(file_path, ".json")
    with open(file_path, "r") as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data


def load_json_from_path(file_path: str) -> dict:
    """Read yaml file from `path`."""
    file_path = get_full_path(file_path)
    with open(file_path, mode="r", encoding="utf-8") as jfl:
        json_loaded = json.load(jfl)
    return json_loaded


def get_full_path_and_create_dir(file_path):
    """Takes a path relative to the project folder and creates the full path.
    Also creates the specified directory if it does not exist."""
    path = get_full_path(file_path)
    dirpath = os.path.dirname(path)
    if dirpath != "":
        os.makedirs(dirpath, exist_ok=True)
    return path


def get_full_path(path_relative):
    """Takes a path relative to the project root folder and produces the full path."""
    return os.path.join(ROOT_DIR, path_relative)


def dump_to_json(dump_dict, file_path):
    """Save thr `dump_dict` to the json file under the path given in relation to
    the root directory."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, mode="w", encoding="utf-8") as json_file:
        json.dump(dump_dict, json_file, sort_keys=True, indent=4)


def dump_current_conversation_to_json(conversation, filename="conversation"):
    """Dumps the conversation to the conversation directory as a json file."""
    dump_to_json(conversation, f"{CONVERSATIONS_CURRENT_DIR}/{filename}.json")
    dump_to_json(conversation, f"{CHAT_INFO_DIR}/{filename}.json")


def dump_conversation(conversation: list, label: str = "conversation"):
    """Stores conversation in json format in conversations/raw and in formatted
    markdown file in conversations/formatted. Default name is `conversation`."""
    json_file_path = f"{CONVERSATIONS_RAW_DIR}/{label}.json"
    txt_file_path = f"{CONVERSATIONS_FORMATTED_DIR}/{label}.md"
    if conversation[-1]["content"] == "break":
        conversation = conversation[:-1]
    dump_to_json(conversation, json_file_path)
    LOGGER.info(f"Conversation stored in {json_file_path} and {txt_file_path}")


def add_extension(path, extension):
    """Takes a path relative to the output folder and adds the specified
    extension (e.g., '.csv') IF the path has no extension."""
    if os.path.splitext(path)[-1] == "":
        path += extension
    return path


def remove_extension(path):
    """Removes the extension from the path or file"""
    path_without_extension, _ = os.path.splitext(path)
    return path_without_extension


def file_exists(file_path):
    """Checks if the file in the specified path exists."""
    if file_path is None:
        return False
    return os.path.isfile(get_full_path(file_path))


def get_sources_available_to_chatbot(chatbot_id: str) -> list[str]:
    """Gets a list of sources that the specified chatbot can request."""
    chatbot_subfolder = get_subfolder_of_assistant(chatbot_id)
    return get_file_names_in_directory(os.path.join(LIBRARY_DIR, chatbot_subfolder))


def get_source_content_and_path(chatbot_id: str, source_name: str) -> Tuple[str, str]:
    """Finds the content and path of a source. The filename of the prompt is used to find
    the subfolder that the source is expected to be located in."""
    source_path = get_path_to_source(source_name, chatbot_id)
    if source_path:
        content = load_textfile_as_string(source_path)
    else:
        content = None
    return content, source_path


def get_path_to_source(source_name: str, chatbot_id: str):
    """Finds the full path to the specified source."""
    bot_subfolder = get_subfolder_of_assistant(chatbot_id)
    sources_directory = os.path.join(LIBRARY_DIR, bot_subfolder)
    source_paths = get_file_paths_in_directory(sources_directory)
    source_names = [get_filename(source_path) for source_path in source_paths]
    if source_name in source_names:
        return source_paths[source_names.index(source_name)]
    else:
        return None


def get_subfolder_of_assistant(prompt_file_name: str):
    """Convention -> all directories that contain files associated with an assistant must
    consist of the following two components: the file-specific directory (such as
    media/images) and an assistant-specific path relative to the file-specific directory.
    This function takes the name of the assistant and inferrs the assistant-specific
    relative path. For example, if images are located in 'media/images/ex_bots/ex_bot_A/',
    then the assistant-specific path is 'ex_bots/ex_bot_A/'. Following this convention
    makes it easier to write prompts, since only the file name needs to be specified."""
    prompt_path = get_relative_path_of_prompt_file(prompt_file_name)

    # Get the directory name from the file path
    directory = os.path.dirname(prompt_path)
    # Split the directory path into components
    components = directory.split(os.path.sep)
    # Check if there is a subfolder (at least two components)
    if len(components) >= 2:
        subfolder = os.path.join(*components[1:])
        return subfolder
    else:
        return None  # Return None if there is no subfolder


def get_relative_path_of_prompt_file(prompt_file_name: str) -> str:
    """Identifies the prompts in the prompts directory for all, and finds the relative
    path for the file name provided. Note that prompts should have unique names for this
    to work well.
    """
    full_path = PROMPTS_DIR
    prompt_file_name = add_extension(prompt_file_name, ".md")
    matches = []
    # Iterate over the files in the directory
    for root, dirs, files in os.walk(full_path):
        if prompt_file_name in files:
            # File found, find the path relative to the root directory
            matches.append(
                os.path.relpath(os.path.join(root, prompt_file_name), start=ROOT_DIR)
            )

    if len(matches) == 0:
        print("No match found")
        return None
    elif len(matches) > 1:
        print("Warning: name of prompt file is not unique")
        return matches[0]
    if len(matches) == 1:
        return matches[0]


def get_file_paths_in_directory(directory_path):
    """Get the paths of all files within the specified directory and its
    subdirectories."""
    file_names = []
    full_directory_path = get_full_path(directory_path)
    for root, _, files in os.walk(full_directory_path):
        for file in files:
            file_names.append(os.path.join(root, file))
    return file_names


def get_filename(file_path, include_extension=False):
    """Gets the name of the file associated with the path."""
    file_name = os.path.basename(file_path)
    if include_extension:
        return file_name
    return os.path.splitext(file_name)[0]


def collect_prompts_in_dictionary(directory_path):
    """Finds paths for all files in directory and subdirectories, and creates a
    dictionary where the keys are file names and the values are file paths."""
    all_files = {}
    file_paths = get_file_paths_in_directory(directory_path)
    for file_path in file_paths:
        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        all_files[file_name_without_extension] = load_textfile_as_string(file_path)
    return all_files


PROMPTS = collect_prompts_in_dictionary(PROMPTS_DIR)

CONFIG = load_yaml_file(CONFIG_PATH)
SETTINGS = load_yaml_file(SETTINGS_PATH)
API_KEY = load_yaml_file(API_KEY_PATH)["key"]

MODEL_ID = CONFIG["model_id"]
