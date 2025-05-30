import os
from openfactcheck.state import FactCheckerState
from openfactcheck.solver import StandardTaskSolver, Solver

from .urdufactcheck_utils.chat_api import OpenAIChat, AnthropicChat
from .urdufactcheck_utils.prompt import CLAIM_EXTRACTION_PROMPT


@Solver.register("urdufactcheck_claimprocessor", "response", "claims")
class UrduFactCheckClaimProcessor(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.gpt_model = os.environ.get("MODEL_NAME", "gpt-4o")
        if "claude" in self.gpt_model:
            self.gpt = AnthropicChat(self.gpt_model)
        else:
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
