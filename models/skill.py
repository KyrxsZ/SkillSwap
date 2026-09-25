from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Skill:
    id: str
    student_name: str
    title: str
    category: str
    description: str
    teach: str
    learn: str
    image_url: Optional[str] = None
    created_at: str = ""
    owner_student_id: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def new(cls, **values):
        values["created_at"] = datetime.now(timezone.utc).isoformat()
        return cls(**values)