from openfactcheck.state import FactCheckerState
from openfactcheck.solver import StandardTaskSolver, Solver

from .rarr_utils.question_generation import run_rarr_question_generation
from .rarr_utils.functional_prompt import QGEN_PROMPT
from .rarr_utils import search


@Solver.register("rarr_retriever", "claims", "claims_with_evidences")
class RARRRetriever(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.model = self.global_config.get("rarr_model", "gpt-4o-instruct")
        self.temperature_qgen = args.get("temperature_qgen", 0.7)
        self.num_rounds_qgen = args.get("num_rounds_qgen", 3)
        self.max_search_results_per_query = args.get("max_search_results_per_query", 5)
        self.max_sentences_per_passage = args.get("max_sentences_per_passage", 4)
        self.sliding_distance = args.get("sliding_distance", 1)
        self.max_passages_per_search_result = args.get("max_passages_per_search_result", 1)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claims = state.get(self.input_name)

        results = dict()
        for claim in claims:
            questions = run_rarr_question_generation(
                claim=claim,
                context=None,
                model=self.model,
                prompt=QGEN_PROMPT,
                temperature=self.temperature_qgen,
                num_rounds=self.num_rounds_qgen,
            )
            evidences = []
            for question in questions:
                q_evidences = search.run_search(
                    query=question,
                    max_search_results_per_query=self.max_search_results_per_query,
                    max_sentences_per_passage=self.max_sentences_per_passage,
                    sliding_distance=self.sliding_distance,
                    max_passages_per_search_result_to_return=self.max_passages_per_search_result,
                )
                evidences.extend([(question, x["text"]) for x in q_evidences])

            results[claim] = evidences

        state.set(self.output_name, results)
        return True, state
