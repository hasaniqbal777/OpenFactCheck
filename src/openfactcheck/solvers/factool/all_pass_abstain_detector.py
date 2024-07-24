import logging

from openfactcheck.core.state import FactCheckerState
from openfactcheck.core.solver import StandardTaskSolver, Solver

@Solver.register_solver("all_pass_abstain_detector", "response", "response")
class AllPassAbstainDetector(StandardTaskSolver):
    def __init__(self, args):
        super().__init__(args)

    def __call__(self, state: FactCheckerState, *args, **kwargs):
        return True, state
