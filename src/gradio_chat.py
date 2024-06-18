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
from utils.chat_utilities import generate_and_add_raw_bot_response

CHATBOT_PASSWORD = os.environ["CHATBOT_PASSWORD"]


def chat_with_bot_in_gradio_interface(server_port=None):
    """Allows you to have a conversation with the chatbot in a gradio
    interface. racks two versions of the chat in parallell. DEEP_CHAT contains
    the raw conversation history, including system messages and raw chatbot
    responses which commands intended for backend interpretation. The
    surface_chat is the representation of the chat which is seen by the user and
    presented in the gradio interface."""

    def initiate_new_chat(chatbot_id):
        reset_files_that_track_cumulative_variables()
        deep_chat = initiate_conversation_with_prompt(
            PROMPTS[chatbot_id],
        )
        return deep_chat

    def respond(user_message, deep_chat, surface_chat, chatbot_id, image_window):
        """Updates the surface chat by generating and adding chatbot response."""
        user_message, deep_chat, surface_chat, image_window = create_response(
            user_message, deep_chat, surface_chat, chatbot_id, image_window
        )
        return user_message, deep_chat, surface_chat, chatbot_id, image_window

    def reset_conversation(deep_chat, chatbot_id):
        """Function that gets called when 'Reset conversation' button gets
        clicked."""
        deep_chat = initiate_new_chat(chatbot_id)
        surface_chat = []
        return surface_chat, deep_chat

    with gr.Blocks() as demo:
        # Initiate chat
        chatbot_id = gr.State(value="mental_health")
        deep_chat = gr.State(initiate_conversation_with_prompt(chatbot_id.value))

        # Password authentification & chatbot selection
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

        # Chatbot interface (initially hidden)
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

        reset_button.click(
            reset_conversation,
            inputs=[deep_chat, chatbot_id],
            outputs=[surface_chat, deep_chat],
        )

        # Authentfication click
        @auth_button.click(
            inputs=[password, chatbot_selection],
            outputs=[
                auth_interface,
                chat_interface,
                wrong_password_message,
                deep_chat,
                chatbot_id,
            ],
        )
        def authenticate(password, chatbot_selection):
            """Function to authenticate the user."""
            if (
                SETTINGS["gradio_password_disabled"] or password == CHATBOT_PASSWORD
            ):  # Password correct
                auth_interface = gr.update(visible=False)
                chat_interface = gr.update(visible=True)
                wrong_password_message = gr.update(visible=False)
            else:
                # Password incorrect
                auth_interface = gr.update(visible=True)
                chat_interface = gr.update(visible=False)
                wrong_password_message = gr.update(visible=True)

            if chatbot_selection == "Schizophrenia":
                chatbot_id = "mental_health"
            else:
                chatbot_id = "ehealth_module1"
            deep_chat = initiate_new_chat(chatbot_id)

            return (
                auth_interface,
                chat_interface,
                wrong_password_message,
                deep_chat,
                chatbot_id,
            )

    demo.launch(share=True)


def create_response(user_message, deep_chat, surface_chat, chatbot_id, image_window):
    """Returns a tuple: ("", surface_chat). The surface chat has been updated
    with a response from the chatbot."""

    deep_chat.append({"role": "user", "content": user_message})
    deep_chat, harvested_syntax = respond_to_user(deep_chat, chatbot_id)
    raw_response = grab_last_assistant_response(deep_chat)
    surface_response = remove_syntax_from_message(raw_response)

    image_url_list = get_image_urls(harvested_syntax)
    if image_url_list:
        image_url = image_url_list[0]
        # The image window is a chatbot component where there is no user inputs.
        image_window.append((None, (image_url,)))

    dump_current_conversation_to_json(deep_chat)

    if harvested_syntax["referral"]:
        chatbot_id = harvested_syntax["referral"]["name"]
        deep_chat = direct_to_new_assistant(chatbot_id)
        deep_chat = generate_and_add_raw_bot_response(deep_chat)
        surface_response = remove_syntax_from_message(
            grab_last_assistant_response(deep_chat)
        )

    deep_chat = remove_inactive_sources(deep_chat)
    deep_chat = truncate_if_too_long(deep_chat)

    # Update surface chat and refresh text-input window
    surface_chat.append((user_message, surface_response))
    user_message = ""

    return user_message, deep_chat, surface_chat, image_window


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
