from openfactcheck.state import FactCheckerState
from openfactcheck.solver import StandardTaskSolver, Solver

from .factool_utils.chat_api import OpenAIChat
from .factool_utils.search_api import GoogleSerperAPIWrapper
from .factool_utils.prompt import QUERY_GENERATION_PROMPT


@Solver.register("factool_retriever", "claims", "claims_with_evidences")
class FactoolRetriever(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.gpt_model = self.global_config.get("factool_gpt_model", "gpt-4o")
        self.snippet_cnt = args.get("snippet_cnt", 10)
        self.gpt = OpenAIChat(self.gpt_model)
        self.query_prompt = QUERY_GENERATION_PROMPT
        self.search_engine = GoogleSerperAPIWrapper(snippet_cnt=self.snippet_cnt)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claims = state.get(self.input_name)

        queries = self._query_generation(claims=claims)
        evidences = self.search_engine.run(queries)
        results = {}
        for query, claim, evidence in zip(queries, claims, evidences):
            merged_query = " ".join(query) if query and len(query) > 1 else str(query) if query else ""
            results[claim] = [(merged_query, x["content"]) for x in evidence]
        state.set(self.output_name, results)
        return True, state

    def _query_generation(self, claims):
        messages_list = [
            [
                {"role": "system", "content": self.query_prompt["system"]},
                {
                    "role": "user",
                    "content": self.query_prompt["user"].format(input=claim),
                },
            ]
            for claim in claims
        ]
        return self.gpt.run(messages_list, list)
