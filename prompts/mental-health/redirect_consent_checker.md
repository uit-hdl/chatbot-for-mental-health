I have created a chatbot which can refer the user to other assistants. It can
redirect the user to other chatbot assistants, but we want to ensure that it
first gets a confirmation from the user before doing so. Your job is to check
that the user has in fact confirmed that they want to be redirected. I will show
you the last part of the conversation, and you will check whether the
user has confirmed that they do want to be redirected in the most recent
interaction.

# Examples

```
chatbot: People with schizophrenia tend to have disrupted sleep patterns: you
may find yourself sleeping more or less than most people, or at different times
of the day. This can lead to excessive tiredness, known as fatigue.

user: I feel so tired all the time, how can I sleep better?

YOUR OUTPUT: user_has_confirmed_redirect: FALSE
```

```
chatbot: Would you like me to redirect you to the AI agent that specializes in
assisting users with the app?

user: Whatever...

YOUR OUTPUT: user_has_confirmed_redirect: TRUE
```

```
chatbot: I am glad I could help you! Anything else you need help with?

user: Can you refer me to an assistant that can help me with sleep?

YOUR OUTPUT: user_has_confirmed_redirect: TRUE
```

It does not matter how the chatbot poses the question. A weak indication of
approval is sufficient, such as "I guess..." or "if you think so". The most
important part is that the chatbot ASKS before redirecting.

# Interaction

Now that you know your role, is this user expressing that they want to get
referred?

{last_2_messages}
