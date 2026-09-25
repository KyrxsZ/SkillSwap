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

    def get(self, request_id):
        return next((item for item in self._read() if item["id"] == request_id), None)

    def get_request_by_id(self, request_id):
        return self.get(request_id)

    def get_received(self, student_id):
        return [item for item in self._read() if item.get("target_student_id") == student_id]

    def get_received_requests(self, student_id):
        return self.get_received(student_id)

    def get_sent(self, student_id):
        return [item for item in self._read() if item.get("requester_student_id") == student_id]

    def get_sent_requests(self, student_id):
        return self.get_sent(student_id)

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

    def update_request_status(self, request_id, status):
        return self.update_status(request_id, status)


class DynamoDBRequestRepository:
    def __init__(self, table_name, region):
        import boto3
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def list(self):
        return self.table.scan().get("Items", [])

    def get(self, request_id):
        return self.table.get_item(Key={"id": request_id}).get("Item")

    def get_request_by_id(self, request_id):
        return self.get(request_id)

    def get_received(self, student_id):
        return [item for item in self.list() if item.get("target_student_id") == student_id]

    def get_received_requests(self, student_id):
        return self.get_received(student_id)

    def get_sent(self, student_id):
        return [item for item in self.list() if item.get("requester_student_id") == student_id]

    def get_sent_requests(self, student_id):
        return self.get_sent(student_id)

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

    def update_request_status(self, request_id, status):
        return self.update_status(request_id, status)