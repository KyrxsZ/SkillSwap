from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class ExchangeRequest:
    id: str
    requester_name: str
    skill_id: str
    skill_title: str
    message: str
    exchange_skill: str
    status: str = "Pending"
    created_at: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def new(cls, **values):
        values["created_at"] = datetime.now(timezone.utc).isoformat()
        return cls(**values)