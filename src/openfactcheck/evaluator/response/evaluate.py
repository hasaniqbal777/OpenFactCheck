import os
import uuid
import tqdm
import json
import traceback
from typing import Callable

from openfactcheck.utils.logging import get_logger
from openfactcheck.base import OpenFactCheck
from openfactcheck.state import FactCheckerState

# Get the logger
logger = get_logger(__name__)

class ResponseEvaluator:
    """
    This class is used to evaluate the factuality of a response using the pipeline of solvers.
    """
    def __init__(self, ofc: OpenFactCheck):
        """
        Initialize the ResponseEvaluator object.
        """
        
        # Set the OpenFactCheck object
        self.ofc = ofc

    def persist_output(self, state: FactCheckerState, idx, solver_name, cont, sample_name=0):
        """
        Persist the output of the solver
        """
        result = {
            "idx": idx,
            "solver": solver_name,
            "continue": cont,
            "state": state.to_dict()
        }

        # Create the output path
        output_path = os.path.join(self.ofc.output_path, os.path.dirname(sample_name))
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Write the output to a file
        with open(os.path.join(self.ofc.output_path, f'{sample_name}.jsonl'), 'a', encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    def read_output(self, sample_name):
        """
        Read the output file for the given sample
        """
        with open(os.path.join(self.ofc.output_path, f'{sample_name}.jsonl'), 'r', encoding="utf-8") as f:
            return [json.loads(line) for line in f]
        
    def remove_output(self, sample_name):
        """
        Remove the output file for the given sample
        """
        os.remove(os.path.join(self.ofc.output_path, f'{sample_name}.jsonl'))

    def evaluate(self, response: str, question: str = None, callback: Callable = None, **kwargs):
        """
        Evaluate the response using the pipeline and return the output
        """

        # Check if sample_name is provided in kwargs else generate a random one
        sample_name = kwargs.get("sample_name", str(uuid.uuid4()))

        # Initialize the state
        solver_output = FactCheckerState(question=question, response=response)

        # Initialize the output name
        output_name = "response"
        for idx, (name, (solver, input_name, output_name)) in tqdm.tqdm(enumerate(self.ofc.pipeline.items()),
                                                            total=len(self.ofc.pipeline)):
            logger.info(f"Invoking solver: {idx}-{name}")
            logger.debug(f"State content: {solver_output}")
        
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
                
                self.persist_output(solver_output, idx, name, cont, sample_name=sample_name)
                
            except:
                logger.error(f"Error at {traceback.format_exc()}")
                cont = False
                output_name = input_name

            # Break if the solver returns False
            if not cont:
                logger.info(f"Break at {name}")
                break

        return solver_output.get(output_name)

    def evaluate_streaming(self, response: str, question: str = None, **kwargs):
        """
        Evaluate the response using the pipeline and stream the output
        """

        def evaluate_response():
            # Check if sample_name is provided in kwargs else generate a random one
            sample_name = kwargs.get("sample_name", str(uuid.uuid4()))

            # Initialize the state
            solver_output = FactCheckerState(question=question, response=response)

            # Initialize the output name
            output_name = "response"
            for idx, (name, (solver, input_name, output_name)) in tqdm.tqdm(enumerate(self.ofc.pipeline.items()),
                                                                total=len(self.ofc.pipeline)):
                logger.info(f"Invoking solver: {idx}-{name}")
                logger.debug(f"State content: {solver_output}")
            
                try:
                    # Solver input is the output of the previous solver
                    solver_input = solver_output

                    # Run the solver
                    cont, solver_output = solver(solver_input, **kwargs)

                    # Persist the output
                    logger.debug(f"Latest result: {solver_output}")
                    
                    # Stream the output
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
        
        # Execute the generator if stream is True, otherwise process normally
        return evaluate_response()