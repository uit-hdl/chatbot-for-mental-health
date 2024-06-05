import gradio as gr
import sys
import os
import re
import numpy as np

from console_chat import PROMPTS
from console_chat import initiate_conversation_with_prompt
from console_chat import remove_inactive_sources
from console_chat import respond_to_user
from console_chat import dump_current_conversation_to_json
from console_chat import direct_to_new_assistant
from console_chat import truncate_if_too_long
from utils.general import remove_syntax_from_message
from utils.backend import reset_files_that_track_cumulative_variables
from utils.backend import get_file_names_in_directory
from utils.backend import load_textfile_as_string
from utils.backend import get_full_path
from utils.chat_utilities import grab_last_assistant_response

CHATBOT_PASSWORD = os.environ["CHATBOT_PASSWORD"]
SLIDES_DIR = "library/e-companion/slides"
CHATBOT_SHEETS_DIR = "library/e-companion/chatbot-sheets"
CHATBOT_ID = "e_companion"


def e_health_course_prototype():
    """Guides you trough module 1 with slides and chatbot in Gradio interface.
    racks two versions of the chat in parallell. DEEP_CHAT contains the raw
    conversation history, including system messages and raw chatbot responses
    which commands intended for backend interpretation. The surface_chat is the
    representation of the chat which is seen by the user and presented in the
    gradio interface."""
    global DEEP_CHAT, SLIDES, MAX_SLIDE_INDEX, SHEETS, SHEET_CURRENT

    # Get static global variables
    SLIDES = collect_textfile_info_in_dicts(SLIDES_DIR)
    MAX_SLIDE_INDEX = len(SLIDES) - 1
    SHEETS = collect_textfile_info_in_dicts(CHATBOT_SHEETS_DIR)
    DEEP_CHAT = initiate_new_chat()

    with gr.Blocks() as demo:
        slide_index = gr.State(0)
        sheet_content = gr.State(
            get_sheet_associated_with_slide(
                slide_name=SLIDES[slide_index.value]["name"]
            )
        )

        with gr.Row():

            with gr.Column():
                # Text content of slide
                slide_content = gr.Markdown(SLIDES[slide_index.value]["content"])
                # slide_content = gr.TextArea(SLIDES[slide_index.value]["content"])
                # Buttons for navigating slides
                with gr.Row():
                    back_button = gr.Button("Back")
                    next_button = gr.Button("Next")
                    back_button.click(
                        update_slide_index,
                        inputs=[back_button, slide_index],
                        outputs=[slide_index, slide_content],
                    )
                    next_button.click(
                        update_slide_index,
                        inputs=[next_button, slide_index],
                        outputs=[slide_index, slide_content],
                    )

            # Chatbot interface
            with gr.Column():
                surface_chat = gr.Chatbot(label="Your input")
                user_message = gr.Textbox(label="Enter message and hit enter")
                reset_button = gr.Button("Restart conversation")

                user_message.submit(
                    create_response,
                    inputs=[user_message, surface_chat, slide_index],
                    outputs=[user_message, surface_chat, slide_index],
                )
                reset_button.click(
                    reset_conversation,
                    inputs=[],
                    outputs=[user_message, surface_chat],
                )

    demo.launch(share=True)


def collect_textfile_info_in_dicts(dir) -> list[dict[str, str]]:
    """Collects information about slides/sheets in list of dictionary, each
    with the name and content of a slide/sheet."""
    names = get_file_names_in_directory(dir)
    content = load_text_variables_from_directory(dir)
    slides = [
        {
            "content": content,
            "name": name,
        }
        for content, name in zip(content, names)
    ]
    return slides


def get_slide_content():
    """Loads the contents of each slide."""
    return load_text_variables_from_directory(SLIDES_DIR)


def get_chatbot_sheets():
    """Loads the sheets used by the chatbot to assist the user with each
    slide."""
    return load_text_variables_from_directory(CHATBOT_SHEETS_DIR)


def load_text_variables_from_directory(dir):
    """Loads the text-files in the directory and dumps them as strings into a
    list."""
    strings = []
    full_directory_path = get_full_path(dir)
    for dir, _, files in os.walk(full_directory_path):
        for file in files:
            full_path = os.path.join(dir, file)
            content = load_textfile_as_string(full_path)
            strings.append(content)
    return strings


def initiate_new_chat():
    reset_files_that_track_cumulative_variables()
    return initiate_conversation_with_prompt(
        PROMPTS[CHATBOT_ID],
    )


def reset_conversation():
    """Function that gets called when 'Reset conversation' button gets
    clicked."""
    global DEEP_CHAT
    DEEP_CHAT = initiate_new_chat()
    return "", []


def create_response(user_message, surface_chat, slide_index):
    """Returns a tuple: ("", surface_chat). The surface chat has been updated
    with a response from the chatbot."""
    global DEEP_CHAT
    DEEP_CHAT.append({"role": "user", "content": user_message})
    DEEP_CHAT, harvested_syntax = respond_to_user(DEEP_CHAT, CHATBOT_ID)
    raw_response = grab_last_assistant_response(DEEP_CHAT)
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_message, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    for image_url in image_url_list:
        surface_chat.append((None, (image_url,)))

    dump_current_conversation_to_json(DEEP_CHAT)

    if harvested_syntax["referral"]:
        assistant_name = harvested_syntax["referral"]["name"]
        DEEP_CHAT = direct_to_new_assistant(assistant_name)
        surface_response = grab_last_assistant_response(DEEP_CHAT)
        surface_response_no_syntax = remove_syntax_from_message(surface_response)
        surface_chat.append((None, surface_response_no_syntax))

    DEEP_CHAT = remove_inactive_sources(DEEP_CHAT)
    DEEP_CHAT = truncate_if_too_long(DEEP_CHAT)

    return "", surface_chat


def update_slide_context():
    """Updates the deep chat so that the user message is always followed by
    the context that corresponds to that slide."""
    DEEP_CHAT.append({"role": "system", "content": ""})


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


def update_slide_index(button, slide_index):
    """Updates slide index, slide content, and chatbot sheet."""
    # Update current slide index.
    print(slide_index)
    if button == "Next":
        slide_index = cap(slide_index + 1)
    elif button == "Back":
        slide_index = cap(slide_index - 1)
    # print(SLIDES[slide_index])
    return slide_index, SLIDES[slide_index]["content"]


def cap(x):
    """Ensure value stays between 0 and a maximum value."""
    if x < 0:
        return 0
    elif x > MAX_SLIDE_INDEX:
        return MAX_SLIDE_INDEX
    else:
        return x


def authenticate(password):
    """Function to authenticate the user."""
    if password == CHATBOT_PASSWORD:
        return gr.update(visible=False), gr.update(visible=True), ""
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value="Wrong password, please try again.", visible=True),
        )


def get_sheet_associated_with_slide(slide_name) -> dict:
    """Fetches the sheet which corresponds to the slide. Each submodule consists
    of multiple slides, and each sheet corresponds to one sub-module."""
    slide_identifier = extract_trailing_numbers(slide_name)
    submodule_index = slide_identifier[0]
    sheet_content = [sheet for sheet in SHEETS if submodule_index in sheet["name"]]
    if len(sheet_content) != 1:
        raise ValueError(f"Slide corresponds to {len(sheet_content)} sheets.")
    return sheet_content[0]["content"]


def extract_trailing_numbers(string):
    match = re.search(r"\d+$", string)
    if match:
        return match.group()


if __name__ == "__main__":
    chatbot_id = "mental_health"
    if len(sys.argv) == 2:
        chatbot_id = sys.argv[1]
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    e_health_course_prototype()
