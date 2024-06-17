"""Script for doing E-health course in gradio chatbot interface."""

import os
import sys
from fastapi import FastAPI
import gradio as gr

src_directory = os.getcwd() + "/src"
sys.path.append(src_directory)

from src.console_chat import direct_to_new_assistant
from src.utils.general import remove_syntax_from_message
from src.utils.managing_sources import remove_inactive_sources
from src.utils.manage_chat_length import truncate_if_too_long
from src.utils.backend import reset_files_that_track_cumulative_variables
from src.utils.backend import dump_current_conversation_to_json
from src.utils.chat_utilities import initiate_conversation_with_prompt
from src.utils.chat_utilities import grab_last_assistant_response
from src.utils.chat_utilities import re
from src.gradio_chat_with_history_and_images import (
    respond_to_user,
    PROMPTS,
    CHATBOT_PASSWORD,
    initiate_conversation_with_prompt,
    get_image_urls,
    create_response
)


app = FastAPI()


chatbot_id = "ehealth_module1"
DEEP_CHAT = []


def initiate_new_chat():
    reset_files_that_track_cumulative_variables()
    return initiate_conversation_with_prompt(
        PROMPTS[chatbot_id],
    )


def respond(user_message, surface_chat):
    """Updates the surface chat by generating and adding chatbot response."""
    user_message, surface_chat = create_response(user_message, surface_chat, chatbot_id)
    return user_message, surface_chat


def reset_conversation():
    """Function that gets called when 'Reset conversation' button gets
    clicked."""
    global DEEP_CHAT
    DEEP_CHAT = initiate_new_chat()
    return "", []


def authenticate(password):
    """Function to authenticate the user."""
    if password == CHATBOT_PASSWORD:  # Hardcoded password for demonstration
        return gr.update(visible=False), gr.update(visible=True), ""
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value="Wrong password, please try again.", visible=True),
        )


with gr.Blocks() as demo:
    with gr.Column(visible=True) as auth_interface:
        password_input = gr.Textbox(label="Enter Password")
        auth_button = gr.Button("Submit")
        error_message = gr.Label(value="", visible=False, label="")

    # Chatbot interface (initially hidden)
    with gr.Column(visible=False, elem_id="chat_interface") as chat_interface:
        surface_chat = gr.Chatbot(label="Your input")
        user_message = gr.Textbox(label="Enter message and hit enter")
        reset_button = gr.Button("Restart conversation")

        user_message.submit(
            respond,
            inputs=[user_message, surface_chat],
            outputs=[user_message, surface_chat],
        )
        reset_button.click(
            reset_conversation,
            inputs=[],
            outputs=[auth_interface, chat_interface, error_message],
        )

    auth_button.click(
        authenticate,
        inputs=[password_input],
        outputs=[auth_interface, chat_interface, error_message],
    )


app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
