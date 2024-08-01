"""Script for doing E-health course in gradio chatbot interface. This script has
to be here in order for the Azure app to function."""

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
from src.utils.backend import dump_chat_to_dashboard
from src.utils.chat_utilities import initiate_conversation_with_prompt
from src.utils.chat_utilities import grab_last_assistant_response
from src.utils.chat_utilities import re
from src.gradio_chat import authenticate, initiate_new_chat, respond, reset_conversation


app = FastAPI()

with gr.Blocks() as demo:
    # Initiate state variables
    chatbot_id = gr.State(value="mental_health")
    deep_chat = gr.State(initiate_new_chat(chatbot_id.value))

    # ** Password authentification & chatbot selection screen **
    with gr.Column(visible=True) as auth_interface:
        password = gr.Textbox(label="Enter Password")
        chatbot_selection = gr.Radio(
            choices=["Schizophrenia", "E-health course"],
            label="Select Chatbot",
            value="Schizophrenia",
        )
        auth_button = gr.Button("Submit")
        wrong_password_message = gr.Label(
            value="Wrong password, try again", visible=False, label=""
        )

    # ** Chatbot interface - revealed after authentification **
    with gr.Row(visible=False) as chat_interface:

        # Left column with images
        with gr.Column(scale=0.7):
            # Window that shows history of dispayed images
            image_window = gr.Chatbot(height=500, label="Images")
            with gr.Row():
                # Create row to place them side-by-side
                reset_button = gr.Button("Restart conversation", scale=0.20)
                user_message = gr.Textbox(label="Enter message and hit enter")

        # Right column with chat window
        with gr.Column():
            surface_chat = gr.Chatbot(height=600, label="Chat")

    # ** Clicks **
    # Authentfication click
    auth_button.click(
        authenticate,
        inputs=[password, chatbot_selection],
        outputs=[
            auth_interface,
            chat_interface,
            wrong_password_message,
            deep_chat,
            chatbot_id,
        ],
    )
    # Submitting user message
    user_message.submit(
        respond,
        inputs=[
            user_message,
            deep_chat,
            surface_chat,
            chatbot_id,
            image_window,
        ],
        outputs=[
            user_message,
            deep_chat,
            surface_chat,
            chatbot_id,
            image_window,
        ],
    )
    # Resetting chat
    reset_button.click(
        reset_conversation,
        inputs=[deep_chat, chatbot_id],
        outputs=[surface_chat, deep_chat],
    )

app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
