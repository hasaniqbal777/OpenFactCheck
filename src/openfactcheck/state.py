from typing import Any, Optional

from openfactcheck.utils.logging import get_logger

# Get the logger
logger = get_logger(__name__)


class FactCheckerState:
    """
    A class to manage the state of a fact-checking system.

    It holds a question and its corresponding response, and provides methods
    to set and get these attributes dynamically.
    """

    def __init__(self, question: Optional[str] = None, response: Optional[str] = None) -> None:
        """
        Initialize the FactCheckerState object.

        Parameters
        ----------
        question : Optional[str]
            The question to be fact-checked.
        response : Optional[str]
            The response to the question.
        """
        self.question: Optional[str] = question
        self.response: Optional[str] = response

    def set(self, name: str, value: Any) -> None:
        """
        Set an attribute of the state object.

        Parameters
        ----------
        name : str
            The name of the attribute to set.
        value : Any
            The value to set for the attribute.
        """
        if hasattr(self, name):
            logger.warning(f"Modifying existing attribute '{name}'")
        setattr(self, name, value)

    def get(self, name: str) -> Any:
        """
        Get an attribute of the state object.

        Parameters
        ----------
        name : str
            The name of the attribute to retrieve.

        Returns
        -------
        Any
            The value of the requested attribute.

        Raises
        ------
        ValueError
            If the attribute does not exist.
        """
        if not hasattr(self, name):
            raise ValueError(f"Attribute '{name}' does not exist")
        return getattr(self, name)

    def __str__(self) -> str:
        """
        Return a string representation of the state object.

        Returns
        -------
        str
            A string representation of the object's dictionary.
        """
        return str(self.__dict__)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a dictionary representation of the state object.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the object's attributes.
        """
        return self.__dict__
