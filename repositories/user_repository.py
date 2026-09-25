import json
from pathlib import Path

from models.user import User


class LocalUserRepository:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "users.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, items):
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def get_by_student_id(self, student_id):
        return next((item for item in self._read() if item["student_id"] == student_id), None)

    def get_user_by_student_id(self, student_id):
        return self.get_by_student_id(student_id)

    def create(self, user):
        items = self._read()
        if any(item["student_id"] == user.student_id for item in items):
            return None
        item = user.to_dict()
        items.append(item)
        self._write(items)
        return item

    def create_user(self, user):
        return self.create(user)


class DynamoDBUserRepository:
    def __init__(self, table_name, region):
        import boto3
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def get_by_student_id(self, student_id):
        return self.table.get_item(Key={"student_id": student_id}).get("Item")

    def get_user_by_student_id(self, student_id):
        return self.get_by_student_id(student_id)

    def create(self, user):
        from botocore.exceptions import ClientError

        try:
            response = self.table.put_item(
                Item=user.to_dict(),
                ConditionExpression="attribute_not_exists(student_id)",
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return None
            raise
        return user.to_dict() if response else None

    def create_user(self, user):
        return self.create(user)