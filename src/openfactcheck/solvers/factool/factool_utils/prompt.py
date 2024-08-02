"""All prompts used for fact-checking subtasks prompting."""

CLAIM_EXTRACTION_PROMPT = {
    "system": "Please provide the claim you would like to fact-check.",
    "user": """You are given a piece of text that includes knowledge claims. A claim is a statement that asserts something as true or false, which can be verified by humans. Your task is to accurately identify and extract every claim stated in the provided text. Then, resolve any coreference (pronouns or other referring expressions) in the claim for clarity. Each claim should be concise (less than 15 words) and self-contained.
Your response MUST be a list of dictionaries. Each dictionary should contains the key "claim", which correspond to the extracted claim (with all coreferences resolved).
You MUST only respond in the format as described below. DO NOT RESPOND WITH ANYTHING ELSE. ADDING ANY OTHER EXTRA NOTES THAT VIOLATE THE RESPONSE FORMAT IS BANNED. START YOUR RESPONSE WITH '['.
[response format]: 
[
    {{
    "claim": "Ensure that the claim is fewer than 15 words and conveys a complete idea. Resolve any coreference (pronouns or other referring expressions) in the claim for clarity",
    }},
    ...
]

Here are two examples:
[text]: Tomas Berdych defeated Gael Monfis 6-1, 6-4 on Saturday. The sixth-seed reaches Monte Carlo Masters final for the first time . Berdych will face either Rafael Nadal or Novak Djokovic in the final.
[response]: [{{"claim": "Tomas Berdych defeated Gael Monfis 6-1, 6-4"}}, {{"claim": "Tomas Berdych defeated Gael Monfis 6-1, 6-4 on Saturday"}}, {{"claim": "Tomas Berdych reaches Monte Carlo Masters final"}}, {{"claim": "Tomas Berdych is the sixth-seed"}}, {{"claim": "Tomas Berdych reaches Monte Carlo Masters final for the first time"}}, {{"claim": "Berdych will face either Rafael Nadal or Novak Djokovic"}}, {{"claim": "Berdych will face either Rafael Nadal or Novak Djokovic in the final"}}]

[text]: Tinder only displays the last 34 photos - but users can easily see more. Firm also said it had improved its mutual friends feature.
[response]: [{{"claim": "Tinder only displays the last photos"}}, {{"claim": "Tinder only displays the last 34 photos"}}, {{"claim": "Tinder users can easily see more photos"}}, {{"claim": "Tinder said it had improved its feature"}}, {{"claim": "Tinder said it had improved its mutual friends feature"}}]

Now complete the following,ONLY RESPONSE IN A LIST FORMAT, NO OTHER WORDS!!!:
[text]: {input}
[response]: 
"""
}

QUERY_GENERATION_PROMPT = {
    "system": "You are a query generator that generates effective and concise search engine queries to verify a given claim. You only response in a python list format(NO OTHER WORDS!)",
    "user": """You are a query generator designed to help users verify a given claim using search engines. Your primary task is to generate a Python list of two effective and skeptical search engine queries. These queries should assist users in critically evaluating the factuality of a provided claim using search engines.
You should only respond in format as described below (a Python list of queries). PLEASE STRICTLY FOLLOW THE FORMAT. DO NOT RETURN ANYTHING ELSE. START YOUR RESPONSE WITH '['.
[response format]: ['query1', 'query2']

Here are three examples:
claim: The CEO of twitter is Bill Gates.
response: ["Who is the CEO of twitter?", "CEO Twitter"]

claim: Michael Phelps is the most decorated Olympian of all time.
response: ["Who is the most decorated Olympian of all time?", "Michael Phelps"]

claim: ChatGPT is created by Google.
response: ["Who created ChatGPT?", "ChatGPT"]

Now complete the following(ONLY RESPONSE IN A LIST FORMAT, DO NOT RETURN OTHER WORDS!!! START YOUR RESPONSE WITH '[' AND END WITH ']'):
claim: {input}
response: 
"""
}

VERIFICATION_PROMPT = {
    "system": "You are a brilliant assistant.",
    "user": """You are given a piece of text. Your task is to identify whether there are any factual errors within the text.
When you are judging the factuality of the given text, you could reference the provided evidences if needed. The provided evidences may be helpful. Some evidences may contradict to each other. You must be careful when using the evidences to judge the factuality of the given text.
The response should be a dictionary with three keys - "reasoning", "factuality", "error", and "correction", which correspond to the reasoning, whether the given text is factual or not (Boolean - True or False), the factual error present in the text, and the corrected text.
The following is the given text
[text]: {claim}
The following is the provided evidences
[evidences]: {evidence}
You should only respond in format as described below. DO NOT RETURN ANYTHING ELSE. START YOUR RESPONSE WITH '{{'.
[response format]: 
{{
    "reasoning": "Why is the given text factual or non-factual? Be careful when you said something is non-factual. When you said something is non-factual, you must provide multiple evidences to support your decision.",
    "error": "None if the text is factual; otherwise, describe the error.",
    "correction": "The corrected text if there is an error.",
    "factuality": True if the given text is factual, False otherwise.
}}
"""
}
