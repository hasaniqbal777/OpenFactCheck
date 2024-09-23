import os 
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from openfactcheck.utils.logging import get_logger
from openfactcheck.lib import OpenFactCheckConfig
from openfactcheck.solver import SOLVER_REGISTRY, Solver

# Get the logger
logger = get_logger(__name__)

if TYPE_CHECKING:
    from openfactcheck.evaluator.llm import LLMEvaluator
    from openfactcheck.evaluator.response import ResponseEvaluator
    from openfactcheck.evaluator.checker import CheckerEvaluator

class OpenFactCheck:
    """
    Base class for OpenFactCheck that initializes the solvers and pipeline
    with the given configuration.

    Parameters
    ----------
    config : OpenFactCheckConfig
        An instance of OpenFactCheckConfig containing the configuration
        settings for OpenFactCheck.

    Attributes
    ----------
    logger : Logger
        An instance of the logger to log messages.
    config : OpenFactCheckConfig
        An instance of OpenFactCheckConfig containing the configuration
        settings for OpenFactCheck.
    solver_configs : dict
        A dictionary containing the configuration settings for the solvers.
    pipeline : list
        A list of solvers to be included in the pipeline.
    output_path : str
        The path to the output directory where the results will be stored.

    Methods
    -------
    load_solvers(solver_paths)
        Load solvers from the given paths.
    list_solvers()
        List all registered solvers.
    list_claimprocessors()
        List all registered claim processors.
    list_retrievers()
        List all registered retrievers.
    list_verifiers()
        List all registered verifiers.
    init_solver(solver_name, args)
        Initialize a solver with the given configuration.
    init_solvers()
        Initialize all registered solvers.
    init_pipeline()
        Initialize the pipeline with the given configuration.
    init_pipeline_manually(pipeline)
        Initialize the pipeline with the given configuration.
    persist_output(state, idx, solver_name, cont, sample_name=0)
        Persist the output of the solver.
    read_output(sample_name)
        Read the output file for the given sample.
    remove_output(sample_name)
        Remove the output file for the given sample.
    __call__(response, question, callback_fun, **kwargs)
        Evaluate the response using the pipeline.

    Examples
    --------
    >>> config = OpenFactCheckConfig("config.json")
    >>> ofc = OpenFactCheck(config)
    >>> response, sample_name = ofc("This is a sample response.")
    >>> output = ofc.read_output(sample_name)
    >>> ofc.remove_output(sample_name)
    """
    def __init__(self, config: OpenFactCheckConfig):
        """
        Initialize OpenFactCheck with the given configuration.

        Parameters
        ----------
        config : OpenFactCheckConfig
            An instance of OpenFactCheckConfig containing the configuration
            settings for OpenFactCheck.
        """
        self.logger = logger
        self.config = config    

        # Initialize attributes
        self.solver_configs = self.config.solver_configs
        self.pipeline = self.config.pipeline
        self.output_path = os.path.abspath(self.config.output_path)

        # Load and register solvers
        self.load_solvers(self.config.solver_paths)
        self.logger.info(f"Loaded solvers: {list(self.list_solvers().keys())}")

        # Initialize the pipeline
        self.init_pipeline()
    
    @property
    def LLMEvaluator(self) -> 'LLMEvaluator':
        """
        Return the LLM Evaluator
        """
        from openfactcheck.evaluator.llm import LLMEvaluator
        return LLMEvaluator(self)
    
    @property
    def FactCheckerEvaluator(self) -> 'CheckerEvaluator':
        """
        Return the FactChecker Evaluator
        """
        from openfactcheck.evaluator.checker import CheckerEvaluator
        return CheckerEvaluator(self)
    
    @property
    def ResponseEvaluator(self) -> 'ResponseEvaluator':
        """
        Return the LLM Response Evaluator
        """
        from openfactcheck.evaluator.response import ResponseEvaluator
        return ResponseEvaluator(self)

    @staticmethod
    def load_solvers(solver_paths: dict):
        """
        Load solvers from the given paths
        """
        for key, value in solver_paths.items():
            if key == "default":
                for solver_path in value:
                    abs_path = Path(solver_path).resolve()
                    if abs_path.is_dir():
                        sys.path.append(str(abs_path.parent))
                        Solver.load(str(abs_path), f"{abs_path.parent.parent.name}.{abs_path.parent.name}.{abs_path.name}")
            else:
                for solver_path in value:
                    abs_path = Path(solver_path).resolve()
                    if abs_path.is_dir():
                        sys.path.append(str(abs_path.parent))
                        Solver.load(str(abs_path), abs_path.name)

    @staticmethod
    def list_solvers():
        """
        List all registered solvers
        """
        return SOLVER_REGISTRY
    
    @staticmethod
    def list_claimprocessors():
        """
        List all registered claim processors
        """
        # Get all claim processors
        claimprocessors = {}
        for solver, value in SOLVER_REGISTRY.items():
            if "claimprocessor" in solver:
                claimprocessors[solver] = value

        return claimprocessors
    
    @staticmethod
    def list_retrievers():
        """
        List all registered retrievers
        """
        # Get all retrievers
        retrievers = {}
        for solver, value in SOLVER_REGISTRY.items():
            if "retriever" in solver:
                retrievers[solver] = value

        return retrievers
    
    @staticmethod
    def list_verifiers():
        """
        List all registered verifiers
        """
        # Get all verifiers
        verifiers = {}
        for solver, value in SOLVER_REGISTRY.items():
            if "verifier" in solver:
                verifiers[solver] = value

        return verifiers
    
    def init_solver(self, solver_name, args):
        """
        Initialize a solver with the given configuration
        """

        # Check if the solver is registered
        if solver_name not in SOLVER_REGISTRY:
            logger.error(f"{solver_name} not in SOLVER_REGISTRY")
            raise RuntimeError(f"{solver_name} not in SOLVER_REGISTRY")
        
        # Initialize the solver
        solver_cls = SOLVER_REGISTRY[solver_name]
        for key, value in args.items():
            setattr(solver_cls, key, value)
        
        logger.info(f"Solver {solver_cls(args)} initialized")

        return solver_cls(args), solver_cls.input_name, solver_cls.output_name
    
    def init_solvers(self):
        """
        Initialize all registered solvers
        """
        solvers = {}
        for k, v in self.solver_configs.items():
            solver, input_name, output_name = self.init_solver(k, v)
            solvers[k] = (solver, input_name, output_name)
        return solvers
    
    def init_pipeline(self):
        """
        Initialize the pipeline with the given configuration
        """
        self.pipeline = {}
        for required_solver in self.config.pipeline:
            if required_solver not in self.solver_configs:
                logger.error(f"{required_solver} not in solvers config")
                raise RuntimeError(f"{required_solver} not in solvers config")
            solver, input_name, output_name = self.init_solver(required_solver, self.solver_configs[required_solver])
            self.pipeline[required_solver] = (solver, input_name, output_name)

        self.logger.info("-------------- OpenFactCheck Initialized ----------------")
        self.logger.info("Pipeline:")
        for idx, (name, (solver, iname, oname)) in enumerate(self.pipeline.items()):
            self.logger.info(f"{idx}-{name} ({iname} -> {oname})")
        self.logger.info("---------------------------------------------------------")
    
    def init_pipeline_manually(self, pipeline: list):
        """
        Initialize the pipeline with the given configuration

        Parameters
        ----------
        pipeline : list
            A list of solvers to be included in the pipeline
        """
        self.pipeline = {}
        for required_solver in pipeline:
            if required_solver not in self.solver_configs:
                raise RuntimeError(f"{required_solver} not in solvers config")
            solver, input_name, output_name = self.init_solver(required_solver, self.solver_configs[required_solver])
            self.pipeline[required_solver] = (solver, input_name, output_name)

        self.logger.info("-------------- OpenFactCheck Initialized ----------------")
        self.logger.info("Pipeline:")
        for idx, (name, (solver, iname, oname)) in enumerate(self.pipeline.items()):
            self.logger.info(f"{idx}-{name} ({iname} -> {oname})")
        self.logger.info("---------------------------------------------------------")