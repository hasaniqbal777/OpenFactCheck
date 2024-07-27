import os
import json
import yaml
import datasets
import transformers
from pathlib import Path
from typing import Union
from collections import namedtuple
from importlib import resources as pkg_resources

from openfactcheck.lib.logger import logger, set_logger_level
from openfactcheck.lib.errors import ConfigValidationError
from openfactcheck import templates as solver_config_templates_dir
from openfactcheck import solvers as solver_templates_dir

# Import solver configuration templates
solver_config_templates_path = pkg_resources.files(solver_config_templates_dir) / 'solver_configs'
with solver_config_templates_path as solver_config_templates_dir_path:
    solver_config_template_files = [str(f) for f in solver_config_templates_dir_path.iterdir()]

# Import default solvers
# TODO: Currently, only webservice solvers are supported as default solvers
solver_templates_paths = [
    str(pkg_resources.files(solver_templates_dir) / 'webservice')
]

class OpenFactCheckConfig:
    """
    Class to load the OpenFactCheck configuration from a JSON or YAML file.

    Parameters
    ----------
    filename: str, Path
        The path to the configuration file.

    Attributes
    ----------
    retries: int
        Number of retries for the pipeline components.
    pipeline: namedtuple
        Namedtuple containing the pipeline components.
    solver_configs: dict
        Dictionary containing the solver configurations.
    solver_paths: dict
        Dictionary containing the paths to the solver models.
    output_path: str
        Path to the output directory.
    secrets: namedtuple
        Namedtuple containing the API keys.
    verbose: str
        The verbosity level for the logger.

    Methods
    -------
    solver_configuration(solver: str = None) -> dict:
        Get the solver configuration for a specific solver or all solvers.
    validate():
        Validate the configuration file

    Examples
    --------
    >>> config = OpenFactCheckConfig("config.json")
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
        self.config = None
        self.retries = 0
        self.pipeline = None
        self.solver_configs = None
        self.solver_paths = None
        self.output_path = None
        self.secrets = None
        self.verbose = ""

        try:
            # Check if the file exists
            if Path(self.filename).exists():
                # Loading Config File
                with open(self.filename, encoding="utf-8") as file:
                    self.config = json.load(file)
                    self.logger.info(f"Config file loaded successfully from {self.filename}")
            else:
                # Create a dummy configuration file
                self.logger.warning(f"Config file not found: {self.filename}")
                self.config = {}

            # Initialize Retries
            if 'retries' in self.config:
                self.retries = self.config['retries']
            else:
                self.logger.warning("No retries found in the configuration file. Using default value of 3.")
                self.retries = 3
                
            # Initialize template solvers along with the user-defined solvers
            # User defined solvers will override the template solvers
            if 'solver_configs' in self.config:
                self.solver_configs = SolversConfig(solver_config_template_files + self.config['solver_configs'])()
            else:
                self.logger.warning("No solver configurations found in the configuration file. Using default templates only.")
                self.solver_configs = SolversConfig(solver_config_template_files)()

            # Initialize template solver paths along with the user-defined solver paths
            if 'solver_paths' in self.config:
                self.solver_paths = solver_templates_paths + self.config['solver_paths']
            else:
                self.logger.warning("No solver paths found in the configuration file. Using default solver paths only.")
                self.solver_paths = solver_templates_paths

            # Initialize Output Path
            if 'output_path' in self.config:
                self.output_path = self.config['output_path']
                os.makedirs(self.output_path, exist_ok=True)
            else:
                self.logger.warning("No output path found in the configuration file. Using default output path 'tmp/output'.")
                self.output_path = "tmp/output"
                os.makedirs(self.output_path, exist_ok=True)
            
            # Initialize Pipeline config
            if 'pipeline' in self.config:
                self.pipeline = Pipeline(claimprocessor=self.config['pipeline']['claimprocessor'],
                                            retriever=self.config['pipeline']['retriever'],
                                            verifier=self.config['pipeline']['verifier'])
            else:
                if self.solver_configs:
                    solvers = list(self.solver_configs.keys())
                    claimprocessor = None
                    retriever = None
                    verifier = None
                    for solver in solvers:
                        if 'claimprocessor' in solver:
                            claimprocessor = solver
                        if 'retriever' in solver:
                            retriever = solver
                        if 'verifier' in solver:
                            verifier = solver
                        if claimprocessor and retriever and verifier:
                            break
                    self.pipeline = Pipeline(claimprocessor=claimprocessor, retriever=retriever, verifier=verifier)
                    self.logger.warning(f"No pipeline found in the configuration file. Using first solver as default pipeline. ClaimProcessor: {claimprocessor}, Retriever: {retriever}, Verifier: {verifier}")

            # Initialize Secrets config
            if 'secrets' in self.config:
                self.secrets = Secrets(openai_api_key=self.config['secrets']['openai_api_key'],
                                        serper_api_key=self.config['secrets']['serper_api_key'],
                                        azure_search_key=self.config['secrets']['azure_search_key'])
            else:
                self.logger.warning("No secrets found in the configuration file. Make sure to set the environment variables.")
                self.secrets = Secrets(openai_api_key=None, serper_api_key=None, azure_search_key=None)
        
            # Initialize Environment Variables
            if self.secrets.openai_api_key:
                os.environ['OPENAI_API_KEY'] = self.secrets.openai_api_key
            if self.secrets.serper_api_key:
                os.environ['SERPER_API_KEY'] = self.secrets.serper_api_key
            if self.secrets.azure_search_key:
                os.environ['AZURE_SEARCH_KEY'] = self.secrets.azure_search_key

            # Initialize Verbose
            if 'verbose' in self.config:
                self.verbose = self.config['verbose']
                set_logger_level(self.logger, self.verbose)
            else:
                self.logger.warning("No verbose level found in the configuration file. Using default level 'INFO'.")
                self.verbose = "INFO"
                set_logger_level(self.logger, "INFO")

            # Validate Configuration
            self.validate()

            # Disable Transformers and Datasets logging
            transformers.logging.set_verbosity_error()
            datasets.logging.set_verbosity_error()

        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.filename}")
            raise FileNotFoundError(f"Config file not found: {self.filename}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.filename}")
            raise ValueError(f"Invalid JSON in config file: {self.filename}")
        
        except ConfigValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise ConfigValidationError(f"Configuration validation failed: {e}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error loading config file: {e}")
            raise Exception(f"Unexpected error loading config file: {e}")
        
    def validate(self):
        """
        Validate the configuration file.

        Raises
        ------
        ValueError
            If the configuration file is invalid.

        Examples
        --------
        >>> config = OpenFactCheckConfig("config.json")
        >>> config.validate()
        """
        # Check for environment variables
        if 'OPENAI_API_KEY' not in os.environ:
            self.logger.warning("OPENAI_API_KEY environment variable not found.")
            raise ConfigValidationError("OPENAI_API_KEY environment variable not found.")
        if 'SERPER_API_KEY' not in os.environ:
            self.logger.warning("SERPER_API_KEY environment variable not found.")
            raise ConfigValidationError("SERPER_API_KEY environment variable not found.")
        if 'AZURE_SEARCH_KEY' not in os.environ:
            self.logger.warning("AZURE_SEARCH_KEY environment variable not found.")
            raise ConfigValidationError("AZURE_SEARCH_KEY environment variable not found.")

        
    
    def solver_configuration(self, solver: str = None) -> dict:
        """
        Get the solver configuration for a specific solver or all solvers.

        Parameters
        ----------
        solver: str
            The name of the solver to get the configuration for.
            If not provided, returns the configuration for all solvers.

        Returns
        -------
        dict
            The configuration for the specified solver or all solvers.

        Raises
        ------
        ConfigValidationError
            If the configuration validation fails.

        Examples
        --------
        >>> config = OpenFactCheckConfig("config.json")
        >>> config.solver_configuration()
        >>> config.solver_configuration("factcheckgpt_claimprocessor")
        """
        if solver:
            if solver in self.solver_configs:
                return self.solver_configs[solver]
            else:
                self.logger.error(f"Solver not found: {solver}")
                raise ValueError(f"Solver not found: {solver}")
        else:
            return self.solver_configs
                

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
                self.load_config(self.filename_s)
            elif isinstance(self.filename_s, list):
                for filename in self.filename_s:
                    self.load_config(filename)
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

    def load_config(self, filename: Union[str, Path]):
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

            # Log the loaded configuration pattern
            if 'template' in filename:
                self.logger.info(f"Template solver configuration loaded: {filename.split('/')[-1]}")
            else:
                self.logger.info(f"User-defined solver configuration loaded from: {filename}")

    def __call__(self):
        return self.solvers