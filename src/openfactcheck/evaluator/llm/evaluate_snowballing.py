import os
import re
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

class SnowballingEvaluator():
    """
    Evaluate the LLM responses on the Snowballing dataset.

    Parameters
    ----------
    LLMEvaluator : class
        The LLMEvaluator class.

    Methods
    -------
    evaluate_snowballing(llm_responses: list):
        Evaluate the LLM responses on the Snowballing dataset
    snowballing_barplot(result: dict, fig_path: str, save: bool = False):
        Create a bar plot of the accuracy of the LLM responses on the Snowballing dataset
        for each topic and the overall accuracy.
    get_boolean(response: str, strict=False):
        Get a boolean value from the response.
    """
    def __init__(self):
        pass

    def get_boolean(self, response: str, strict=False):
        """
        Get a boolean value from the response.
        
        """
        low_response = response.lower()
        if strict:
            if low_response.startswith("yes"):
                return True
            elif low_response.startswith("no"):
                return False
            return None
        else:
            # Check if the response contains any of the specified words
            pattern = r"{}".format("|".join(["n't", "no"]))
            if bool(re.search(pattern, response, re.IGNORECASE)):
                return False
            else:
                return True

    def snowballing_barplot(self, result: dict, fig_path: str = "", save: bool = False):
        """
        Create a bar plot of the accuracy of the LLM responses on the Snowballing dataset
        for each topic and the overall accuracy.

        Parameters
        ----------
        cresult : dict
            The evaluation results for the LLM responses on the Snowballing dataset
        fig_path : str
            The path to save the figure.
        save : bool, optional
            Whether to save the figure, by default True.
        """

        # Data
        items = result.keys()

        # Extract the accuracy values for each topic
        values = [round(v["accuracy"], 2) for k, v in result.items()]

        # Create a new figure
        fig, ax = plt.subplots()

        # Plotting
        bars = sns.barplot(x=items, y=values, palette="rocket", hue=items, ax=ax)

        # Adding values on top of each bar
        for bar in bars.patches:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), 
                    f'{bar.get_height():.2f}',
                    ha='center', 
                    va='bottom', 
                    color='black', 
                    rotation='horizontal')
            
        # Rotating x-axis tick labels
        plt.xticks(rotation=20) 

        # Set y-axis limits to accommodate annotations
        plt.ylim((0, max(values) + 0.1)) 

        # Adding labels and title
        plt.xlabel("Topics")
        plt.ylabel("Accuracy")
        plt.title("Performance on Snowballing Dataset.")

        if save:
            # Save the figure
            plt.tight_layout()
            plt.savefig(os.path.join(fig_path, "snowballing_barplot.pdf"), format="pdf")
            plt.savefig(os.path.join(fig_path, "snowballing_barplot.png"), format="png")
        
        # Return the figure
        return fig     

    def snowballing_cm(self, labels: list, preds: list, fig_path: str = "", save: bool = False):
        """
        Create a confusion matrix for the Snowballing dataset.

        Parameters
        ----------
        labels : list
            The true labels.
        preds : list
            The predicted labels.
        fig_path : str
            The path to save the figure.
        save : bool, optional
            Whether to save the figure, by default True.
        """

        # Create a new figure
        fig, ax = plt.subplots()

        # Plotting
        cm = sns.heatmap(confusion_matrix(labels, preds), annot=True, fmt="d", cmap="Blues", ax=ax)

        # Adding labels and title
        plt.xticks(ticks=[0.5, 1.5], labels=["True", "False"])
        plt.yticks(ticks=[0.5, 1.5], labels=["True", "False"])
        plt.ylabel("True label")
        plt.xlabel("Predicted label")
        plt.title("Confusion Matrix on Snowballing dataset.")

        if save:
            # Save the figure
            plt.tight_layout()
            plt.savefig(os.path.join(fig_path, "snowballing_cm.pdf"), format="pdf")
            plt.savefig(os.path.join(fig_path, "snowballing_cm.png"), format="png")

        # Return the figure
        return fig       
        
    def evaluate_snowballing(self, llm_responses: list):
        """
        Evaluate the LLM responses on the Snowballing dataset.
        """
        
        # Store evaluation results for three specific topics and aggregate results 
        # for the entire dataset, indexed by topic names.
        results = {} 

        # Define the ground truth answers for the three specific topics.
        topic_answers = {
            "Primality Testing": True,
            "US Senator Search": True,
            "Graph Connectivity-Flight Search": False,
        }

        # Store the responses for each topic.
        topic_responses = {}
        for key in topic_answers:
            topic_responses[key] = []

        # Store the responses for each topic.
        for item in llm_responses:
            topic_responses[item["topic"]].append(self.get_boolean(item["response"]))

        # Evaluate the LLM responses
        labels, preds = [], []
        for key in topic_answers:
            # Evaluate the responses for each topic.
            y_true = [topic_answers[key]] * len(topic_responses[key])
            y_pred = topic_responses[key]
            results[key] = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

            # Aggregate the results for the entire dataset.
            labels += [topic_answers[key]] * len(topic_responses[key])
            preds += topic_responses[key]

        # Evaluate the responses for the entire dataset.
        results["All"] = classification_report(labels, preds, output_dict=True, zero_division=0)

        return results, labels, preds