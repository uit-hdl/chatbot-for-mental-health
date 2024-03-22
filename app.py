"""App for beta-testing on Hugging Face."""

import sys
import os

src_directory = os.getcwd() + "/src"
sys.path.append(src_directory)

import gradio as gr

from src.console_chat import PROMPTS
from src.console_chat import initiate_conversation_with_prompt
from src.console_chat import remove_inactive_sources
from src.console_chat import respond_to_user
from src.console_chat import dump_current_conversation_to_json
from src.console_chat import direct_to_new_assistant
from src.console_chat import truncate_if_too_long
from src.utils.general import remove_syntax_from_message
from src.utils.chat_utilities import grab_last_assistant_response

DEEP_CHAT = []


def chat_with_bot_in_gradio_interface(chatbot_id, server_port=None):
    """Launches a conversation with the mental health chatbot in Gradio interface.
    Intended to be used in Hugging Faces space."""
    global DEEP_CHAT
    DEEP_CHAT = initiate_conversation_with_prompt(
        PROMPTS[chatbot_id],
    )

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label="Your input")
        msg = gr.Textbox()

        msg.submit(respond, [msg, chatbot], [msg, chatbot])

    demo.launch(share=True, server_port=server_port)


def respond(user_message, surface_chat):
    global DEEP_CHAT
    DEEP_CHAT.append({"role": "user", "content": user_message})
    DEEP_CHAT, harvested_syntax = respond_to_user(DEEP_CHAT, "mental_health")
    raw_response = grab_last_assistant_response(DEEP_CHAT)
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_message, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    for image_url in image_url_list:
        surface_chat.append((None, (image_url,)))

    dump_current_conversation_to_json(DEEP_CHAT)

    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            assistant_name = harvested_syntax["referral"]["name"]
            DEEP_CHAT = direct_to_new_assistant(assistant_name)
            surface_response = grab_last_assistant_response(DEEP_CHAT)
            surface_chat.append((None, surface_response))

    DEEP_CHAT = remove_inactive_sources(DEEP_CHAT)
    DEEP_CHAT = truncate_if_too_long(DEEP_CHAT)
    return "", surface_chat


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


chat_with_bot_in_gradio_interface("mental_health")
