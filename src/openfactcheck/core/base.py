from openfactcheck.lib.logger import logger
from openfactcheck.lib.config import OpenFactCheckConfig

class OpenFactCheck:
    def __init__(self, config: OpenFactCheckConfig):
        self.logger = logger
        self.config = config

        self.logger.info("OpenFactCheck initialized")

if __name__ == "__main__":
    config = OpenFactCheckConfig()
    ofc = OpenFactCheck(config)