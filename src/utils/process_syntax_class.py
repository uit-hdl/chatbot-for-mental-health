"""Functions that are related to processing of commands made by the bot, specifically: extracting
the part of strings that contain command syntax, separating the name of the command from the
argument of the command, and collecting the information in a managable format."""
import re
import os
import json
import ast

from typing import List
from typing import Dict

from utils.general import grab_last_assistant_response
from utils.general import remove_quotes_from_string
from utils.backend import file_exists
from utils.backend import IMAGES_DIR
from utils.backend import VIDEOS_DIR
from utils.backend import LIBRARY_DIR
from utils.backend import load_textfile_as_string
from utils.backend import get_shared_subfolder_name
from utils.backend import dump_to_json

from utils.backend import load_json_from_path

coversation = load_json_from_path("conversations/current/conversation.json")
coversation.append(
    {
        "role": "assistant",
        "content": "For \u00e5 finne 1Password-ikonet i nettleseren, f\u00f8lg disse trinnene:\n\n1. Klikk p\u00e5 det gr\u00e5 ikonet \u00f8verst til h\u00f8yre i nettleseren som ser ut som et puslespill. (`extensions_dropdown.png`)\n2. En nedtrekksliste vises som inkluderer 1password-utvidelsen. Klikk p\u00e5 1password og deretter p\u00e5 `pin`-ikonet ved siden av 1password-ikonet for \u00e5 feste denne utvidelsen til verkt\u00f8ylinjen for enkel tilgang.\n3. N\u00e5 vil du se 1Password-ikonet p\u00e5 verkt\u00f8ylinjen. Klikk p\u00e5 det for \u00e5 \u00e5pne 1Password.\n\nHer er bildet som viser hvor du finner puslespill-ikonet for \u00e5 feste 1Password-ikonet til verkt\u00f8ylinjen.\n\u00a4:display_image(extensions_dropdown.png):\u00a4\n\u00a4:cite([\"password_manager_a_norwegian\"]):\u00a4\n\nKan du pr\u00f8ve disse trinnene og gi meg beskjed om du har klart det?",
    }
)
chatbot_id = "tech_support_v2_norwegian"


class ProcessSyntaxOfBotResponse:
    """Scans the response for symbols ¤: and :¤ and extracts the name of the
    commands and their arguments. Returns a dictionary with keys being the command types, with each
    type containing the information collected for that type. Commands are 'referral',
    'request_knowledge', 'display_image', 'play_video', and 'show_sources'. Dumps the resulting
    dictionary to chat-info/harvested_syntax.json."""

    def __init__(self, conversation, chatbot_id):
        self.chatbot_id = chatbot_id
        self.subfolder = get_shared_subfolder_name(chatbot_id)
        self.knowledge_requests = None
        self.citations = None
        self.media = None

        chatbot_response = grab_last_assistant_response(conversation)

        print(self.citations)
        print(chatbot_response)
        # commands, arguments = extract_command_names_and_arguments(chatbot_response)
        # harvested_syntax = process_and_organize_commands_and_arguments(
        #     commands, arguments, subfolder
        # )

    def extract_command_names_and_arguments(self, chatbot_response: str) -> (list, list):
        """Takes a response that may contain substrings of the form ¤:command_name(argument):¤ and
        extracts the command names (command_name) and command arguments in lists."""
        chatbot_response_without_newlines = chatbot_response.replace("\n", "")
        command_pattern = r"¤:(.*?):¤"
        command_strings = re.findall(command_pattern, chatbot_response_without_newlines)
        commands = []
        arguments = []
        for command_string in command_strings:
            open_parenthesis_index = command_string.find("(")
            command_name = command_string[:open_parenthesis_index]
            argument = extract_command_argument(command_string)
            commands.append(command_name)
            arguments.append(argument)
        return commands, arguments

    def process_and_organize_commands_and_arguments(
        commands: list, arguments: list, subfolder: str
    ):
        """Processes the list of commands and associated arguments, and organizes this information in a
        dictionary."""
        harvested_syntax = {}
        harvested_syntax["knowledge_requests"] = get_knowledge_requests(
            commands, arguments, subfolder
        )
        harvested_syntax["sources"] = get_citations(commands, arguments)
        (
            harvested_syntax["images"],
            harvested_syntax["videos"],
        ) = get_image_and_video_requests(commands, arguments, subfolder)
        harvested_syntax["referral"] = get_referral(commands, arguments)
        harvested_syntax["end_chat"] = "end_chat" in commands
        return harvested_syntax

    def get_knowledge_requests(
        commands: list, arguments: list, subfolder: str
    ) -> List[Dict]:
        """Fetches the text associated with each knowledge request command."""
        sources = []
        if commands:
            for command, argument in zip(commands, arguments):
                if command == "request_knowledge":
                    knowledge = {}
                    source_path = os.path.join(LIBRARY_DIR, subfolder, argument) + ".md"
                    knowledge["source_name"] = remove_quotes_from_string(argument)
                    if file_exists(source_path):
                        knowledge["content"] = load_textfile_as_string(source_path)
                        knowledge["file_found"] = True
                    else:
                        knowledge["content"] = None
                        knowledge["file_found"] = False
                    sources.append(knowledge)
        return sources

    def get_citations(commands: list, arguments: list) -> list[str]:
        """Get sources that the chatbot has cited in its response."""
        sources = None
        for command, argument in zip(commands, arguments):
            if command == "cite":
                if argument is None:
                    print("Warning: Empty citation argument.")
                else:
                    try:
                        sources = ast.literal_eval(argument)
                    except (SyntaxError, ValueError):
                        print(f"Warning: could not evaluate citation: {argument}")
        return sources

    def get_image_and_video_requests(
        commands, arguments, subfolder
    ) -> (list[str], list[str]):
        """Finds file paths for the images and videos."""
        images = []
        videos = []
        for command, argument in zip(commands, arguments):
            if command == "display_image":
                filename = remove_quotes_from_string(argument)
                images.append(os.path.join(IMAGES_DIR, subfolder, filename))
            if command == "play_video":
                filename = remove_quotes_from_string(argument)
                videos.append(os.path.join(VIDEOS_DIR, subfolder, filename))

        return images, videos

    def get_referral(commands, arguments) -> dict:
        """Gets the referral dictionary with information on who to redirect the user to,
        and what the user needs help with."""
        for command, argument in zip(commands, arguments):
            if command == "referral":
                return convert_json_string_to_dict(argument)

    def convert_json_string_to_dict(json_data: str) -> dict:
        """Converts json file content extracted from a string into a dictionary."""
        # Standardize quotation marks
        json_data = json_data.replace("'", '"')
        try:
            result = json.loads(json_data)
        except json.JSONDecodeError as e:
            print(f"Warning: error decoding JSON string: {e}")
            result = None
        return result

    def extract_command_argument(command_string: str) -> str:
        """Extract command argument from strings. E.g. 'show_video(video_name)' -> 'show_video'."""
        arg = re.search(r"\((.*?)\)", command_string)
        if arg:
            return arg.group(1)


ProcessSyntaxOfBotResponse(coversation, chatbot_id)
