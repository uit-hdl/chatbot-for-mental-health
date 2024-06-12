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
from utils.backend import SETTINGS
from utils.chat_utilities import grab_last_assistant_response

CHATBOT_PASSWORD = os.environ["CHATBOT_PASSWORD"]
DEEP_CHAT = []


def chat_with_bot_in_gradio_interface(chatbot_id, server_port=None):
    """Allows you to have a conversation with the chatbot in a gradio
    interface. racks two versions of the chat in parallell. DEEP_CHAT contains
    the raw conversation history, including system messages and raw chatbot
    responses which commands intended for backend interpretation. The
    surface_chat is the representation of the chat which is seen by the user and
    presented in the gradio interface."""
    global DEEP_CHAT

    def initiate_new_chat():
        reset_files_that_track_cumulative_variables()
        return initiate_conversation_with_prompt(
            PROMPTS[chatbot_id],
        )

    def respond(user_text, surface_chat, image_window):
        """Updates the surface chat by generating and adding chatbot response."""
        user_text, surface_chat, image_window = create_response(
            user_text, surface_chat, chatbot_id, image_window
        )
        return user_text, surface_chat, image_window

    def reset_conversation():
        """Function that gets called when 'Reset conversation' button gets
        clicked."""
        global DEEP_CHAT
        DEEP_CHAT = initiate_new_chat()
        return "", []

    def authenticate(password):
        """Function to authenticate the user."""
        if (
            SETTINGS["gradio_password_disabled"] or password == CHATBOT_PASSWORD
        ):  # Hardcoded password for demonstration
            return gr.update(visible=False), gr.update(visible=True), ""
        else:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(value="Wrong password, please try again.", visible=True),
            )

    DEEP_CHAT = initiate_new_chat()

    with gr.Blocks() as demo:
        # Password authentification
        with gr.Column(visible=True) as auth_interface:
            password_input = gr.Textbox(label="Enter Password")
            auth_button = gr.Button("Submit")
            error_message = gr.Label(value="", visible=False, label="")

        # Chatbot interface (initially hidden)
        with gr.Row(visible=False, elem_id="chat_interface") as chat_interface:

            # Left column with images
            with gr.Column(scale=0.5):
                # Window that shows history of dispayed images
                reset_button = gr.Button("Restart conversation")
                image_window = gr.Chatbot(height=600, label="Images")
                reset_button.click(
                    reset_conversation,
                    inputs=[],
                    outputs=[auth_interface, chat_interface, error_message],
                )

            # Right column with chat window
            with gr.Column():
                user_message = gr.Textbox(label="Enter message and hit enter")
                surface_chat = gr.Chatbot(label="Chat", height=650)
                user_message.submit(
                    respond,
                    inputs=[user_message, surface_chat, image_window],
                    outputs=[user_message, surface_chat, image_window],
                )

        auth_button.click(
            authenticate,
            inputs=[password_input],
            outputs=[auth_interface, chat_interface, error_message],
        )

    demo.launch(share=True, server_port=server_port)


def create_response(user_text, surface_chat, chatbot_id, image_window):
    """Returns a tuple: ("", surface_chat). The surface chat has been updated
    with a response from the chatbot."""
    global DEEP_CHAT
    DEEP_CHAT.append({"role": "user", "content": user_text})
    DEEP_CHAT, harvested_syntax = respond_to_user(DEEP_CHAT, chatbot_id)
    raw_response = grab_last_assistant_response(DEEP_CHAT)
    surface_response = remove_syntax_from_message(raw_response)

    surface_chat.append((user_text, surface_response))

    image_url_list = get_image_urls(harvested_syntax)
    if image_url_list:
        image_url = image_url_list[0]
        image_window.append((None, (image_url,)))

    dump_current_conversation_to_json(DEEP_CHAT)

    if harvested_syntax["referral"]:
        assistant_name = harvested_syntax["referral"]["name"]
        DEEP_CHAT = direct_to_new_assistant(assistant_name)
        surface_response = grab_last_assistant_response(DEEP_CHAT)
        surface_response_no_syntax = remove_syntax_from_message(surface_response)
        surface_chat.append((None, surface_response_no_syntax))

    DEEP_CHAT = remove_inactive_sources(DEEP_CHAT)
    DEEP_CHAT = truncate_if_too_long(DEEP_CHAT)

    return "", surface_chat, image_window


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


if __name__ == "__main__":
    chatbot_id = "mental_health"
    if len(sys.argv) == 2:
        chatbot_id = sys.argv[1]
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    chat_with_bot_in_gradio_interface(chatbot_id)
