from openfactcheck import FactCheckerState, StandardTaskSolver, Solver

@Solver.register("all_pass_abstain_detector", "response", "response")
class AllPassAbstainDetector(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        return True, state
