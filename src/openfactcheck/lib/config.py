import os
import json
import yaml
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from collections import namedtuple
from importlib import resources as pkg_resources


from openfactcheck.utils.logging import get_logger, set_verbosity
from openfactcheck.errors import ConfigValidationError
from openfactcheck import templates as solver_config_templates_dir
from openfactcheck import solvers as solver_templates_dir

# Import solver configuration templates
solver_config_templates_path = str(pkg_resources.files(solver_config_templates_dir) / "solver_configs")
solver_config_template_files = [str(f) for f in Path(solver_config_templates_path).iterdir()]


# Import default solvers
# TODO: Currently, only webservice solvers are supported as default solvers
solver_templates_paths = [
    str(pkg_resources.files(solver_templates_dir) / "webservice"),
    str(pkg_resources.files(solver_templates_dir) / "factool"),
]

# Load environment variables from .env file
load_dotenv()


class OpenFactCheckConfig:
    """
    Class to load the OpenFactCheck configuration from a JSON or YAML file.

    Parameters
    ----------
    filename_or_path: str or path object
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
    For loading the default configuration file 'config.json':
    >>> config = OpenFactCheckConfig()

    For loading the configuration file from a specific path or filename:
    >>> config = OpenFactCheckConfig("config.json")

    For loading the configuration file and validating it:
    >>> config = OpenFactCheckConfig("config.json")
    >>> config.validate()
    """

    def __init__(self, filename_or_path: str | Path = "config.json"):
        # Setup Logger
        self.logger = get_logger()

        # Set the filename or path
        self.filename_or_path = filename_or_path

        # Define namedtuple structures
        Secrets = namedtuple("Secrets", ["openai_api_key", "serper_api_key", "scraper_api_key"])

        # Define Attributes
        self.config: dict = {}
        self.retries: int = 3
        self.pipeline: list = []
        self.solver_configs: dict[Any, Any] = SolversConfig(solver_config_template_files)()
        self.solver_paths: dict[str, list[str]] = {"default": solver_templates_paths, "user_defined": []}
        self.output_path: str = "tmp/output"
        self.secrets: Secrets = Secrets(openai_api_key=None, serper_api_key=None, scraper_api_key=None)
        self.verbose = "WARNING"

        try:
            # Check if the file exists
            if Path(self.filename_or_path).exists():
                # Loading Config File
                with open(self.filename_or_path, encoding="utf-8") as file:
                    self.config = json.load(file)
                    self.logger.info(f"Config file loaded successfully from {self.filename_or_path}")
            else:
                # Create a dummy configuration file
                self.logger.warning(f"Config file not found: {self.filename_or_path}")

            # Initialize Retries
            if "retries" in self.config:
                self.retries = self.config["retries"]
            else:
                self.logger.warning("No retries found in the configuration file. Using default value of 3.")

            # Initialize template solvers along with the user-defined solvers
            # User defined solvers will override the template solvers
            if "solver_configs" in self.config:
                self.solver_configs = SolversConfig(solver_config_template_files + self.config["solver_configs"])()
            else:
                self.logger.warning(
                    "No solver configurations found in the configuration file. Using default templates only."
                )

            # Initialize template solver paths along with the user-defined solver paths
            if "solver_paths" in self.config:
                self.solver_paths = {
                    "default": solver_templates_paths,
                    "user_defined": self.config["solver_paths"],
                }
            else:
                self.logger.warning(
                    "No solver paths found in the configuration file. Using default solver paths only."
                )

            # Initialize Output Path
            if "output_path" in self.config:
                self.output_path = self.config["output_path"]
                os.makedirs(self.output_path, exist_ok=True)
            else:
                self.logger.warning(
                    "No output path found in the configuration file. Using default output path 'tmp/output'."
                )
                self.output_path = "tmp/output"
                os.makedirs(self.output_path, exist_ok=True)

            # Initialize Pipeline config
            if "pipeline" in self.config:
                self.pipeline = self.config["pipeline"]
            else:
                if self.solver_configs:
                    solvers = list(self.solver_configs.keys())
                    claimprocessor = "factool_claimprocessor" if "factool_claimprocessor" in solvers else None
                    retriever = "factool_retriever" if "factool_retriever" in solvers else None
                    verifier = "factcheckgpt_verifier" if "factcheckgpt_verifier" in solvers else None
                    for solver in solvers:
                        if claimprocessor and retriever and verifier:
                            break
                        if "claimprocessor" in solver:
                            claimprocessor = solver
                        if "retriever" in solver:
                            retriever = solver
                        if "verifier" in solver:
                            verifier = solver
                    self.pipeline = [claimprocessor, retriever, verifier]
                    self.logger.warning(
                        f"No pipeline found in the configuration file. Using first solver as default pipeline. ClaimProcessor: {claimprocessor}, Retriever: {retriever}, Verifier: {verifier}"
                    )

            # Initialize Secrets config
            if "secrets" in self.config:
                self.secrets = Secrets(
                    openai_api_key=self.config["secrets"]["openai_api_key"],
                    serper_api_key=self.config["secrets"]["serper_api_key"],
                    scraper_api_key=self.config["secrets"]["scraper_api_key"],
                )
            else:
                self.logger.warning(
                    "No secrets found in the configuration file. Make sure to set the environment variables."
                )

            # Initialize Environment Variables
            if self.secrets.openai_api_key:
                os.environ["OPENAI_API_KEY"] = self.secrets.openai_api_key
            if self.secrets.serper_api_key:
                os.environ["SERPER_API_KEY"] = self.secrets.serper_api_key
            if self.secrets.scraper_api_key:
                os.environ["SCRAPER_API_KEY"] = self.secrets.scraper_api_key

            # Initialize Verbose
            if "verbose" in self.config:
                self.verbose = self.config["verbose"]
                set_verbosity(self.verbose)
            else:
                self.logger.warning("No verbose level found in the configuration file. Using default level 'WARNING'.")

            # Validate Configuration
            self.validate()

        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.filename_or_path}")
            raise FileNotFoundError(f"Config file not found: {self.filename_or_path}")

        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.filename_or_path}")
            raise ValueError(f"Invalid JSON in config file: {self.filename_or_path}")

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
        if "OPENAI_API_KEY" not in os.environ:
            self.logger.warning("OPENAI_API_KEY environment variable not found.")
            raise ConfigValidationError("OPENAI_API_KEY environment variable not found.")
        if "SERPER_API_KEY" not in os.environ:
            self.logger.warning("SERPER_API_KEY environment variable not found.")
            raise ConfigValidationError("SERPER_API_KEY environment variable not found.")
        if "SCRAPER_API_KEY" not in os.environ:
            self.logger.warning("SCRAPER_API_KEY environment variable not found.")
            raise ConfigValidationError("SCRAPER_API_KEY environment variable not found.")

    def solver_configuration(self, solver: str | None = None) -> dict:
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
    A class to load solver configurations from one or more JSON or YAML files.

    This class reads solver configurations from specified files, merges them,
    and provides access to the combined configuration as a dictionary.

    Parameters
    ----------
    filename_or_paths : str | Path | list[str | Path]
        The path or list of paths to the solver configuration files.

    Attributes
    ----------
    solvers : dict[Any, Any]
        Dictionary containing the merged solver configurations.

    Examples
    --------
    Load solver configurations from a single file:

    >>> solvers = SolversConfig("solvers.yaml")
    >>> config = solvers()

    Load solver configurations from multiple files:

    >>> solvers = SolversConfig(["solvers1.json", "solvers2.yaml"])
    >>> config = solvers()

    Access the solvers dictionary:

    >>> config = solvers()
    """

    def __init__(self, filename_or_path_s: str | Path | list[str] | list[Path]) -> None:
        """
        Initialize the SolversConfig class.

        Parameters
        ----------
        filename_or_path_s: str or path object or list of str or path objects
            The path to the solvers configuration or a list of paths to multiple solvers configurations.
        """
        # Setup Logger
        self.logger = get_logger()

        # Set the filename or path
        self.filename_or_path_or_path_s = filename_or_path_s

        # Define Attributes
        self.solvers: dict[Any, Any] = {}

        try:
            if isinstance(self.filename_or_path_or_path_s, (str, Path)):
                self.__load_config(self.filename_or_path_or_path_s)
            elif isinstance(self.filename_or_path_or_path_s, list):
                self.__load_configs(self.filename_or_path_or_path_s)
            else:
                self.logger.error(f"Invalid filename type: {type(self.filename_or_path_or_path_s)}")
                raise ValueError(f"Invalid filename type: {type(self.filename_or_path_or_path_s)}")

        except FileNotFoundError:
            self.logger.error(f"Solvers file not found: {self.filename_or_path_or_path_s}")
            raise FileNotFoundError(f"Solvers file not found: {self.filename_or_path_or_path_s}")
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in solvers file: {self.filename_or_path_or_path_s}")
            raise ValueError(f"Invalid JSON in solvers file: {self.filename_or_path_or_path_s}")
        except Exception as e:
            self.logger.error(f"Unexpected error loading solvers file: {e}")
            raise Exception(f"Unexpected error loading solvers file: {e}")

    def __load_config(self, filename_or_path: str | Path) -> None:
        # Ensure filename is a string when performing string operations
        filename = str(filename_or_path)

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
            if "template" in filename:
                self.logger.info(f"Template solver configuration loaded: {filename.split('/')[-1]}")
            else:
                self.logger.info(f"User-defined solver configuration loaded from: {filename}")

    def __load_configs(self, filenames: list[str] | list[Path]) -> None:
        for filename in filenames:
            self.__load_config(filename)

    def __call__(self) -> dict[Any, Any]:
        return self.solvers
