from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError


class DynamoDbService:
    def __init__(
        self,
        table_name: str,
    ):

        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)

    def create_record(self, item: dict) -> Dict[str, Any]:

        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"Eroare la crearea record-ului: {e.response['Error']['Message']}")
            raise e

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(Key={"id": record_id})
            return response.get("Item", None)
        except ClientError as e:
            print(f"Eroare la citirea record-ului: {e.response['Error']['Message']}")
            raise e

    def get_all_by_record_type(
        self, record_type: str, index_name: str = "recordType-index"
    ) -> List[Dict[str, Any]]:

        records = []
        last_evaluated_key = None

        try:
            while True:
                query_kwargs = {
                    "IndexName": index_name,
                    "KeyConditionExpression": boto3.dynamodb.conditions.Key(
                        "recordType"
                    ).eq(record_type),
                }

                if last_evaluated_key:
                    query_kwargs["ExclusiveStartKey"] = last_evaluated_key

                response = self.table.query(**query_kwargs)

                records.extend(response.get("Items", []))

                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            return records

        except ClientError as e:
            print(
                f"Eroare la interogarea GSI-ului ({index_name}): {e.response['Error']['Message']}"
            )
            raise e

    def delete_record(self, record_id: str) -> bool:

        try:
            self.table.delete_item(Key={"id": record_id})
            return True
        except ClientError as e:
            print(f"Eroare la ștergere: {e.response['Error']['Message']}")
            raise e
