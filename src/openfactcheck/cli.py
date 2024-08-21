import argparse

from openfactcheck import OpenFactCheck
from openfactcheck.lib import OpenFactCheckConfig

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

    def callback(index, sample_name, solver_name, input_name, output_name, input, output, continue_run):
        print(f"Callback: {index}, {sample_name}, {solver_name}, {input_name}, {output_name}, {input}, {output}, {continue_run}")

    config = OpenFactCheckConfig(args.config_path)
    results = OpenFactCheck(config).ResponseEvaluator.evaluate("Abraham Lincoln was the first president of the United States.",
                                                               callback=callback)