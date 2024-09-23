from typing import Any, Optional, TypeVar, Type

from botocore.client import BaseClient
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer
from botocore.exceptions import ClientError

from openfactcheck.utils import logging
from openfactcheck.services.model import DynamoDBBaseModel

logger = logging.get_logger(__name__)

T = TypeVar("T", bound=DynamoDBBaseModel)


class DynamoDBInterface:
    """
    Interface to interact with AWS DynamoDB service.

    Provides methods to create, update, and fetch items from a DynamoDB table.

    Parameters
    ----------
    dynamodb_svc : botocore.client.BaseClient
        Boto3 DynamoDB service client.
    table : str
        Name of the DynamoDB table.

    Attributes
    ----------
    logger : logging.Logger
        Logger instance for the class.
    table : str
        Name of the DynamoDB table.
    dynamodb_svc : botocore.client.BaseClient
        Boto3 DynamoDB service client.

    Methods
    -------
    create_or_update(storable: DynamoDBBaseModel) -> None:
        Create or update a DynamoDB item based on the provided storable object.
    fetch(pk: str, model: Type[T]) -> Optional[T]:
        Fetch a DynamoDB item by primary key and deserialize it into the provided model.

    Raises
    ------
    ClientError
        If the DynamoDB service reports an error.
    """

    def __init__(self, dynamodb_svc: BaseClient, table: str) -> None:
        self.logger = logger
        self.table: str = table
        self.dynamodb_svc: BaseClient = dynamodb_svc

    def _serialize_item(self, storable: DynamoDBBaseModel) -> dict[str, Any]:
        """
        Serialize a DynamoDBBaseModel instance to a dictionary format for DynamoDB storage.

        Parameters
        ----------
        storable : DynamoDBBaseModel
            The object to serialize.

        Returns
        -------
        Dict[str, Any]
            The serialized item ready to be stored in DynamoDB.
        """
        serializer = TypeSerializer()
        item_dict = storable.model_dump(exclude_unset=True, by_alias=True)
        av = {k: serializer.serialize(v) for k, v in item_dict.items()}

        # Add the primary key
        av["PK"] = serializer.serialize(storable.PK)

        # Optionally add the sort key, if present
        if storable.SK is not None:
            av["SK"] = serializer.serialize(storable.SK)

        # Optionally add the GS1 partition key, if present
        if storable.GS1PK is not None:
            av["GS1PK"] = serializer.serialize(storable.GS1PK)

        return av

    def _deserialize_item(self, item: dict[str, Any], model: Type[T]) -> T:
        """
        Deserialize a DynamoDB item into an instance of the provided model.

        Parameters
        ----------
        item : dict
            The DynamoDB item to deserialize.
        model : Type[T]
            The model class to instantiate with the deserialized data.

        Returns
        -------
        T
            An instance of the model class populated with data from the item.
        """
        deserializer = TypeDeserializer()
        attributes = {k: deserializer.deserialize(v) for k, v in item.items()}
        return model(**attributes)

    def _paged_scan(self) -> list[dict[str, Any]]:
        """
        Perform a paginated scan of the DynamoDB table and return all items.

        Returns
        -------
        list of dict
            A list of items retrieved from the DynamoDB table.

        Raises
        ------
        ClientError
            If the DynamoDB service reports an error.
        """
        try:
            items = []
            scan_kwargs = {"TableName": self.table}
            while True:
                response = self.dynamodb_svc.scan(**scan_kwargs)
                items.extend(response.get("Items", []))
                self.logger.debug(f"Fetched {len(response.get('Items', []))} items in this page.")
                if "LastEvaluatedKey" in response:
                    scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
                else:
                    break
            self.logger.info(f"Total {len(items)} items fetched from table {self.table}.")
            return items
        except ClientError as e:
            self.logger.error(f"DynamoDBInterface._paged_scan failed: {e}")
            raise

    def create_or_update(self, storable: DynamoDBBaseModel) -> None:
        """
        Create or update a DynamoDB item based on the provided storable object.

        Parameters
        ----------
        storable : DynamoDBBaseModel
            The object to create or update in DynamoDB.

        Raises
        ------
        ClientError
            If the DynamoDB service reports an error.
        """
        try:
            item = self._serialize_item(storable)
            self.dynamodb_svc.put_item(TableName=self.table, Item=item)
            self.logger.info(f"Item with PK={storable.PK} created/updated successfully.")
        except ClientError as e:
            self.logger.error(f"DynamoDBInterface.create_or_update failed: {e}")
            raise

    def fetch(self, pk: str, model: Type[T]) -> Optional[T]:
        """
        Fetch a DynamoDB item by primary key and deserialize it into the provided model.

        Parameters
        ----------
        pk : str
            The primary key of the item to fetch.
        model : Type[T]
            The model class to deserialize the item into.

        Returns
        -------
        Optional[T]
            An instance of the model if found; otherwise, None.

        Raises
        ------
        ClientError
            If the DynamoDB service reports an error.
        """
        try:
            key = {"PK": {"S": pk}}
            response = self.dynamodb_svc.get_item(TableName=self.table, Key=key)
            if "Item" not in response:
                self.logger.info(f"No item found with PK={pk}.")
                return None
            self.logger.info(f"Item with PK={pk} fetched successfully.")
            return self._deserialize_item(response["Item"], model)
        except ClientError as e:
            self.logger.error(f"DynamoDBInterface.fetch failed: {e}")
            raise

    def delete(self, pk: str) -> None:
        """
        Delete a DynamoDB item by primary key.

        Parameters
        ----------
        pk : str
            The primary key of the item to delete.

        Raises
        ------
        ClientError
            If the DynamoDB service reports an error.
        """
        try:
            key = {"PK": {"S": pk}}
            self.dynamodb_svc.delete_item(TableName=self.table, Key=key)
            self.logger.info(f"Item with PK={pk} deleted successfully.")
        except ClientError as e:
            self.logger.error(f"DynamoDBInterface.delete failed: {e}")
            raise

    def list(self, model: Type[T]) -> Optional[list[T]]:
        """
        List all items in the DynamoDB table and deserialize them into the provided model.

        Parameters
        ----------
        model : Type[T]
            The model class to deserialize the items into.

        Returns
        -------
        Optional[List[T]]
            A list of instances of the model class if items are found; otherwise, None.

        Raises
        ------
        ClientError
            If the DynamoDB service reports an error.
        """
        try:
            items = self._paged_scan()
            if not items:
                self.logger.info(f"No items found in table {self.table}.")
                return None
            self.logger.info("Items fetched successfully.")
            return [self._deserialize_item(item, model) for item in items]
        except ClientError as e:
            self.logger.error(f"DynamoDBInterface.list failed: {e}")
            raise
