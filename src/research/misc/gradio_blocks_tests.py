# %%
import path_setup
import gradio as gr
import numpy as np
import os

# %%
slide_filenames = os.listdir("library")
slide_contents = []
for name in slide_filenames:
    full_path = os.path.join(os.path.abspath("library"), name)
    with open(full_path, "r") as file:
        slide_contents.append(file.read())

max_slide_index = len(slide_contents) - 1

# Initialize slide index
current_slide_index = 0


def next_slide():
    """Updates the text in the slide when the next button is clicked."""
    global current_slide_index
    current_slide_index = cap(current_slide_index + 1)
    return gr.update(value=slide_contents[current_slide_index])


def cap(x):
    return min(max(x, 0), max_slide_index)


# Function to update the info_text_box with the current slide content
def previous_slide():
    global current_slide_index
    current_slide_index = cap(current_slide_index - 1)
    return gr.update(value=slide_contents[current_slide_index])


def cap(x):
    return min(max(x, 0), max_slide_index)


# Function to handle the "Next" button click
def increase_slide_number():
    global current_slide_index
    current_slide_index = (current_slide_index + 1) % len(
        slide_contents
    )  # Loop back to the first slide if at the end
    print(current_slide_index)
    next_slide()


# Function to respond to user input (you can define your logic here)
def respond(user_message, chat):
    response = "Thats nice fag"
    chat.append((user_message, response))
    return user_message, chat


# Create the interface
with gr.Blocks() as demo:

    with gr.Row():

        # Column 1
        with gr.Column():
            info_text_box = gr.Markdown(slide_contents[current_slide_index])
            with gr.Row():
                back_button = gr.Button("Back")
                next_button = gr.Button("Next")
                back_button.click(previous_slide, outputs=[back_button, info_text_box])
                next_button.click(next_slide, outputs=[next_button, info_text_box])

        # Column 2
        with gr.Column():
            user_message = gr.Textbox(label="Input")
            chat = gr.Chatbot(label="Chat")

            user_message.submit(
                respond,
                inputs=[user_message, chat],
                outputs=[user_message, chat],
            )

    demo.launch()


# %%
import gradio as gr

# Define the text slides
slides = [
    "Slide 1: This is the content of slide 1.",
    "Slide 2: This is the content of slide 2.",
    "Slide 3: This is the content of slide 3.",
]


# Function to handle the "Next" button click
def increase_slide_number(button, slide_index):
    if button == "Next":
        slide_index = (slide_index + 1) % len(
            slides
        )  # Loop back to the first slide if at the end
    return slide_index, slides[slide_index]


# Dummy function that shows a state being updated
def update_string(s):
    s += "b"
    return s, s


def set_image(image_path):
    image_state.value = image_path


# Function to respond to user input (you can define your logic here)
def respond(user_message, chat, deep_chat):
    response = "Thats nice fag"
    chat.append((user_message, response))
    deep_chat.append([{"role": "system", "content": "New message"}])
    return user_message, chat, deep_chat


# Create the interface
with gr.Blocks() as demo:
    string_state = gr.State("0")
    image_url = gr.State("images/schizophrenia_genes_environment_interactions.png")
    slide_index = gr.State(0)  # Initialize slide index
    deep_chat = gr.State([[{"role": "system", "content": "Initial prompt"}]])

    with gr.Row():
        # Column 1
        with gr.Column(scale=0.5):
            string_state_text = gr.Markdown(string_state.value)
            info_text_box = gr.Markdown(slides[0])
            # info_text_box = gr.TextArea(slides[state_var.value])
            button = gr.Button("Next")
            button_update_state = gr.Button("Update and print state")
            image = gr.Image(value=image_url.value)

            button_image = gr.Button("Toggle image")

            button.click(
                increase_slide_number,
                inputs=[button, slide_index],
                outputs=[slide_index, info_text_box],
            )
            button_update_state.click(
                update_string,
                inputs=[string_state],
                outputs=[string_state, string_state_text],
            )

        # Column 2
        with gr.Column():
            user_message = gr.Textbox(label="Input")
            chat = gr.Chatbot(label="Abuse bot")
            user_message.submit(
                respond,
                inputs=[user_message, chat, deep_chat],
                outputs=[user_message, chat, deep_chat],
            )

demo.launch()

# %% UPDATE STATE VECTOR
import gradio as gr


def update_list(s, i, l):
    s += "b"
    i = i + 1
    l += "b"
    return s, i, l, s, i, l


def check_state(s, i, l):
    print(s)
    print(i)
    print(l)


with gr.Blocks() as demo:
    s = gr.State("a")
    i = gr.State(0)
    l = gr.State(["a"])

    text_s = gr.Textbox(value=s.value, label="State S")
    text_i = gr.Textbox(value=i.value, label="State I")
    text_l = gr.Textbox(value=l.value, label="State L")

    button = gr.Button("Update State")
    button_check_state = gr.Button("Print State")

    # Here, we connect the button click to the update_list function
    # And we also update the textbox values with the new state values
    button.click(
        update_list, inputs=[s, i, l], outputs=[s, i, l, text_s, text_i, text_l]
    )
    button_check_state.click(check_state, inputs=[s, i, l])

demo.launch()

# %% *** Toggle image ***


image_genes = "images/schizophrenia_genes_environment_interactions.png"
image_park = "images/patient_walking_in_pretty_park.png"

import gradio as gr
import time as time


def toggle_image(image_url, image_chat):
    if image_url == image_genes:
        image_url = image_park
    else:
        image_url = image_genes

    image = image_url
    # Here I want to update the chat with the new image
    image_chat.append((None, (image_url,)))

    return image_url, image_chat, image


def respond(user_message, surface_chat, image, image_chat):
    surface_chat.append((user_message, "Hi asshole"))
    if "park" in user_message:
        image = image_park
    elif "gene" in user_message:
        image = image_genes

    image_chat.append((None, (image,)))
    time.sleep(1)
    user_message = ""
    return user_message, surface_chat, image_url, image, image_chat


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=0.6):
            image_url = gr.State(image_genes)

            toggle_button = gr.Button("Update Image")
            image_chat = gr.Chatbot(height=500)

            image = gr.Image(value=image_url.value)

            toggle_button.click(
                toggle_image,
                inputs=[image_url, image_chat],
                outputs=[image_url, image_chat, image],
            )

        with gr.Column():
            user_message = gr.Textbox(label="Your message")
            surface_chat = gr.Chatbot(height=800)
            user_message.submit(
                respond,
                inputs=[user_message, surface_chat, image, image_chat],
                outputs=[user_message, surface_chat, image_url, image, image_chat],
            )


demo.launch()
