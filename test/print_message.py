import textwrap

def wrap_and_print_message(role, message, line_length=80):
    paragraphs = message.split('\n\n')  # Split message into paragraphs
    
    for i, paragraph in enumerate(paragraphs):
        lines = paragraph.split('\n')  # Split each paragraph into lines
        wrapped_lines = []
        for line in lines:
            wrapped_line = '\n'.join(textwrap.wrap(line, line_length))
            wrapped_lines.append(wrapped_line)
        
        formatted_paragraph = '\n'.join(wrapped_lines)

        if i == 0:
            formatted_message = f'\n{role}: {formatted_paragraph}\n'
        else:
            formatted_message = f'{formatted_paragraph}\n'
    
        print(formatted_message)

role = "Assistant"
message = "Simple message. \n\n with some more info\n and some new lines"
wrap_and_print_message(role, message)