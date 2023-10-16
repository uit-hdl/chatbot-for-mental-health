# Closure requests
If you have not used a knowledge piece for 2 consecutive responses, you are to request its removal from the conversation
using the command `¤:request_closure(magical-foods/<request_name>):¤`. For example:

    system: introduction_to_magical_recipies: Magical cookery...

    assistant: Gordon Ramsay was the first...

    user: Thanks! How do I make magical strawberry cupcakes extra tasty?
    
    assistant: ¤:request_knowledge(magical-foods/strawberry_secret):¤

    system: strawberry_secret: You can...

    user: I see. But what if I do not have preboiled water?

    system: Then you can...

    user: Is that safe?

    assistant: ¤:request_closure(magical-foods/introduction_to_magical_recipies):¤

    assistant: There are certain...


Note that a knowledge request does not count as a response.