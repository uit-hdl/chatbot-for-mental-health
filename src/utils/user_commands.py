import numpy as np
import logging
import os

from utils.general import grab_last_response
from utils.general import count_tokens
from utils.general import print_whole_conversation
from utils.general import offer_to_store_conversation

logging.basicConfig(
    filename="log/chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def scan_user_message_for_commands(
    user_message,
    conversation,
    break_conversation
):
    """Scans user input for commands, allowing them to execute commands from the command line during
    a chat to receive diagnostic information or perform other actions without interrupting the
    chat."""
    global GRAB_LAST_RESPONSE, SUMMARY, N_TOKENS_USED, RESPONSE_TIMES
    
    n_rewind = None
    commands = [
        "options",
        "break",
        "count_tokens",
        "count_words",
        "calc_cost",
        "print_response",
        "print_response_times",
        "print_last3",
        "print_chat",
        "print_prompt",
        "print_summary",
        "rewind_by1",
        "rewind_by2",
        "rewind_by3",
        "rewind_by4",
        "clear",
        "history",
        "log",
        "store_chat"
    ]

    while user_message in commands:
        if user_message == "break":
            break_conversation = True
            break

        elif user_message == "options":
            print(f"Possible commands are {commands}")

        elif user_message == "count_tokens":
            print(f"The number of tokens used is: {np.sum(np.array(N_TOKENS_USED))}")

        elif user_message == "calc_cost":
            print(
                f"The number of tokens is: {count_tokens(conversation)*.0003246:.3} kr"
            )

        elif user_message == "print_response":
            print(grab_last_response(conversation))

        elif user_message == "print_response_times":
            print(
                f"Response_times:{RESPONSE_TIMES} ({np.sum(np.array(RESPONSE_TIMES)):.4}s total)"
            )

        elif user_message == "print_prompt":
            print(f"The system prompt is: \n\n{conversation[0]['content']}")

        elif user_message == "print_last3":
            print("\n*** Printing last 3 messages... ***")
            print(f"The last 3 messages are: \n\n{conversation[-3:]}")
            print("*** End of printing last 3 messages ***\n")

        elif user_message == "print_chat":
            print("\n*** Printing whole chat... ***")
            print_whole_conversation(conversation)
            print("*** End of printing whole chat ***\n")

        elif user_message == "print_summary":
            print(f"\n{SUMMARY}")

        elif user_message == "clear":
            os.system("clear")

        elif user_message == "history":
            print_whole_conversation(conversation)
            
        elif user_message == "store_chat":
            offer_to_store_conversation(conversation)

        elif user_message == "log":
            response_times_rounded = [np.round(t, 4) for t in RESPONSE_TIMES]
            time_total = np.sum(np.array(RESPONSE_TIMES))
            tokens_total = np.sum(np.array(N_TOKENS_USED))
            logging.info(
                f"\nResponse times: {response_times_rounded} ({time_total:.4}s total)"
            )
            logging.info(f"Tokens used: {N_TOKENS_USED} ({tokens_total} total)")

        elif "rewind_by" in user_message:
            n_rewind = int(user_message[-1])
            print(n_rewind)
            break

        user_message = input("user: ")

    return user_message, n_rewind, break_conversation
