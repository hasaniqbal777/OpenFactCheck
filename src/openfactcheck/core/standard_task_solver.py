import logging
from typing import Tuple

from fact_check_state import FactCheckerState

class StandardTaskSolver:
    """
    A class to represent a standard task solver. A standard task solver is a
    class that implements a specific task in a fact-checking system. It
    receives a FactCheckerState object as input and returns a new
    FactCheckerState object as output.

    Parameters
    ----------
    args : dict
        A dictionary containing the arguments to be passed to the solver.
    """

    name: str = None
    input_name: str = None
    output_name: str = None
    global_config: dict = dict()

    def __init__(self, args: dict):
        self.args = args
        logging.debug(self.args)

    def __call__(self, state: FactCheckerState, **kwargs) -> Tuple[
        bool, FactCheckerState]:
        raise NotImplementedError

    @classmethod
    def build_solver(cls, args):
        raise NotImplementedError

    @property
    def input_name(self):
        return self.__class__.input_name

    @property
    def output_name(self):
        return self.__class__.output_name

    def __str__(self):
        return f'[name:"{self.__class__.name}", input: "{self.__class__.input_name}": output: "{self.__class__.output_name}"]'
