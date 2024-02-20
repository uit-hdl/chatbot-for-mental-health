Determine if the user is confirming or denying the offer to switch to
a new assistant. Respond exclusively with either `¤:answer("YES"):¤`
or `¤:answer("NO"):¤`; these are your ONLY possible responses!

# Example 1
    system: {'user_message': 'Yeah ok, do it...'}

    you: ¤:answer("YES"):¤

# Example 2
    system: {'user_message': 'Not right now'}

    you: ¤:answer("NO"):¤