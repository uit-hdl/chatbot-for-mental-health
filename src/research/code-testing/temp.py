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
def increase_slide_number(button, slide_index, state_var):
    if button == "Next":
        slide_index = (slide_index + 1) % len(
            slides
        )  # Loop back to the first slide if at the end
        state_var = state_var + 1
    return slide_index, slides[slide_index], state_var


# Function to respond to user input (you can define your logic here)
def respond(user_message):
    return "Chatbot response: Thanks for your input - " + user_message


# Create the interface
with gr.Blocks() as demo:
    slide_index = gr.State(0)  # Initialize slide index
    state_var = gr.State(0)  # Initialize slide index

    with gr.Row():
        # Column 1
        with gr.Column():
            info_text_box = gr.Markdown(slides[0])
            info_text_box = gr.TextArea(slides[state_var.value])
            button = gr.Button("Next")
            button.click(
                increase_slide_number,
                inputs=[button, slide_index, state_var],
                outputs=[slide_index, info_text_box, state_var],
            )

        # Column 2
        with gr.Column():
            user_message = gr.Textbox(label="Input")
            chat = gr.Chatbot(label="Chat")
            user_message.submit(
                respond,
                inputs=[user_message],
                outputs=[chat],
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

# Initialize slide index
current_slide_index = 0


# Function to update the text with the current slide content
def update_text(button, global_text_variable):
    global current_slide_index
    if button == "Next":
        current_slide_index = (current_slide_index + 1) % len(slides)
    elif button == "Back":
        current_slide_index = (current_slide_index - 1) % len(slides)
    global_text_variable = global_text_variable + "a"
    print(global_text_variable)
    return slides[current_slide_index], gr.update(global_text_variable)


# Create the interface
with gr.Blocks() as demo:
    global_text_variable = gr.State("abc")
    x = gr.State(1)

    with gr.Row():
        # Column 1
        with gr.Column():
            text_box = gr.Textbox(
                slides[current_slide_index], label=global_text_variable.value
            )

            next_button = gr.Button("Next")
            next_button.click(
                update_text,
                inputs=[next_button, global_text_variable],
                outputs=[text_box, global_text_variable],
            )

            back_button = gr.Button("Back")
            back_button.click(
                update_text,
                inputs=[back_button, global_text_variable],
                outputs=[back_button, global_text_variable],
            )

demo.launch()
