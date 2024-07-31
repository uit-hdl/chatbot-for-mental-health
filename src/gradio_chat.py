import gradio as gr
import os

from console_chat import collect_prompts_in_dictionary
from console_chat import initiate_conversation_with_prompt
from console_chat import remove_inactive_sources
from console_chat import respond_to_user
from console_chat import dump_current_conversation_to_json
from console_chat import direct_to_new_assistant
from console_chat import truncate_if_too_long
from utils.general import remove_syntax_from_message
from utils.backend import reset_files_that_track_cumulative_variables
from utils.backend import MISC_CONFIG
from utils.chat_utilities import grab_last_assistant_response
from utils.chat_utilities import generate_and_add_raw_bot_response

CHATBOT_PASSWORD = os.environ["CHATBOT_PASSWORD"]

CHAT_WINDOW_HEIGHT = 750
IMAGES_WINDOW_HEIGHT = 650
IMAGES_WINDOW_SCALE = 0.7
RESET_BUTTON_SCALE = 0.05


def chat_with_bot_in_gradio_interface():
    """Allows you to have a conversation with the chatbot in a gradio
    interface. racks two versions of the chat in parallell. DEEP_CHAT contains
    the raw conversation history, including system messages and raw chatbot
    responses which commands intended for backend interpretation. The
    surface_chat is the representation of the chat which is seen by the user and
    presented in the gradio interface."""

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
            with gr.Column(scale=IMAGES_WINDOW_SCALE):
                # Window that shows history of dispayed images
                image_window = gr.Chatbot(height=IMAGES_WINDOW_HEIGHT, label="Images")
                with gr.Row():
                    # Create row to place them side-by-side
                    reset_button = gr.Button(
                        "Restart conversation", scale=RESET_BUTTON_SCALE
                    )
                    user_message = gr.Textbox(label="Enter message and hit enter")

            # Right column with chat window
            with gr.Column():
                surface_chat = gr.Chatbot(height=CHAT_WINDOW_HEIGHT, label="Chat")

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

    demo.launch(share=True)


def authenticate(password, chatbot_selection):
    """Function run when user clicks "submit" on screen 1. Checks
    authentification attempt and chatbot selection."""
    if (
        MISC_CONFIG["gradio_password_disabled"] or password == CHATBOT_PASSWORD
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


def respond(user_message, deep_chat, surface_chat, chatbot_id, image_window):
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

    dump_current_conversation_to_json(deep_chat, also_dump_formatted=True)

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

    return user_message, deep_chat, surface_chat, chatbot_id, image_window


def initiate_new_chat(chatbot_id):
    """Initiates new chat object by using the chatbot ID to fetch the associated
    prompt."""
    reset_files_that_track_cumulative_variables()
    prompt = collect_prompts_in_dictionary(chatbot_id)[chatbot_id]
    deep_chat = initiate_conversation_with_prompt(prompt)
    return deep_chat


def reset_conversation(deep_chat, chatbot_id):
    """Function that gets called when 'Reset conversation' button gets
    clicked."""
    deep_chat = initiate_new_chat(chatbot_id)
    surface_chat = []
    return surface_chat, deep_chat


def get_image_urls(harvested_syntax):
    """Gets the path of the image that the bot is trying to show (if any)."""
    image_url_list = []
    for image in harvested_syntax["images"]:
        image_url_list.append(image["path"])
    return image_url_list


if __name__ == "__main__":
    chat_with_bot_in_gradio_interface()
