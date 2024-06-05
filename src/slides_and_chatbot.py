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
from utils.chat_utilities import identify_user_messages

CHATBOT_PASSWORD = os.environ["CHATBOT_PASSWORD"]
SLIDES_DIR = "library/e-companion/slides"
CHATBOT_SOURCES_DIR = "library/e-companion/chatbot-sheets"
CHATBOT_ID = "e_companion"


def e_health_course_prototype():
    """Guides you trough module 1 with slides and chatbot in Gradio interface.
    racks two versions of the chat in parallell. DEEP_CHAT contains the raw
    conversation history, including system messages and raw chatbot responses
    which commands intended for backend interpretation. The surface_chat is the
    representation of the chat which is seen by the user and presented in the
    gradio interface."""
    global DEEP_CHAT, SLIDES, MAX_SLIDE_INDEX, SOURCES

    # Get static global variables
    SLIDES = collect_textfile_info_in_dicts(SLIDES_DIR)
    SOURCES = collect_textfile_info_in_dicts(CHATBOT_SOURCES_DIR)
    MAX_SLIDE_INDEX = len(SLIDES) - 1

    with gr.Blocks() as demo:
        deep_chat = gr.State(initiate_new_chat())
        slide_index = gr.State(0)

        with gr.Row():

            with gr.Column():
                # Text content of slide
                slide_content = gr.Markdown(SLIDES[slide_index.value]["content"])
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
                user_message = gr.Textbox(label="Enter message and hit enter")
                surface_chat = gr.Chatbot(label="Your input")
                reset_button = gr.Button("Restart conversation")

                user_message.submit(
                    create_response,
                    inputs=[user_message, surface_chat, slide_index, deep_chat],
                    outputs=[user_message, surface_chat, deep_chat],
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
    return load_text_variables_from_directory(CHATBOT_SOURCES_DIR)


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


def create_response(user_message, surface_chat, slide_index, deep_chat):
    """Returns a tuple: ("", surface_chat). The surface chat has been updated
    with a response from the chatbot."""
    deep_chat.append({"role": "user", "content": user_message})
    deep_chat = refresh_context_in_chat(deep_chat, slide_index)
    deep_chat, harvested_syntax = respond_to_user(deep_chat, CHATBOT_ID)
    raw_response = grab_last_assistant_response(deep_chat)
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_message, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    for image_url in image_url_list:
        surface_chat.append((None, (image_url,)))

    dump_current_conversation_to_json(deep_chat)

    if harvested_syntax["referral"]:
        assistant_name = harvested_syntax["referral"]["name"]
        deep_chat = direct_to_new_assistant(assistant_name)
        surface_response = grab_last_assistant_response(deep_chat)
        surface_response_no_syntax = remove_syntax_from_message(surface_response)
        surface_chat.append((None, surface_response_no_syntax))

    deep_chat = remove_inactive_sources(deep_chat)
    deep_chat = truncate_if_too_long(deep_chat)

    return "", surface_chat, deep_chat


def refresh_context_in_chat(deep_chat, slide_index) -> list[dict]:
    """Deletes old context message and replaces with new one. Assumes last
    message is from user."""
    # Delete old context message if there is one
    context_message, index_context_message = find_context_message(deep_chat)
    if context_message:
        del deep_chat[index_context_message]
    # Add new context message after user message
    context_message = create_context_message(slide_index)
    deep_chat.append({"role": "system", "content": context_message})
    return deep_chat


def find_context_message(deep_chat):
    """Gets the content and index of the slide context message."""
    context_message = None
    index_context_message = None
    for i, d in enumerate(deep_chat):
        if d["role"] == "system" and "CONTEXT" in d["content"]:
            context_message = d["content"]
            index_context_message = i
    if not context_message:
        print("No context message")
    return context_message, index_context_message


def create_context_message(slide_index: int) -> str:
    """Creates a context message of the form 'CONTEXT source {source_name}:
    {source_content}'"""
    slide_name = SLIDES[slide_index]["name"]
    slide_identifiers = extract_trailing_numerical_identifiers(slide_name)

    # Get header in source associated with the current slide
    slide_header = f"# SLIDE {slide_identifiers[0]}.{slide_identifiers[1]}"
    # Update source content to indicate relevant section
    source_content_updated = SOURCES[slide_index]["content"].replace(
        slide_header, f"{slide_header} [CURRENT]"
    )
    source_name = get_source_associated_with_slide(slide_name)["name"]
    context_message = f"CONTEXT source {source_name}: {source_content_updated}"

    return context_message


def get_source_associated_with_slide(slide_name: str) -> dict[str, str]:
    """Fetches the source which contains the information in the slide. Returns
    dictionary with keys "name" and "content". Each slide is expected to end in
    two numerical digits (e.g. name_13), the first of which refers to the
    submodule, i.e. the source. The sources are expected to start with a
    digit between 0 and 9 [UPDATE]."""
    slide_identifiers = extract_trailing_numerical_identifiers(slide_name)
    submodule_index = slide_identifiers[0]
    source = [source for source in SOURCES if source["name"][0] == submodule_index]
    if len(source) != 1:
        # There should be exactly one source associated with slide
        raise ValueError(f"Slide corresponds to {len(source)} sheets.")
    return source[0]


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


def update_slide_index(button, slide_index):
    """Updates slide index."""
    print(slide_index)
    if button == "Next":
        slide_index = cap_slide_index(slide_index + 1)
    elif button == "Back":
        slide_index = cap_slide_index(slide_index - 1)
    return slide_index, SLIDES[slide_index]["content"]


def cap_slide_index(x):
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


def extract_trailing_numerical_identifiers(slide_name):
    """Identifies the numerical identifiers of the slide."""
    match = re.search(r"(\d+)_(\d+)$", slide_name)
    if match and len(match.groups()) != 2:
        raise ValueError(f"Filename {slide_name} should have format name_i_j")
    return match.groups()


# Get static global variables
SLIDES = collect_textfile_info_in_dicts(SLIDES_DIR)
MAX_SLIDE_INDEX = len(SLIDES) - 1
SOURCES = collect_textfile_info_in_dicts(CHATBOT_SOURCES_DIR)


with gr.Blocks() as demo:
    deep_chat = gr.State(initiate_new_chat())
    slide_index = gr.State(0)

    with gr.Row():

        with gr.Column():
            # Text content of slide
            slide_content = gr.Markdown(SLIDES[slide_index.value]["content"])
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
            user_message = gr.Textbox(label="Enter message and hit enter")
            surface_chat = gr.Chatbot(label="Your input")
            reset_button = gr.Button("Restart conversation")

            user_message.submit(
                create_response,
                inputs=[user_message, surface_chat, slide_index, deep_chat],
                outputs=[user_message, surface_chat, deep_chat],
            )
            reset_button.click(
                reset_conversation,
                inputs=[],
                outputs=[user_message, surface_chat],
            )

demo.launch(share=True)


if __name__ == "__main__":
    chatbot_id = "mental_health"
    if len(sys.argv) == 2:
        chatbot_id = sys.argv[1]
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    e_health_course_prototype()
