import gradio as gr
import sys
import os

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


def e_health_course_prototype(chatbot_id, server_port=None):
    """Guides you trough module 1 with slides and chatbot in Gradio interface.
    racks two versions of the chat in parallell. DEEP_CHAT contains the raw
    conversation history, including system messages and raw chatbot responses
    which commands intended for backend interpretation. The surface_chat is the
    representation of the chat which is seen by the user and presented in the
    gradio interface."""
    global DEEP_CHAT, SLIDE_CONTENTS, MAX_SLIDE_INDEX, CHATBOT_ID, CURRENT_SLIDE_FLAT_INDEX

    # Set global variables
    CHATBOT_ID = chatbot_id
    SLIDE_CONTENTS = get_slide_content()
    MAX_SLIDE_INDEX = len(SLIDE_CONTENTS) - 1
    CURRENT_SLIDE_FLAT_INDEX = 0
    CURRENT_SLIDE_ID = "0.0"
    DEEP_CHAT = initiate_new_chat()

    with gr.Blocks() as demo:

        with gr.Row():

            with gr.Column():
                # Text content of slide
                slide_text = gr.Markdown(SLIDE_CONTENTS[CURRENT_SLIDE_FLAT_INDEX])

                # Buttons for navigating slides
                with gr.Row():
                    back_button = gr.Button("Back")
                    next_button = gr.Button("Next")
                    back_button.click(previous_slide, outputs=slide_text)
                    next_button.click(next_slide, outputs=slide_text)

            # Chatbot interface (initially hidden)
            with gr.Column(visible=True, elem_id="chat_interface") as chat_interface:
                surface_chat = gr.Chatbot(label="Your input")
                user_message = gr.Textbox(label="Enter message and hit enter")
                reset_button = gr.Button("Restart conversation")

                user_message.submit(
                    create_response,
                    inputs=[user_message, surface_chat],
                    outputs=[user_message, surface_chat],
                )
                reset_button.click(
                    reset_conversation,
                    inputs=[],
                    outputs=[user_message, surface_chat],
                )

    demo.launch(share=True, server_port=server_port)


def get_slide_content():
    slide_contents = []
    full_directory_path = get_full_path("library/e-companion/slides")
    for dir, _, files in os.walk(full_directory_path):
        for file in files:
            full_path = os.path.join(dir, file)
            content = load_textfile_as_string(full_path)
            slide_contents.append(content)
    return slide_contents


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


def create_response(user_message, surface_chat):
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


def previous_slide():
    """Updates slide index and the content of the slide."""
    global CURRENT_SLIDE_FLAT_INDEX
    # Update current slide index.
    CURRENT_SLIDE_FLAT_INDEX = cap(CURRENT_SLIDE_FLAT_INDEX - 1)
    slide_content = SLIDE_CONTENTS[CURRENT_SLIDE_FLAT_INDEX]
    return gr.update(value=slide_content)


def next_slide():
    """Updates slide index and the content of the slide."""
    global CURRENT_SLIDE_FLAT_INDEX
    # Update current slide index.
    CURRENT_SLIDE_FLAT_INDEX = cap(CURRENT_SLIDE_FLAT_INDEX + 1)
    slide_content = SLIDE_CONTENTS[CURRENT_SLIDE_FLAT_INDEX]
    return gr.update(value=slide_content)


def cap(x):
    """Ensure value stays between 0 and a maximum value."""
    return min(max(x, 0), MAX_SLIDE_INDEX)


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


if __name__ == "__main__":
    chatbot_id = "mental_health"
    if len(sys.argv) == 2:
        chatbot_id = sys.argv[1]
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    e_health_course_prototype(chatbot_id)
