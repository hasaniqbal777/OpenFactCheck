from factool import Factool

from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("factool_blackbox", "response", "claim_info")
class FactoolBlackboxSolver(StandardTaskSolver):
    """
    A solver to process the response using the Factool black box model.
    """
    def __init__(self, args):
        super().__init__(args)
        self.input_prompt = args.get("input_prompt", None)
        self.model_name = self.global_config.get("model_name", "gpt-4o")

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        prompt = state.get(self.input_prompt)
        response = state.get(self.input_name)

        factool_instance = Factool(self.model_name)

        inputs = [{"prompt": prompt, "response": response, "category": "kbqa"}]
        claim_info = factool_instance.run(inputs)

        state.set("claim_info", claim_info)
        return True, state
