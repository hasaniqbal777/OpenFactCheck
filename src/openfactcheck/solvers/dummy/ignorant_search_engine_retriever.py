import random
import string

from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("ignorant_search_engine_retriever", "claims", "claims_with_evidences")
class IgnorantSearchEngineRetriever(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)
        self.max_num_documents = args.get("max_num_documents",5)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claims = state.get(self.input_name)

        claims_with_evidences = {}
        for idx, claim in enumerate(claims):
            # Assume we call some search engine API here
            documents = [string.ascii_letters[random.randint(0, 25)] for i in range(self.max_num_documents)]
            key = f"{idx}-{claim}"  # Convert the tuple to a string key
            claims_with_evidences[key] = documents

        state.set(self.output_name, claims_with_evidences)
        return True, state
