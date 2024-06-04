# %%
import path_setup
import gradio as gr
import numpy as np
import os


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
                back_button.click(previous_slide, outputs=info_text_box)
                next_button.click(next_slide, outputs=info_text_box)

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

slide_contents = [
    "Slide 1: This is the content of slide 1.",
    "Slide 2: This is the content of slide 2.",
    "Slide 3: This is the content of slide 3.",
]
current_slide_index = 0

# What functions do I need here?

with gr.Blocks() as demo:

    with gr.Row():
        gr.Text()
        info_text_box = gr.Markdown(
            slide_contents[current_slide_index]
        )  # Text to be updated when I click next
        button = gr.Button("Next")
        button.click()  # What should be arguments here?
    demo.launch()

# %%
with gr.Blocks():
    with gr.Group():
        gr.Textbox(label="First")
        gr.Textbox(label="Last")
    demo.launch()
