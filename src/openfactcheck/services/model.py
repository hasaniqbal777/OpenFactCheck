from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Optional


class DynamoDBBaseModel(BaseModel, ABC):
    """
    Base model for DynamoDB items, requiring a primary key (PK).
    Optional sort key (SK) and global secondary index partition key (GS1PK) can be defined.
    """

    @property
    @abstractmethod
    def PK(self) -> str:
        """Primary Key for DynamoDB storage. Must be implemented by subclasses."""
        pass

    @property
    def SK(self) -> Optional[str]:
        """Sort Key for DynamoDB storage. Optional."""
        return None

    @property
    def GS1PK(self) -> Optional[str]:
        """Global Secondary Index 1 Partition Key for DynamoDB. Optional."""
        return None

    class Config:
        # Updated configuration key for Pydantic v2
        populate_by_name = True

        # Allow extra fields (useful for DynamoDB metadata)
        extra = "allow"
