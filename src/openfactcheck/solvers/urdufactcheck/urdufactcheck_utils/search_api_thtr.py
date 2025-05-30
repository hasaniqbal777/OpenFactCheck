import os
import json
import asyncio
import aiohttp

from .chat_api import OpenAIChat, AnthropicChat
from .prompt import (
    URDU_TO_ENGLISH_TRANSLATION_PROMPT,
    ENGLISH_TO_URDU_TRANSLATION_PROMPT,
)


class GoogleSerperAPIWrapper:
    """Wrapper around the Serper.dev Google Search API.
    You can create a free API key at https://serper.dev.
    To use, you should have the environment variable ``SERPER_API_KEY``
    set with your API key, or pass `serper_api_key` as a named parameter
    to the constructor.
    Example:
        .. code-block:: python
            from langchain import GoogleSerperAPIWrapper
            google_serper = GoogleSerperAPIWrapper()
    """

    def __init__(self, snippet_cnt=10) -> None:
        self.k = snippet_cnt
        self.gl = "us"
        self.hl = "ur"
        self.serper_api_key = os.environ.get("SERPER_API_KEY", None)
        assert (
            self.serper_api_key is not None
        ), "Please set the SERPER_API_KEY environment variable."
        assert (
            self.serper_api_key != ""
        ), "Please set the SERPER_API_KEY environment variable."

        self.gpt_model = os.environ.get("MODEL_NAME", "gpt-4o")
        if "claude" in self.gpt_model:
            self.gpt = AnthropicChat(self.gpt_model)
        else:
            self.gpt = OpenAIChat(self.gpt_model)
        self.english_to_urdu_translation_prompt = ENGLISH_TO_URDU_TRANSLATION_PROMPT
        self.urdu_to_english_translation_prompt = URDU_TO_ENGLISH_TRANSLATION_PROMPT

    async def _google_serper_search_results(
        self, session, search_term: str, gl: str, hl: str
    ) -> dict:
        headers = {
            "X-API-KEY": self.serper_api_key or "",
            "Content-Type": "application/json",
        }
        payload = {"q": search_term, "gl": gl, "hl": hl}
        try:
            async with session.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,  # <-- this is correct for POST JSON
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            print(f"Error for query '{search_term}': {e}")
            return {}

    def _parse_results(self, results):
        snippets = []

        if os.environ.get("SAVE_SERPER_COST", "False") == "True":
            SERPER_COST_PATH = os.environ.get("SERPER_COST_PATH", "serper_cost.jsonl")
            if results.get("credits"):
                credits = results.get("credits")
                with open(SERPER_COST_PATH, "a") as f:
                    f.write(json.dumps({"google_serper_credits": credits}) + "\n")

        if results.get("answerBox"):
            answer_box = results.get("answerBox", {})
            if answer_box.get("answer"):
                element = {"content": answer_box.get("answer"), "source": "None"}
                return [element]
            elif answer_box.get("snippet"):
                element = {
                    "content": answer_box.get("snippet").replace("\n", " "),
                    "source": "None",
                }
                return [element]
            elif answer_box.get("snippetHighlighted"):
                element = {
                    "content": answer_box.get("snippetHighlighted"),
                    "source": "None",
                }
                return [element]

        if results.get("knowledgeGraph"):
            kg = results.get("knowledgeGraph", {})
            title = kg.get("title")
            entity_type = kg.get("type")
            if entity_type:
                element = {"content": f"{title}: {entity_type}", "source": "None"}
                snippets.append(element)
            description = kg.get("description")
            if description:
                element = {"content": description, "source": "None"}
                snippets.append(element)
            for attribute, value in kg.get("attributes", {}).items():
                element = {"content": f"{attribute}: {value}", "source": "None"}
                snippets.append(element)

        for result in results["organic"][: self.k]:
            if "snippet" in result:
                element = {"content": result["snippet"], "source": result["link"]}
                snippets.append(element)
            for attribute, value in result.get("attributes", {}).items():
                element = {"content": f"{attribute}: {value}", "source": result["link"]}
                snippets.append(element)

        if len(snippets) == 0:
            element = {
                "content": "No good Google Search Result was found",
                "source": "None",
            }
            return [element]

        # keep only the first k snippets
        snippets = snippets[: int(self.k / 2)]

        return snippets

    async def parallel_searches(self, search_queries, gl, hl):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._google_serper_search_results(session, query, gl, hl)
                for query in search_queries
            ]
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            return search_results

    def run(self, queries):
        """Run query through GoogleSearch and parse result."""
        flattened_queries = []

        for sublist in queries:
            if sublist is None:
                sublist = ["None", "None"]
            for item in sublist:
                flattened_queries.append(item)

        # Get results
        results = asyncio.run(
            self.parallel_searches(flattened_queries, gl=self.gl, hl=self.hl)
        )
        snippets_list = []
        for i in range(len(results)):
            snippets_list.append(self._parse_results(results[i]))

        # Flatten the list of snippets
        snippets_split = [
            snippets_list[i] + snippets_list[i + 1]
            for i in range(0, len(snippets_list), 2)
        ]

        snippets_split_length = 0
        for snippet_split in snippets_split:
            if snippets_split_length == 0:
                snippets_split_length = len(snippet_split)
            if snippets_split_length > len(snippet_split):
                snippets_split_length = len(snippet_split)

        # Check if the evidence threshold is met
        print(f"Evidence threshold is set to {os.environ.get('EVIDENCE_THRESHOLD', 5)}")
        if snippets_split_length <= int(os.environ.get("EVIDENCE_THRESHOLD", 5)):
            print(f"Evidence threshold not met: {snippets_split_length}")
            # Translate Queries to English
            messages_list = [
                [
                    {
                        "role": "system",
                        "content": self.urdu_to_english_translation_prompt["system"],
                    },
                    {
                        "role": "user",
                        "content": self.urdu_to_english_translation_prompt[
                            "user"
                        ].format(input=query),
                    },
                ]
                for query in flattened_queries
            ]
            english_queries = self.gpt.run(messages_list, str)

            # Get results in English Language
            results = asyncio.run(
                self.parallel_searches(english_queries, gl=self.gl, hl="en")
            )
            snippets_list_en = []
            for i in range(len(results)):
                snippets_list_en.append(self._parse_results(results[i]))

            # Flatten the list of snippets
            snippets_split_en = [
                snippets_list_en[i] + snippets_list_en[i + 1]
                for i in range(0, len(snippets_list_en), 2)
            ]

            translated_snippets = []
            for snippet_split in snippets_split_en:
                messages_list = [
                    [
                        {
                            "role": "system",
                            "content": self.english_to_urdu_translation_prompt[
                                "system"
                            ],
                        },
                        {
                            "role": "user",
                            "content": self.english_to_urdu_translation_prompt[
                                "user"
                            ].format(input=snippet["content"]),
                        },
                    ]
                    for snippet in snippet_split
                ]
                urdu_snippets = self.gpt.run(messages_list, str)
                translated_snippet = []
                for urdu_snippet in urdu_snippets:
                    translated_snippet.append({"content": urdu_snippet})
                translated_snippets.append(translated_snippet)

            # Combine the translated snippets with the original snippets
            combined_snippets = [
                list1 + list2
                for list1, list2 in zip(snippets_split, translated_snippets)
            ]
            return combined_snippets
        else:
            return snippets_split
