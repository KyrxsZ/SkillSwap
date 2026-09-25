from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class User:
    student_id: str
    name: str
    password_hash: str
    created_at: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def new(cls, **values):
        values["created_at"] = datetime.now(timezone.utc).isoformat()
        return cls(**values)