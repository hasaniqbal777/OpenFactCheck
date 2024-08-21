from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("factool_post_editor", "claim_info", "claim_info")
class FactoolPostEditor(StandardTaskSolver):
    """
    A solver to post-process the results of the Factool model. 
    Used to presents the results in human-readable format and to save the analysis in a JSON file.
    """
    def __init__(self, args):
        super().__init__(args)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        claim_info = state.get(self.input_name)

        for key, pair in claim_info.items():
            claim_info[key]['edited_claims'] = claim_info[key]['stances'][0]

        state.set(self.output_name, claim_info)
        return True, state
