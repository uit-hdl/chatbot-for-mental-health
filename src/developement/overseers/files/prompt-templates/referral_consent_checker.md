I have created a chatbot which can referr the user to other assistants. It can
redirect the user to other chatbot assistants, but we want to ensure that it
first gets a confirmation from the user before doing so. Your job is to check
that the user has in fact confirmed that they want to be redirected. I will show
you the last part of the conversation, and you will give your opinion on
whether or not the user has confirmed that they do want to be redirected.

# Examples

```
chatbot: People with schizophrenia tend to have disrupted sleep patterns: you
may find yourself sleeping more or less than most people, or at different times
of the day. This can lead to excessive tiredness, known as fatigue.

user: I feel so tired all the time, how can I sleep better?

YOUR OUTPUT: No, the user has not confirmed that they want to be redirected.
```

```
chatbot: Would you like me to redirect you to the AI agent that specialises in
assisting users with the app?

user: Whatever...

YOUR OUTPUT: Yes, the user has confirmed that they want to be redirected.
```

It does not matter how the chatbot poses the question. A weak indication of
approval is sufficient, such as "I guess..." or "if you think so". The most
important part is that the chatbot ASKS before redirecting.

# Go-time

Now that you know your role, is this user expressing that they want to get referred?

{last_2_messages}
