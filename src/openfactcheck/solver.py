import os
import importlib

from openfactcheck.utils.logging import get_logger
from openfactcheck.state import FactCheckerState

# Get the logger
logger = get_logger(__name__)

# Global solver registry
SOLVER_REGISTRY = {}

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
        self.logger = logger
        self.args = args

        logger.debug(self.args)

    def __call__(self, state: FactCheckerState, **kwargs) -> tuple[
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

class Solver:
    """
    Class to handle the registration and loading of solvers
    """
    def __init__(self):
        pass

    def register(name, input_name=None, output_name=None):
        def decorator(cls):
            """
            Decorator to register a solver class
            """

            # Check if the solver is already registered
            if name in SOLVER_REGISTRY:
                return SOLVER_REGISTRY[name]

            # Check if the solver class extends StandardTaskSolver
            if not issubclass(cls, StandardTaskSolver):
                logger.error(f"Solver '{name}' must extend StandardTaskSolver, got {cls.__name__}.")
                raise ValueError(f"Solver '{name}' must extend StandardTaskSolver, got {cls.__name__}.")
            
            # Register the solver
            SOLVER_REGISTRY[name] = cls
            cls.name = name
            cls.input_name = input_name
            cls.output_name = output_name

            logger.info(f"Solver '{name}' registered")
            return cls

        return decorator
    
    @staticmethod
    def load_from_directory(directory, namespace):
        """
        Load solvers from a directory
        """

        # Check if the directory exists
        for item in sorted(os.listdir(directory), 
                           key=lambda x: os.path.isdir(os.path.join(directory, x)), 
                           reverse=True):
            
            # Skip hidden files and directories
            if item.startswith('_') or item.startswith('.'):
                continue

            # Get the full path of the item
            full_path = os.path.join(directory, item)

            # Load the item
            if os.path.isdir(full_path):
                Solver.load_from_directory(full_path, namespace + '.' + item)
            else:
                Solver.load_from_file(full_path, namespace)
    
    @staticmethod
    def load_from_file(file_path, namespace):
        """
        Load a solver from a file
        """

        # Check if the file is a Python file
        if file_path.endswith(".py"):
            # Get the solver name
            solver_name = os.path.basename(file_path)[:-3]

            # Get the module name
            module_name = namespace + "." + solver_name

            # Log the full module name to debug
            logger.debug(f"Attempting to import {module_name} from {file_path}")

            # Import the module
            try:
                importlib.import_module(module_name)
                logger.debug(f"Successfully imported {module_name}")
            except Exception as e:
                logger.error(f"Failed to import {module_name}: {e}")
                raise Exception(f"Failed to import {module_name}: {e}")

            return module_name

    @staticmethod
    def load(path, namespace):
        if os.path.isdir(path):
            Solver.load_from_directory(path, namespace)
        else:
            Solver.load_from_file(path, namespace)
        return
