"""Rudimentary gradio interface chat."""
import sys

from typing import Tuple
from utils.backend import PROMPTS
from utils.backend import dump_current_conversation
from utils.general import remove_syntax_from_message
from utils.chat_utilities import grab_last_assistant_response
from console_chat import generate_processed_bot_response
from console_chat import direct_to_new_assistant
from console_chat import remove_inactive_sources
from console_chat import check_sources
import gradio as gr

CONVERSATION = []


def chat_with_bot_in_gradio_interface(chatbot_id):
    """Chat with the chatbot in gradio interface. Click on one of the urls that appear in the
    console to start the conversation in a browser window. Has all features (referrals, show image,
    etc...) EXCEPT play videos (ATM)."""
    global CONVERSATION

    prompt = PROMPTS[chatbot_id]

    CONVERSATION.append(
        {
            "role": "system",
            "content": prompt,
        }
    )

    iface = gr.Interface(fn=chatbot_interface, inputs="text", outputs=["text", "image"])
    iface.launch(share=True)


def chatbot_interface(user_input: str) -> Tuple[str, str]:
    """Function that goes into gradio interface function. Maps input text to final chatbot
    response and image url (after processing bot commands, gathering pictures, updating chat
    history, etc...)."""
    global CONVERSATION
    # Your chatbot logic to update message history and generate response
    CONVERSATION.append({"role": "user", "content": user_input})
    CONVERSATION, harvested_syntax = generate_processed_bot_response(
        CONVERSATION, chatbot_id=chatbot_id
    )
    image_url = get_image_url(harvested_syntax)

    CONVERSATION = remove_inactive_sources(CONVERSATION)
    CONVERSATION = check_sources(
        CONVERSATION, harvested_syntax, chatbot_id
    )
    dump_current_conversation(CONVERSATION)

    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            CONVERSATION = direct_to_new_assistant(harvested_syntax["referral"])

    response = grab_last_assistant_response(CONVERSATION)
    response_no_syntax = remove_syntax_from_message(response)
    return response_no_syntax, image_url


def get_image_url(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url = None
    for image in harvested_syntax["images"]:
        image_url = image["path"]
    return image_url


if __name__ == "__main__":
    chatbot_id = "referral"
    if len(sys.argv) > 1:
        chatbot_id = sys.argv[1]
    chat_with_bot_in_gradio_interface(chatbot_id)
