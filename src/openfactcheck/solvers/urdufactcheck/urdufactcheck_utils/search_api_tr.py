import os
import json
import asyncio
import aiohttp

from .chat_api import OpenAIChat
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
        params = {"q": search_term, "gl": gl, "hl": hl}
        async with session.post(
            "https://google.serper.dev/search",
            headers=headers,
            params=params,
            raise_for_status=True,
        ) as response:
            return await response.json()

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
        """Run query through GoogleSearch by translating to English first and
        then translating the snippets back to Urdu—no thresholding."""
        # Flatten the nested query lists
        flattened_queries = []
        for sublist in queries:
            if sublist is None:
                sublist = ["None", "None"]
            for item in sublist:
                flattened_queries.append(item)

        # 1) Translate all Urdu queries into English
        messages_to_en = [
            [
                {
                    "role": "system",
                    "content": self.urdu_to_english_translation_prompt["system"],
                },
                {
                    "role": "user",
                    "content": self.urdu_to_english_translation_prompt["user"].format(
                        input=query
                    ),
                },
            ]
            for query in flattened_queries
        ]
        english_queries = self.gpt.run(messages_to_en, str)

        # 2) Perform all searches in English
        results_en = asyncio.run(
            self.parallel_searches(english_queries, gl=self.gl, hl="en")
        )
        parsed_snippets_en = [self._parse_results(r) for r in results_en]

        # 3) Pair up snippets two by two (to match the original logic)
        snippets_pairs = [
            parsed_snippets_en[i] + parsed_snippets_en[i + 1]
            for i in range(0, len(parsed_snippets_en), 2)
        ]

        # 4) Translate each snippet back into Urdu
        final_snippets = []
        for snippet_list in snippets_pairs:
            # build translation prompts for each snippet
            messages_to_ur = [
                [
                    {
                        "role": "system",
                        "content": self.english_to_urdu_translation_prompt["system"],
                    },
                    {
                        "role": "user",
                        "content": self.english_to_urdu_translation_prompt[
                            "user"
                        ].format(input=snip["content"]),
                    },
                ]
                for snip in snippet_list
            ]
            urdu_texts = self.gpt.run(messages_to_ur, str)
            # collect into the same structure
            final_snippets.append(
                [
                    {"content": txt, "source": snippet_list[idx].get("source", "None")}
                    for idx, txt in enumerate(urdu_texts)
                ]
            )

        return final_snippets
