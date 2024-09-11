We have created a chatbot assistant X which conveys the contents of a manual
about Schizophrenia; what it is, and how to manage it. We want X to only say
things that are explicitly said or implied by this manual (paraphrasing is
allowed), i.e. faithfull conveying the materials without adding assertions that
are not explicitly supported by the source. X may explain, interpret, and
rephrase in order to help the patient understand the content.

First, list concisely the assertions made by X as concisely as you can. Then,
compare these assertions to the content of the source, and evaluate if X making
any assertions that are not explicitly stated in the in the source. Note that X
is not allowed to assume external knowledge, so it does not matter if the
assertions are generally accepted. For example, "Going for a walk can improve
your mood" is commonly accepted advice, but it is not supported unless the
source actually expresses this recomendation.

End your response with either "SUPPORTED" (meaning all assertions are explicitly
supported) or "NOT_SUPPORTED"

# Content to evaluate

source: """{source}"""

chatbot-message: """{chatbot_message}"""
