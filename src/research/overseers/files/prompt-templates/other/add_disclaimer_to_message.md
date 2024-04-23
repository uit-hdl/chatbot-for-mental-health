I am designing a chatbot that attempts to answer user questions by requesting
sections from a manual on Schizophrenia, and then using that information as a
**source** to answer the question. In this case, the chatbot has produced a
response which has been flagged by an AI agent for overstepping its bounds and
making claims which the sources do not support. Your job is to correct the
chatbots message by prepending it with a cautionary disclaimer. For example, if
the chatbot says "Lean protein is a particularly good choice" and the oversser
AI flags this statement as un-supported, then you would modify that sentence to:

"Pleas note that the advice I am about to give contains information that is not
directly based on my sources, so please verify this information with your health-care provider.".

chatbot: "{chatbot_message}"

overseer: "{warning_message}"
