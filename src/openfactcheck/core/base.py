import os 
import sys
import tqdm
import yaml
import json
import traceback
from pathlib import Path

from openfactcheck.lib.logger import logger
from openfactcheck.lib.config import OpenFactCheckConfig
from openfactcheck.core.solver import SOLVER_REGISTRY, Solver
from openfactcheck.core.state import FactCheckerState

class OpenFactCheck:
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

    def __call__(self, response: str, question: str = None, callback_fun=None, **kwargs):
        sample_name = kwargs.get("sample_name", 0)
        solver_output = FactCheckerState(question=question, response=response)
        oname = "response"
        for idx, (name, (solver, iname, oname)) in tqdm.tqdm(enumerate(self.pipeline.items()),
                                                             total=len(self.pipeline)):
            logger.info(f"Invoking solver: {idx}-{name}")
            logger.debug(f"State content: {solver_output}")
            try:
                solver_input = solver_output
                cont, solver_output = solver(solver_input, **kwargs)
                logger.debug(f"Latest result: {solver_output}")
                if callback_fun:
                    callback_fun(
                        index=idx,
                        sample_name=sample_name,
                        solver_name=name,
                        input_name=iname,
                        output_name=oname,
                        input=solver_input.__dict__,
                        output=solver_output.__dict__,
                        continue_run=cont
                    )
                self.persist_output(solver_output, idx, name, cont, sample_name=sample_name)
            except:
                print(traceback.format_exc())
                cont = False
                oname = iname
            if not cont:
                logger.info(f"Break at {name}")
                break

        return solver_output.get(oname)
