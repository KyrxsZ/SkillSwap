import json
import uuid
from pathlib import Path

from models.request import ExchangeRequest


class LocalRequestRepository:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "requests.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, items):
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def list(self):
        return self._read()

    def create(self, exchange_request):
        items = self._read()
        items.insert(0, exchange_request.to_dict())
        self._write(items)
        return exchange_request.to_dict()

    def update_status(self, request_id, status):
        items = self._read()
        for item in items:
            if item["id"] == request_id:
                item["status"] = status
                self._write(items)
                return item
        return None


class DynamoDBRequestRepository:
    def __init__(self, table_name, region):
        import boto3
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def list(self):
        return self.table.scan().get("Items", [])

    def create(self, exchange_request):
        item = exchange_request.to_dict()
        self.table.put_item(Item=item)
        return item

    def update_status(self, request_id, status):
        response = self.table.update_item(
            Key={"id": request_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status},
            ReturnValues="ALL_NEW",
        )
        return response.get("Attributes")