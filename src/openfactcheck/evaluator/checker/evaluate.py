import io
import pandas as pd
from typing import Union
from importlib import resources as pkg_resources
from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score
from sklearn.metrics import classification_report, confusion_matrix

from openfactcheck import OpenFactCheck
from openfactcheck.templates import factchecker as templates_dir

# Import solver configuration templates
gold_claims_template_path = str(pkg_resources.files(templates_dir) / "gold/claims.jsonl")
gold_documents_template_path = str(pkg_resources.files(templates_dir) / "gold/documents.jsonl")

class CheckerEvaluator():
    """
    This class is used to evaluate the performance of a FactChecker.

    Parameters
    ----------
    input_path : Union[str, pd.DataFrame]
        The path to the CSV file or the DataFrame containing the FactChecker responses.
        The CSV file should have the following three columns:
        - label: The label assigned by the FactChecker. This should be a boolean value.
        - time: The time taken by the FactChecker to respond.
        - cost: The cost of the FactChecker response.
    eval_type : str
        The type of evaluation to perform. Either "claim" or "document".
    gold_path : str
        Optional. The path to the gold standard file. If not provided, the default gold standard file will be used.
        This is useful when evaluating the FactChecker on a different dataset.
    eval_type : str

    Attributes
    ----------
    input_path : Union[str, pd.DataFrame]
        The path to the CSV file or the DataFrame containing the FactChecker responses.
    gold_path : str
        The path to the gold standard file.
    eval_type : str
        The type of evaluation to perform. Either "claim" or "document".
    results : dict
        The evaluation results.
    confusion_matrix : numpy.ndarray
        The confusion matrix of the evaluation.
    classification_report : dict
        The classification report of the evaluation.

    Methods
    -------
    evaluate(input_path: Union[str, pd.DataFrame], eval_type: str, gold_path: str = ""):
        This function evaluates the performance of the FactChecker.
    evaluate_binary_classification(y_true, y_pred, pos_label="yes"):
        Evaluate the performance of a binary classification task.
    """
    def __init__(self, ofc: OpenFactCheck):
        """
        Initialize the FactCheckerEvaluator object.
        """
            
        # Set the attributes
        self.input_path = None
        self.gold_path = None
        self.eval_type = None
        self.results = None
        self.confusion_matrix = None
        self.classification_report = None

    @staticmethod
    def evaluate_binary_classification(y_true, y_pred, pos_label="yes"):
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, pos_label=pos_label)
        recall = recall_score(y_true, y_pred, pos_label=pos_label)
        F1 = f1_score(y_true, y_pred, pos_label=pos_label)

        metrics = {
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "F1": round(F1, 3),
        }
        return metrics

    def evaluate(self, input_path: Union[str, pd.DataFrame], eval_type: str, gold_path: str = ""):
        """
        This function evaluates the performance of the FactChecker.
        """
        # Set the input_path, gold_path, and eval_type attributes
        self.input_path = input_path
        self.gold_path = gold_path
        self.eval_type = eval_type

        if self.gold_path == "":
            if eval_type == "claims":
                self.gold_path = gold_claims_template_path
            elif eval_type == "documents":
                self.gold_path = gold_documents_template_path
            else:
                raise ValueError("Invalid evaluation type. Please provide a valid evaluation type.")

        # Load the gold standard file
        with open(self.gold_path, "r") as f:
            json_data = f.read()
        df_gold = pd.read_json(io.StringIO(json_data), lines=True)

        # Check if the input_path is a DataFrame
        if isinstance(self.input_path, pd.DataFrame):
            df_input = self.input_path
        else:
            # Read the CSV file
            df_input = pd.read_csv(self.input_path)

        # Check if the FactChecker responses have the correct number of columns
        assert len(df_input.columns) == 3
        
        # Check if the FactChecker responses have the correct column names
        assert df_input.columns[0] == "label", f"The first column should be 'label' but is {df_input.columns[0]}."
        assert df_input.columns[1] == "time", f"The second column should be 'time' but is {df_input.columns[1]}."
        assert df_input.columns[2] == "cost", f"The third column should be 'cost' but is {df_input.columns[2]}."
        
        # Get the gold labels and the predictions
        if self.eval_type == "claims":
            gold_labels = df_gold['claim_label'].to_list()
        elif self.eval_type == "documents":
            gold_labels = df_gold['response_label'].to_list()
        predictions = df_input[df_input.columns[0]].to_list()

        # Check if the number of gold labels and predictions are the same
        assert (len(gold_labels) == len(predictions)), "The number of gold labels and predictions should be the same."

        # Verify that the gold labels and predictions are boolean values
        assert all(isinstance(label, bool) for label in gold_labels), "The gold labels should be boolean values."
        assert all(isinstance(label, bool) for label in predictions), "The predictions should be boolean values."

        # evalaute performance
        r1 = self.evaluate_binary_classification(y_true=gold_labels, y_pred=predictions, pos_label=True)
        r2 = self.evaluate_binary_classification(y_true=gold_labels, y_pred=predictions, pos_label=False)

        # Calculate total time and cost
        total_time = 0
        total_cost = 0
        
        # Check if the time and cost columns are present in the FactChecker responses
        if "time" in df_input.columns[1]:
            total_time = df_input[df_input.columns[1]].astype(float).sum()
        
        # Check if the cost column is present in the FactChecker responses
        if "cost" in df_input.columns[2]:
            total_cost = df_input[df_input.columns[2]].astype(float).sum()

        self.results = {
            "True_as_positive": r1,
            "False_as_positive": r2,
            "total_time": total_time,
            "total_cost": total_cost,
            "num_samples": len(predictions)
        }

        # Calculate the confusion matrix
        self.confusion_matrix = confusion_matrix(y_true=gold_labels, y_pred=predictions, labels=[True, False])

        # Calculate the classification report
        self.classification_report = classification_report(gold_labels, predictions)

        return self.results