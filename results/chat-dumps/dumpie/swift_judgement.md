
input: Your job is to judge the source fidelity of a message produced by a
chatbot, which I will call `X`. The job of X is to guide the user
through the contents of a manual on topics related to Schizophrenia.
We want X to only say things that are explicitly said or implied by
this manual (paraphrasing is allowed). X is also allowed to advice
talking to a professional, or also query the user. 

When X is communicating a source, it sometimes adds non-supported
claims or advice, and we want to avoid this over-reach! Essentially,
your job is to provide feedback that ensures that X completely
respects the boundaries of its source materials.

Here are the evaluations that you can give to the chatbot message:

1. "ACCEPTED" (message is completely supported by the source; every
   single sentence has a corresponding paragraph or sentence that
   supports it)
2. "WARNING" (message is mostly supported, but some claims are not
   supported by the source)
3. "REJECTED" (X makes claims not supported by the source, and
   gives no warning to the user that it is giving advice or claims
   that are not supported by the source.)

In case of "grey-areas", it is better to be too strict rather than too
lenient! However, do not be too picky about exact wording; focus on
the content. Report your assessment simply using this EXACT syntax:

`¤:provide_feedback({"evaluation": <category>}):¤`

# Examples of input and output 

## Example 1 

chatbot_message("If your sleep is worse than usual, this could mean
you are heading towards a psychotic episode.")

source("... Disrupted sleep patterns in schizophrenia may indicate an
impending psychotic episode...")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 2

chatbot_message("Yes, eating your evening meal at the same time every
day can increase the quality of your sleep.")

source("... A consistent sleep routine can improve sleep...")

¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

## Example 3

chatbot_message("To challenge someone's false perceptions, you should
inform them of their misconception, and educate them.")

source("... It is important for them and for family members not to
allow others’ perceptions to influence how they feel about that person
...")

¤:provide_feedback({"evaluation": "REJECTED"}):¤

chatbot_message(" Here are some communication strategies and tips for discussing schizophrenia:

1. Learn more about schizophrenia: Educate yourself about the condition so you can explain it clearly to friends and family.
[display image | `communication_education.png`]

2. Be honest: Share your personal experiences with schizophrenia, including your fears and hopes. Authenticity can change perceptions.

3. Set boundaries: Communicate your preferences on how others can help and what might not be helpful.

4. Build trust: Show trust in your family and friends' support, and demonstrate that the individual's best interests are a priority.

5. Don't be ashamed: Remember that having schizophrenia is not your fault, and there's no shame in it or in caring for someone with schizophrenia.

6. Learn from others: Join support groups to share experiences and strategies with others who understand your situation.

Following these steps can help reduce stigma and enhance understanding. Support groups provide a safe space where you can gain valuable insights from others who have similar experiences. Do you need assistance finding a support group or more educational resources?")

source("Schizophrenia is not easy to live with. It can put strain on your
relationships with people in your family or those you share a home
with. During relapses in your illness, you may not realize the demands
that are being made of people around you; when you emerge into
recovery, you may find yourself feeling rather lonely. Likewise, it
can be difficult to live with a person with schizophrenia.
Nevertheless, there are some practical steps you can take together to
make things easier.

# Planning a family

[QUERY FOR RELEVANCE] If you are planning a family, there are a number
of issues that you need to discuss with your partner early on, such as
the risk of your child developing schizophrenia, how you will manage
having a child, and, if you are a woman, the possibility that you will
relapse after giving birth or during the pregnancy. There will be
decisions that are not easy to make, but information from your
healthcare team can aid in difficult discussions. As mentioned in
Chapter 5, some medications used to treat schizophrenia may not be
suitable for use during pregnancy. Therefore, you should discuss your
options with your doctor before trying to conceive a child.

[`S` are for those with schizophrenia, while `F` is
intended for family members]

- Learn more about schizophrenia
  - S: Explain it to your friends and family
  - F: Try to be understanding of your family member’s behaviour
- Be honest
  - S: Explain it to your friends and family
  - F: For example, about your fears and your hopes
- Agree on boundaries
  - S: Tell people close to you what you want them to do and,
    importantly, what you don’t want them to do
  - F: Respect your family member’s wishes as far as possible
- Build trust
  - S: Trust that your family want what is best for you
  - F: Show the person that you have their best interests at heart
- Don’t be ashamed
  - S: You are not to blame for your illness and it is nothing to be
    ashamed of
  - F: There is nothing shameful about caring for someone with
    schizophrenia
- Learn from others
  - S and F: Support groups will have members who have been in similar
    situations and can help
")


evaluation: ¤:provide_feedback({"evaluation": "ACCEPTED"}):¤

