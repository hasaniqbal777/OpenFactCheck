import os 
import sys
import uuid
import tqdm
import json
import traceback
from pathlib import Path
from typing import Callable

from openfactcheck.lib.logger import logger
from openfactcheck.lib.config import OpenFactCheckConfig
from openfactcheck.core.solver import SOLVER_REGISTRY, Solver
from openfactcheck.core.state import FactCheckerState

class OpenFactCheck:
    """
    OpenFactCheck class to evaluate the factuality of a response using a pipeline of solvers.

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
        self.pipeline = self.init_pipeline()

        self.logger.info("-------------- OpenFactCheck Initialized ----------------")
        self.logger.info("Pipeline:")
        for idx, (name, (solver, iname, oname)) in enumerate(self.pipeline.items()):
            self.logger.info(f"{idx}-{name} ({iname} -> {oname})")
        self.logger.info("---------------------------------------------------------")

    @staticmethod
    def load_solvers(solver_paths):
        """
        Load solvers from the given paths
        """
        for solver_path in solver_paths:
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
        solver_cls.input_name = args.get("input_name", solver_cls.input_name)
        solver_cls.output_name = args.get("output_name", solver_cls.output_name)

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
        pipeline = {}
        for required_solver in self.config.pipeline:
            if required_solver not in self.solver_configs:
                logger.error(f"{required_solver} not in solvers config")
                raise RuntimeError(f"{required_solver} not in solvers config")
            solver, input_name, output_name = self.init_solver(required_solver, self.solver_configs[required_solver])
            pipeline[required_solver] = (solver, input_name, output_name)

        return pipeline
    
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

    def persist_output(self, state: FactCheckerState, idx, solver_name, cont, sample_name=0):
        result = {
            "idx": idx,
            "solver": solver_name,
            "continue": cont,
            "state": state.to_dict()
        }
        with open(os.path.join(self.output_path, f'{sample_name}.jsonl'), 'a', encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    def read_output(self, sample_name):
        """
        Read the output file for the given sample
        """
        with open(os.path.join(self.output_path, f'{sample_name}.jsonl'), 'r', encoding="utf-8") as f:
            return [json.loads(line) for line in f]
        
    def remove_output(self, sample_name):
        """
        Remove the output file for the given sample
        """
        os.remove(os.path.join(self.output_path, f'{sample_name}.jsonl'))

    def __call__(self, response: str, question: str = None, stream: bool = False, callback: Callable = None, **kwargs):
        """
        Evaluate the response using the pipeline
        """

        def evaluate_response():
            # Check if sample_name is provided in kwargs else generate a random one
            sample_name = kwargs.get("sample_name", str(uuid.uuid4().hex[:6]))

            # Initialize the state
            solver_output = FactCheckerState(question=question, response=response)

            # Initialize the output name
            output_name = "response"
            for idx, (name, (solver, input_name, output_name)) in tqdm.tqdm(enumerate(self.pipeline.items()),
                                                                total=len(self.pipeline)):
                logger.info(f"Invoking solver: {idx}-{name}")
                logger.info(f"State content: {solver_output}")
            
                try:
                    # Solver input is the output of the previous solver
                    solver_input = solver_output

                    # Run the solver
                    cont, solver_output = solver(solver_input, **kwargs)

                    # Persist the output
                    logger.debug(f"Latest result: {solver_output}")
                    if callback:
                        callback(
                            index=idx,
                            sample_name=sample_name,
                            solver_name=name,
                            input_name=input_name,
                            output_name=output_name,
                            input=solver_input.__dict__,
                            output=solver_output.__dict__,
                            continue_run=cont
                        )
                    
                    # Stream the output
                    if stream:
                        yield {
                            "index": idx,
                            "solver_name": name,
                            "input_name": input_name,
                            "output_name": output_name,
                            "input": solver_input.__dict__,
                            "output": solver_output.__dict__,
                            "continue_run": cont
                        }

                    self.persist_output(solver_output, idx, name, cont, sample_name=sample_name)
                    
                except:
                    logger.error(f"Error at {traceback.format_exc()}")
                    cont = False
                    output_name = input_name

                # Break if the solver returns False
                if not cont:
                    logger.info(f"Break at {name}")
                    break
                
            if not stream:
                return solver_output.get(output_name)
        
        # Execute the generator if stream is True, otherwise process normally
        return evaluate_response()