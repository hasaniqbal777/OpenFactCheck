import os
import json
import yaml
import datasets
import transformers
from pathlib import Path
from typing import Union
from collections import namedtuple

from .logger import logger, set_logger_level

class OpenFactCheckConfig:
    """
    Class to load the OpenFactCheck configuration from a JSON or YAML file.
    """
    def __init__(self, filename: Union[str, Path] = "config.json"):
        # Setup Logger
        self.logger = logger
        self.filename = filename

        # Define namedtuple structures
        Secrets = namedtuple("Secrets", ["openai_api_key", 
                                         "serper_api_key", 
                                         "azure_search_key"])
        Pipeline = namedtuple("Pipeline", ["claimprocessor",
                                           "retriever",
                                           "verifier"])
        
        # Define Attributes
        self.retries = 0
        self.pipeline = None
        self.solver_configs = None
        self.solver_paths = None
        self.output_path = None
        self.secrets = None
        self.verbose = ""

        try:
            # Loading Config File
            with open(self.filename, encoding="utf-8") as file:
                config = json.load(file)

                # Initialize Retries
                if 'retries' in config:
                    self.retries = config['retries']
                else:
                    self.logger.warning("Retries config missing or incomplete in the configuration file.")
                    self.retries = 0

                # Initialize Solver Configs
                if 'solver_configs' in config:
                    self.solver_configs = SolversConfig(config['solver_configs'])()
                else:
                    self.logger.warning("Solver configs missing or incomplete in the configuration file.")
                    self.solver_configs = None

                # Initialize Solver Paths
                if 'solver_paths' in config:
                    self.solver_paths = config['solver_paths']
                else:
                    self.logger.warning("Solver paths missing or incomplete in the configuration file.")
                    self.solver_paths = None

                # Initialize Output Path
                if 'output_path' in config:
                    self.output_path = config['output_path']
                    os.makedirs(self.output_path, exist_ok=True)
                else:
                    self.logger.warning("Output path missing or incomplete in the configuration file. Using default path.")
                    self.output_path = "tmp/output"
                    os.makedirs(self.output_path, exist_ok=True)
                
                # Initialize Pipeline config
                if 'pipeline' in config:
                    self.pipeline = Pipeline(claimprocessor=config['pipeline']['claimprocessor'],
                                             retriever=config['pipeline']['retriever'],
                                             verifier=config['pipeline']['verifier'])
                else:
                    self.logger.warning("Pipeline config missing or incomplete in the configuration file.")
                    self.pipeline = Pipeline(claimprocessor=None, retriever=None, verifier=None)

                self.logger.info(f"Config file loaded successfully from {self.filename}")

                # Initialize Secrets config
                if 'secrets' in config:
                    self.secrets = Secrets(openai_api_key=config['secrets']['openai_api_key'],
                                           serper_api_key=config['secrets']['serper_api_key'],
                                           azure_search_key=config['secrets']['azure_search_key'])
                else:
                    self.logger.warning("Secrets config missing or incomplete in the configuration file.")
                    self.secrets = Secrets(openai_api_key=None, serper_api_key=None, azure_search_key=None)
            
                # Initialize Environment Variables
                if self.secrets.openai_api_key:
                    os.environ['OPENAI_API_KEY'] = self.secrets.openai_api_key
                if self.secrets.serper_api_key:
                    os.environ['SERPER_API_KEY'] = self.secrets.serper_api_key
                if self.secrets.azure_search_key:
                    os.environ['AZURE_SEARCH_KEY'] = self.secrets.azure_search_key

                # Initialize Verbose
                if 'verbose' in config:
                    self.verbose = config['verbose']
                    set_logger_level(self.logger, self.verbose)
                else:
                    self.logger.warning("Verbose config missing or incomplete in the configuration file.")
                    self.verbose = ""
                    set_logger_level(self.logger, "INFO")

                # Disable Transformers and Datasets logging
                transformers.logging.set_verbosity_error()
                datasets.logging.set_verbosity_error()

        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.filename}")
            raise FileNotFoundError(f"Config file not found: {self.filename}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.filename}")
            raise ValueError(f"Invalid JSON in config file: {self.filename}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error loading config file: {e}")
            raise Exception(f"Unexpected error loading config file: {e}")
        
class SolversConfig:
    """
    Class to load the solvers configuration from one or more JSON or YAML files.
    Merges all configurations into a single dictionary.

    Parameters
    ----------
    filename(s): str, Path, list
        The path to the solvers configuration or a list of paths to multiple solvers configurations.
    """
    def __init__(self, filename_s: Union[str, Path, list]):
        self.logger = logger
        self.filename_s = filename_s
        self.solvers = {}

        try:
            if isinstance(self.filename_s, (str, Path)):
                self.load_file(self.filename_s)
            elif isinstance(self.filename_s, list):
                for filename in self.filename_s:
                    self.load_file(filename)
            else:
                self.logger.error(f"Invalid filename type: {type(self.filename_s)}")
                raise ValueError(f"Invalid filename type: {type(self.filename_s)}")
            
        except FileNotFoundError:
            self.logger.error(f"Solvers file not found: {self.filename_s}")
            raise FileNotFoundError(f"Solvers file not found: {self.filename_s}")
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in solvers file: {self.filename_s}")
            raise ValueError(f"Invalid JSON in solvers file: {self.filename_s}")
        except Exception as e:
            self.logger.error(f"Unexpected error loading solvers file: {e}")
            raise Exception(f"Unexpected error loading solvers file: {e}")

    def load_file(self, filename: Union[str, Path]):
        with open(filename, encoding="utf-8") as file:
            if filename.endswith(".yaml"):
                file_data = yaml.load(file, Loader=yaml.FullLoader) 
            elif filename.endswith(".json"):
                file_data = json.load(file)
            else:
                self.logger.error(f"Invalid file format: {filename}")
                raise ValueError(f"Invalid file format: {filename}")

            # Merge current file data into existing solvers dictionary
            self.solvers.update(file_data)
            self.logger.info(f"Solvers file loaded and merged successfully from {filename}")

    def __call__(self):
        return self.solvers