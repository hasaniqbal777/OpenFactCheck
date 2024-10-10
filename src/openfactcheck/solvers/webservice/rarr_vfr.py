from openfactcheck.state import FactCheckerState
from openfactcheck.solver import StandardTaskSolver, Solver

from .rarr_utils.agreement_gate import run_agreement_gate
from .rarr_utils.functional_prompt import AGREEMENT_GATE_PROMPT


@Solver.register("rarr_verifier", "claims_with_evidences", "label")
class RARRAgreementGate(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.max_evidences_per_question = args.get("max_evidences_per_question", 1)
        self.model = self.global_config.get("rarr_model", "gpt-4o-instruct")

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claims_with_evidences = state.get(self.input_name)
        results = []
        for claim, evidences in claims_with_evidences.items():
            result = {}
            evidences = evidences[: self.max_evidences_per_question]
            labels = []
            for query, evidence in evidences:
                gate = run_agreement_gate(
                    claim=claim,
                    context=None,
                    query=query,
                    evidence=evidence,
                    model=self.model,
                    prompt=AGREEMENT_GATE_PROMPT,
                )
                labels.append(gate["is_open"])
            result["claim"] = claim
            result["evidences"] = evidences
            result["labels"] = labels
            result["factuality"] = all(labels)
            results.append(result)
        state.set(self.output_name, all([x["factuality"] for x in results]))
        state.set("detail", results)
        return True, state
