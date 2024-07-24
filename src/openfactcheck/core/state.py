import logging

class FactCheckerState:
    """
    A class to manage the state of a fact checking system. It holds a question 
    and its corresponding response, and provides methods to set and get these 
    attributes dynamically.

    Parameters
    ----------
    question : str
        The question to be fact-checked.
    response : str
        The response to the question.
    """
    def __init__(self, question: str = None, response: str = None):
        """
        Initialize the FactCheckerState object.
        """
        self.question: str = question
        self.response: str = response

    def set(self, name, value):
        """
        Set an attribute of the state object.
        """
        if hasattr(self, name):
            logging.warning(f"FactCheckerState.set: Modifying existing attribute {name}")
        setattr(self, name, value)

    def get(self, name):
        """
        Get an attribute of the state object.
        """
        if not hasattr(self, name):
            raise ValueError(f"FactCheckerState.get: Attribute {name} does not exist")
        return getattr(self, name, None)

    def __str__(self):
        """
        Return a string representation of the state object.
        """
        return str(self.__dict__)

    def to_dict(self):
        """
        Return a dictionary representation of the state object.
        """
        return self.__dict__
