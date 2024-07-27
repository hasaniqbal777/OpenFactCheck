import argparse

from openfactcheck.core.base import OpenFactCheck
from openfactcheck.lib.config import OpenFactCheckConfig

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize OpenFactCheck with custom configuration.')
    
    # Add arguments here, example:
    parser.add_argument("--config-path", 
                        type=str, 
                        help="Config File Path",
                        default="config.json")
    
    # Parse arguments from command line
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()

    ofc = OpenFactCheck(OpenFactCheckConfig(args.config_path))