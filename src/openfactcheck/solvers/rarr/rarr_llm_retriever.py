from .rarr_utils.hallucination import run_evidence_hallucination
from .prompts.hallucination_prompts import EVIDENCE_HALLUCINATION

from openfactcheck import FactCheckerState, StandardTaskSolver, Solver


@Solver.register("llm_retriever", "claims_with_questions", "claims_with_evidences")
class RARRLLMRetriever(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.model = self.global_config.get("model", "gpt-4o-instruct")

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claims = state.get(self.input_name)

        for claim, contents in claims.items():
            questions = contents.get("questions", [])
            evidences = []
            for question in questions:
                evidences.append(run_evidence_hallucination(question, model=self.model, prompt=EVIDENCE_HALLUCINATION))
            claims[claim]["evidences"] = evidences

        state.set(self.output_name, claims)
        return True, state
