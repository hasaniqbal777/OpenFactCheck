import os
import yaml

from .factool_utils.chat_api import OpenAIChat
from .factool_utils.prompt import CLAIM_EXTRACTION_PROMPT
from openfactcheck.core.solver import StandardTaskSolver, Solver
from openfactcheck.core.state import FactCheckerState

@Solver.register("factool_decontextualizer", "response", "claims")
class FactoolDecontextualizer(StandardTaskSolver):
    """
    A solver to extract claims from a response.
    """
    def __init__(self, args):
        super().__init__(args)
        self.gpt_model = self.global_config.get("llm_in_use", "gpt-4o")
        self.gpt = OpenAIChat(self.gpt_model)
        self.claim_prompt = CLAIM_EXTRACTION_PROMPT

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        response = state.get(self.input_name)

        claims = self._claim_extraction(responses=[response])[0]

        extracted_claims = [claim["claim"] for claim in claims]

        state.set(self.output_name, extracted_claims)
        return True, state

    def _claim_extraction(self, responses):
        messages_list = [
            [
                {"role": "system", "content": self.claim_prompt["system"]},
                {
                    "role": "user",
                    "content": self.claim_prompt["user"].format(input=response),
                },
            ]
            for response in responses
        ]
        return self.gpt.run(messages_list, list)
