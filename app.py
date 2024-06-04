"""Script for doing E-health course in gradio chatbot interface."""
from fastapi import FastAPI
import gradio as gr
import os
import sys
from dotenv import load_dotenv
load_dotenv()

src_directory = os.getcwd() + "/src"
sys.path.append(src_directory)

from src.gradio_chat_with_history_and_images import (
    chat_with_bot_in_gradio_interface,
)

app = chat_with_bot_in_gradio_interface(chatbot_id="ehealth_module1", server_port=8000) #gr.mount_gradio_app(app, chat_with_bot_in_gradio_interface(chatbot_id="ehealth_module1"), path="/src")

# chat_with_bot_in_gradio_interface(chatbot_id="ehealth_module1").launch(share=True, server_port=8080)
