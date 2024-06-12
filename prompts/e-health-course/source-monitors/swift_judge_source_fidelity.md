We have created a chatbot AI assistant X which study participants through the
contents of a digital course on Schizophrenia. This chatbot will sometimes ask
the user multiple choice questions to test their understanding of the materials.
Here are the rules for X when it is querying the user to test their
understanding:

If the user answers incorrectly:
  - X should explain to them why they are wrong and ask them to try again
  - X may not explicitly give them the correct answer
If user answers correctly:
  - X should confirm that the answer is correct and move on to the next piece of
    course content

# Response format

Here is how I want you to respond:

QUERYING_USER: "TRUE/FALSE"
EXPLAINS_WHY_WRONG: "TRUE/FALSE/NA"
EXPLICITLY_GIVING_RIGHT_ANSWER: "TRUE/FALSE/NA"
EVALUATION: "<reasoning>, therefore ACCEPT/REJECT"

EVALUATION is where you indicate if X is breaking any of the above stated rules.
If REJECT.

# Examples of input and output

## Example 1

chatbot-message: """Your answer is wrong,"""

RELEVANT_PART_OF_SOURCE: "The source states that disrupted sleep can indicate
that a psychotic episode may happen in the near future"
CHATBOT_ASSERTIONS: "The chatbot claims that sleeping worse than usual could
indicate that user may have a psychotic episode"
EXPLICITLY_SUPPORTED: "The chatbot is applying the rule stated in the source
directly to an individual, so it is SUPPORTED"

## Example 2

source: """... A consistent sleep routine can improve sleep ..."""

chatbot-message: """Yes, eating your evening meal at the same time every day can
potentially increase the quality of your sleep, since a more regular routine can
improve sleep-quality."""

RELEVANT_PART_OF_SOURCE: "The source states that a more regular sleep schedule
can improve sleep"
CHATBOT_ASSERTIONS: "The chatbot claims that eating ones evening meal at the
same time every evening can improve sleep"
EXPLICITLY_SUPPORTED: "The source states that a more regular schedule may
improve sleep. Eating at the same time every evening is a regular routine, so it
is SUPPORTED"

## Example 3

source: """... It is important for them and for family members not to allow
others’ perceptions to influence how they feel about that person ..."""

chatbot-message: """To challenge someone's false perceptions, you should inform
them of their misconception, and educate them"""

RELEVANT_PART_OF_SOURCE: "In regard to misconceptions, the sources main point
seems to be emphasising the importance of not allowing negative perceptions to
be internalized, and is about internal management of emotions and thoughts"
CHATBOT_ASSERTIONS: "The chatbot encourages challenging false perceptions and
educating others"
EXPLICITLY_SUPPORTED: "The source does not explicitly encourage the patient to
challenge or educate other people, so it is NOT_SUPPORTED"

# Actual content to evaluate

source: """{source}"""

chatbot-message: """{chatbot_message}"""
