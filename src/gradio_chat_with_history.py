"""Rudimentary gradio interface chat."""
import sys

from utils.backend import PROMPTS
from utils.general import remove_syntax_from_message
from utils.chat_utilities import grab_last_response
from console_chat import generate_processed_bot_response
from console_chat import direct_to_new_assistant
from console_chat import remove_inactive_sources
import gradio as gr

DEEP_CHAT = []


def chat_with_bot_in_gradio_interface(chatbot_id):
    """Chat with the chatbot in gradio interface. Click on one of the urls that appear in the
    console to start the conversation in a browser window. Has all features (referrals, show image,
    etc...) EXCEPT play videos (ATM)."""
    global DEEP_CHAT

    DEEP_CHAT.append(
        {
            "role": "system",
            "content": PROMPTS[chatbot_id],
        }
    )

    iface = gr.ChatInterface(fn=chatbot_interface)
    iface.launch(share=True)


def chatbot_interface(user_message, printed_history: [list, list]) -> str:
    """Function that goes into gradio interface function. Maps input text to final chatbot
    response and image url (after processing bot commands, gathering pictures, updating chat
    history, etc...)."""
    global DEEP_CHAT

    DEEP_CHAT.append({"role": "user", "content": user_message})
    DEEP_CHAT, harvested_syntax = generate_processed_bot_response(
        DEEP_CHAT, chatbot_id=chatbot_id
    )
    DEEP_CHAT = remove_inactive_sources(DEEP_CHAT)
    
    if harvested_syntax["referral"]:
        if harvested_syntax["referral"]["file_exists"]:
            DEEP_CHAT = direct_to_new_assistant(harvested_syntax["referral"])
            
    response = grab_last_response(DEEP_CHAT)
    response_final = remove_syntax_from_message(response)

    return response_final


if __name__ == "__main__":
    chatbot_id = "referral"
    if len(sys.argv) > 1:
        chatbot_id = sys.argv[1]
    chat_with_bot_in_gradio_interface(chatbot_id)
