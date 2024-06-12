"""Script for doing E-health course in gradio chatbot interface."""

import os
import sys

src_directory = os.getcwd() + "/src"
sys.path.append(src_directory)

from src.gradio_chat_with_history_and_images import (
    chat_with_bot_in_gradio_interface,
)

chat_with_bot_in_gradio_interface(chatbot_id="mental_health")
