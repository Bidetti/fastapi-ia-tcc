import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3

from src.app.config import settings

logger = logging.getLogger(__name__)


class DynamoClient:
    def __init__(self, table_name: Optional[str] = None, region: Optional[str] = None):
        self.table_name = table_name or settings.DYNAMODB_TABLE_NAME
        self.region = region or settings.AWS_REGION
        self.client = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.client.Table(self.table_name)
        logger.info(f"Inicializando cliente DynamoDB para tabela {self.table_name}")

    def convert_to_dynamo_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        dynamo_item = {}
        for key, value in item.items():
            if isinstance(value, datetime):
                dynamo_item[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                dynamo_item[key] = json.dumps(value)
            else:
                dynamo_item[key] = value
        return dynamo_item

    def convert_from_dynamo_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if not item:
            return {}

        result = {}
        for key, value in item.items():
            if key.endswith("_timestamp") and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value)
                except ValueError:
                    result[key] = value
            elif key in ["results", "metadata", "summary"] and isinstance(value, str):
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            else:
                result[key] = value
        return result

    async def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        dynamo_item = self.convert_to_dynamo_item(item)

        try:
            self.table.put_item(Item=dynamo_item)
            logger.info(f"Item inserido com sucesso: {item.get('image_id') or item.get('request_id')}")
            return dynamo_item
        except Exception as e:
            logger.error(f"Erro ao inserir item no DynamoDB: {e}")
            raise

    async def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(Key=key)
            item = response.get("Item")

            if not item:
                logger.warning(f"Item não encontrado para chave: {key}")
                return None

            return self.convert_from_dynamo_item(item)
        except Exception as e:
            logger.error(f"Erro ao recuperar item do DynamoDB: {e}")
            raise

    async def query_items(
        self, key_name: str, key_value: Any, index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            query_kwargs = {
                "KeyConditionExpression": f"{key_name} = :value",
                "ExpressionAttributeValues": {":value": key_value},
            }

            if index_name:
                query_kwargs["IndexName"] = index_name

            response = self.table.query(**query_kwargs)
            items = response.get("Items", [])

            return [self.convert_from_dynamo_item(item) for item in items]
        except Exception as e:
            logger.error(f"Erro ao consultar itens no DynamoDB: {e}")
            raise
