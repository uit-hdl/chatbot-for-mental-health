import yaml
import json
import os
import pathlib
import yaml
import datetime
from collections import namedtuple

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

CONFIG_PATH = os.path.join(ROOT_DIR, "config/config.yaml")
API_KEY_PATH = os.path.join(API_DIR, "insomnia_bot_azure.yaml")
SETTINGS_PATH = os.path.join(ROOT_DIR, "config/settings.yaml")
URL_MAP_PATH = os.path.join(ROOT_DIR, "config/url.yaml")

# Map showing which directories contains files corresponding to each type of command
COMMAND_TO_DIR_MAP = {
    "request_knowledge": LIBRARY_DIR,
    "display_image": IMAGES_DIR,
    "play_video": VIDEOS_DIR,
}
# Extensions associated with the files of each type of command.
COMMAND_TO_EXTENSION_MAP = {
    "request_knowledge": ".md",
    "display_image": ".png",
    "play_video": ".mkv",
}


def collect_prompts_in_dictionary(directory_path):
    """Finds paths for all files in directory and subdirectories, and creates a
    dictionary where the keys are file names and the values are file paths."""
    all_files = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_name_without_extension = os.path.splitext(file)[0]
            all_files[file_name_without_extension] = load_textfile_as_string(file_path)
    return all_files


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


def dump_to_json(file, file_path):
    """Save thr `dump_dict` to the json file under the path given in relation to
    the root directory."""
    full_path = get_full_path_and_create_dir(file_path)
    with open(full_path, mode="w", encoding="utf-8") as json_file:
        json.dump(file, json_file, sort_keys=True, indent=4)


def dump_current_conversation(conversation, filename="conversation"):
    """Dumps the conversation to the conversation directory as a json file."""
    file_path = f"{CONVERSATIONS_CURRENT_DIR}/{filename}.json"
    dump_to_json(conversation, file_path)


def dump_conversation_with_timestamp(conversation, label="conversation"):
    """Dumps the chatbot conversation in conversations/ with the date of the
    conversation in the name. The name can be given a more descriptive name
    through the 'label' argument."""
    # Get the current date and time
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{label}_{formatted_datetime}.txt"
    dump_conversation_to_textfile(filename, conversation)
    print(f"Conversation stored in {filename}")


def dump_conversation_to_textfile(filename, conversation):
    """Dumps the conversation to a textfile in conversations/formatted/filename."""
    path_relative = f"{CONVERSATIONS_DIR}/formatted/{filename}"
    full_path = get_full_path_and_create_dir(path_relative)
    # Remove the initial prompt
    conversation = conversation[1:]
    with open(full_path, "w") as file:
        for message in conversation:
            role = message["role"]
            content = message["content"]
            file.write(f"{role.capitalize()}: {content}\n\n")


def dump_conversation_to_textfile(conversation: list, filepath: str):
    """Dumps a conversation to a Markdown file with color-coded roles."""
    full_path = get_full_path_and_create_dir(filepath)

    with open(full_path, "w") as file:
        for i, message in enumerate(conversation):
            role = message["role"]
            content = message["content"]

            if role == "assistant":
                colored_role = '**<font color="#44cc44">assistant</font>**'
            elif role == "user":
                colored_role = '**<font color="#3399ff">user</font>**'
            elif role == "system":
                if i > 0:
                    content = f'<font color="#999999">{content}</font>'
                colored_role = '**<font color="#999999">system</font>**'
            else:
                colored_role = role  # For any other roles

            if i == 1:
                header = "\n\n\n\n# Conversation \n\n\n\n"
                formatted_message = f"{header}{colored_role}: {content}  \n\n\n\n"
            else:
                formatted_message = f"\n{colored_role}: {content}  \n\n\n\n"

            file.write(formatted_message)


def add_extension(path, extension):
    """Takes a path relative to the output folder and adds the specified 
    extension (e.g., '.csv') if the path has no extension."""
    if os.path.splitext(path)[-1] == "":
        path += extension
    return path


def get_filename(file_path, include_extension=False):
    """Gets the name of the file associated with the path."""
    file_name = os.path.basename(file_path)
    if include_extension:
        return file_name
    return os.path.splitext(file_name)[0]


def file_exists(file_path):
    """Checks if the file in the specified path exists."""
    if file_path is None:
        return False
    return os.path.isfile(get_full_path(file_path))


def get_shared_subfolder_name(prompt_file_name: str):
    """Convention -> all directories that contain files associated with an assistant must consist of
    the following two components: the file-specific directory (such as media/images) and an
    assistant-specific path relative to the file-specific directory. This function takes the name of
    the assistant and inferrs the assistant-specific relative path. For example, if images are
    located in 'media/images/ex_bots/ex_bot_A/', then the assistant-specific path is
    'ex_bots/ex_bot_A/'. Following this convention makes it easier to write prompts, since only the
    file name needs to be specified."""
    prompt_path = get_relative_path_of_prompts_file(prompt_file_name)

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


def get_relative_path_of_prompts_file(prompt_file_name: str) -> str:
    """Identifies the prompts in the prompts directory for all, and finds the relative path for the
    file name provided. Note that prompts should have unique names for this to work well."""
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


PROMPTS = collect_prompts_in_dictionary(PROMPTS_DIR)

CONFIG = load_yaml_file(CONFIG_PATH)
SETTINGS = load_yaml_file(SETTINGS_PATH)
URL = load_yaml_file(URL_MAP_PATH)
API_KEY = load_yaml_file(API_KEY_PATH)["key"]

MODEL_ID = CONFIG["model_id"]
