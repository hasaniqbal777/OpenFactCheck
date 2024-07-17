import json
from pathlib import Path
from typing import Union

from .logger import logger

class OpenFactCheckConfig:
    def __init__(self, filename: Union[str, Path] = "config.json"):
        # Setup Logger
        self.logger = logger

        self.filename = filename

        try:
            # Loading Config File
            with open(self.filename, encoding="utf-8") as file:
                self.filename = json.load(file)

        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.filename}")
            raise FileNotFoundError(f"Config file not found: {self.filename}")
        
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.filename}")
            raise ValueError(f"Invalid JSON in config file: {self.filename}")
        
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            raise Exception(f"Error loading config file: {e}")
        