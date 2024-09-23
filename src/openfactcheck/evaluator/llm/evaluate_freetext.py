import os
import time
import json
import math
import pandas as pd
import seaborn as sns
from hashlib import md5
import matplotlib.pyplot as plt

from openfactcheck import OpenFactCheck
from openfactcheck.utils.logging import get_logger

# Get the logger
logger = get_logger(__name__)

class FreeTextEvaluator():
    def __init__(self, ofc: OpenFactCheck):
        """
        Initialize the FreeTextEvaluator object.
        """

        self.logger = logger
        
        # Set the OpenFactCheck object
        self.ofc = ofc

    def calculate_price(self, num_claims, cost_openai=0.015, cost_serper=0.001):
        """
        Calculate the cost (in USD) of the API calls for the free-text experiment.
        2x API calls per claim
        
        Parameters
        ----------
        numClaims : int
            The number of claims in the free-text experiment.
        costOpenAI : float
            The cost of the OpenAI API call.
        costSerper : float
            The cost of the Serper API call.
        """
        return num_claims * 2 * (cost_openai + cost_serper)

    def sum_all_elements(self, obj: dict):
        """
        Sum all elements of an object.
        """
        ret = 0
        for k, v in obj.items():
            ret += v
        return ret

    def assess_freetext(self, output_path: str):
        """
        Assess the free-text experiment, i.e., the number and type of claims, this is, Exact Matching (EM).
        """

        # Initialize the return object
        claims = {
            "num_false_claims": 0,
            "num_mixed_claims": 0,
            "num_true_claims": 0,
            "num_undefined_claims": 0
        }
        path = output_path + '/evidence_stance.json'
        if not os.path.exists(path):
            return False
        df = pd.read_json(path, lines=False)
        dataobj = json.loads(df.to_json())

        # Assess the claims
        for k, v in dataobj.items():
            # If stance contains definitive or mixed, then it is false
            if "definitive" in v["stances"][0] or "mixed" in v["stances"][0]:
                claims["num_mixed_claims"] += 1
            elif "factual" in v["stances"][0] or "confirm" in v["stances"][0]:
                claims["num_true_claims"] += 1
            elif "error" in v["stances"][0] or "incorrect" in v["stances"][0] or "false" in v["stances"][0]:
                claims["num_false_claims"] += 1
            else:
                claims["num_undefined_claims"] += 1

        return claims
    
    def read_evaluations(self):
        """
        Read the evaluations from the output directory.
        """
        data = []
        for dirname in os.listdir(self.base_output_path):
            dirpath = os.path.join(self.base_output_path, dirname)
            if os.path.isdir(dirpath):
                if os.path.exists(os.path.join(dirpath, 'evaluation.json')):
                    with open(os.path.join(dirpath, 'evaluation.json'), 'r') as f:
                        data.append(json.load(f))
        return data
    
    def read_results(self, evaluations):
        """
        Read the results from the evaluations.
        """
        # Calculate the total cost and time
        (costs, time_costs, true_claims, false_claims, mixed_claims, undefined_claims, total_claims) = (0, 0, 0, 0, 0, 0, 0)
        for evaluation in evaluations:
            total_claims += 1

            # Calculate the costs
            costs += self.calculate_price(self.sum_all_elements(evaluation["claims"]))
            time_costs += evaluation["end"] - evaluation["start"]

            # Calculate the number of claims
            false_claims += evaluation["claims"]["num_false_claims"]
            mixed_claims += evaluation["claims"]["num_mixed_claims"]
            undefined_claims += evaluation["claims"]["num_undefined_claims"]
            if (evaluation["claims"]["num_false_claims"] + evaluation["claims"]["num_mixed_claims"]) == 0:
                true_claims += 1
        
        return{
            "Claims": total_claims,
            "True Claims": true_claims,
            "False Claims": false_claims,
            "Mixed Claims": mixed_claims,
            "Undefined Claims": undefined_claims,
            "Cost (USD)": costs,
            "Time (ms)": time_costs,
            "Percentage of True Responses": round(true_claims / total_claims if total_claims != 0 else 0, 3) * 100,
            "Percentage of False Responses": round(false_claims / total_claims if total_claims != 0 else 0, 3) * 100
        }
    
    def freetext_barplot(self, results, fig_path: str = "", save: bool = False):
        """
        Create a barplot for the free-text evaluation results, ensuring full row utilization.

        Parameters
        ----------
        results : dict
            The dictionary of results from the free-text evaluation.
        fig_path : str
            The path to save the figure.
        save : bool
            Whether to save the figure or not.
        """

        # Exclude "Claims" and prepare data
        metrics = list(next(iter(results.values())).keys())
        datasets = list(results.keys())

        # Prepare plot data and handle specific conversions
        plot_data = {}
        for metric in metrics:
            if metric == "Claims":
                continue
            if metric == "Time (s)":
                plot_data["Time (min)"] = [results[dataset][metric] / (1000 * 60) for dataset in datasets] 
            elif metric == "Percentage of True Responses":
                plot_data[metric] = [results[dataset][metric] for dataset in datasets]
            else:
                plot_data[metric] = [results[dataset][metric] for dataset in datasets]

        # Define the layout
        total_metrics = len(plot_data)
        ncols = 4  # Maximum number of columns per row
        nrows = (total_metrics + ncols - 1) // ncols  # Calculate the required number of rows

        # Creating subplots
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 5 * nrows))
        fig.suptitle('Performance on Free-Text Dataset')

        # Flatten axes array if more than one row
        axes = axes.flatten() if nrows > 1 else [axes]

        # Generate each bar plot and deactivate unused axes
        for ax, (metric, values) in zip(axes[:total_metrics], plot_data.items()):
            bars = ax.bar(datasets, values, color=sns.color_palette("rocket", n_colors=len(datasets)))
            ax.set_title(metric)
            ax.set_xticks(range(len(datasets)))
            ax.set_xticklabels(datasets, rotation=45, ha="right")
            ax.set_ylabel(metric)
            
            # Annotate each bar with its value
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2),
                        ha='center', va='bottom')
                
            # Set y-axis limits to accommodate annotations
            ax.set_ylim(0, max(values) * 1.1)

        # Hide unused axes
        for ax in axes[total_metrics:]:
            ax.axis('off')

        # Adjust layout to prevent overlap
        plt.tight_layout()

        if save:
            plt.savefig(os.path.join(fig_path, "freetext_barplot.pdf"), format="pdf")
            plt.savefig(os.path.join(fig_path, "freetext_barplot.png"), format="png")

        # Return the figure
        return fig  


    def evaluate_freetext(self, llm_responses: list, model_name: str, run_id: str):
        """
        Evaluate the LLM responses on free-text datasets.
        Currently, FactoolQA, FELM-WK, FactCheck-Bench and FactScore-Bio datasets are included by default.

        Parameters
        ----------
        llm_responses : list
            The LLM responses on the free-text datasets.
        """

        # Set the pipeline for the FreeTextEvaluator
        pipeline = [
            "all_pass_abstain_detector",
            "factool_decontextualizer",
            "factool_evidence_retriever",
            "factool_claim_examiner",
            "factool_post_editor",
            "concat_response_generator"
        ]

        # Initialize the pipeline manually
        self.ofc.init_pipeline_manually(pipeline=pipeline)

        # Get the dataset name and create DataFrame
        dataset = llm_responses[0]['source']
        llm_responses = pd.DataFrame(llm_responses)

        # Save the base_output_path
        self.base_output_path = f"{self.ofc.output_path}/llm_evaluator/{run_id}/{dataset}"

        # Evaluate the LLM responses
        for idx, response in llm_responses.iterrows():
            
            prompt = response['prompt']
            response = response['response']

            # Set the output path
            output_path = f"{self.base_output_path}/{idx}_{md5(prompt.encode()).hexdigest()}"
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # If the file was already evaluated, skip it
            if (os.path.exists(f"{self.base_output_path}/{idx}_{md5(prompt.encode()).hexdigest()}/evaluation.json")):
                logger.info(f"Skipping the evaluation for prompt {idx} as it was already evaluated.")
                continue

            # TODO: This should work (but it doesn't)
            # self.ofc.init_solver("factool_evidence_retriever", {"path_save_evidence": f"{output_path}/evidence.json"})

            # Evaluate the response
            start = time.time() * 1000
            _result = self.ofc.ResponseEvaluator.evaluate(
                response=response,
                prompt=prompt,
                sample_name=f"llm_evaluator/{run_id}/truth/{dataset}/{idx}"
            )
            end = time.time() * 1000

            # TODO: This is a workaround for the TODO above (move the evidence.json file)
            if os.path.exists("evidence.json"):
                os.rename("evidence.json", f"{output_path}/evidence.json")
            if os.path.exists("evidence_stance.json"):
                os.rename("evidence_stance.json", f"{output_path}/evidence_stance.json")

            # Assess the free-text experiment
            claims = self.assess_freetext(output_path)
            if not claims:
                self.logger.warning(f'Error in assessing experiment for prompt {idx}')
                continue

            # Persist the output
            result = {}
            result["start"] = math.floor(start)
            result["end"] = math.floor(end)
            result["llm"] = model_name
            result["dataset"] = llm_responses["source"][idx]
            result["prompt"] = prompt
            result["claims"] = claims
            result["result"] = _result

            # Save the result
            logger.debug(f"Saving the result for prompt {idx} in {output_path}/evaluation.json")
            with open(f"{output_path}/evaluation.json", "w") as f:
                json.dump(result, f, indent=4)

            logger.info(f"Evaluated the LLM response for prompt {idx} in {end - start} ms.")

        logger.info(f"Finished evaluating the LLM responses for the {dataset} dataset.")

        # Read the outputs
        evaluations = self.read_evaluations()

        # Read the results
        results = self.read_results(evaluations)
       
        return results, evaluations









