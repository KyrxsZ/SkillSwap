import json
import uuid
from pathlib import Path

from models.skill import Skill


SEED_SKILLS = [
    {"student_name": "Maya Chen", "title": "Python", "category": "Technology", "description": "Build practical scripts and understand the fundamentals of Python through friendly, project-based sessions.", "teach": "Python basics, automation, and data handling", "learn": "UI design and accessibility"},
    {"student_name": "Jordan Williams", "title": "Graphic Design", "category": "Design", "description": "Learn how to turn a blank canvas into a clear visual story with layout, color, and typography.", "teach": "Branding, Figma, and visual composition", "learn": "Front-end development"},
    {"student_name": "Aisha Patel", "title": "Video Editing", "category": "Creative", "description": "Make polished short-form videos with a simple editing workflow that keeps your story moving.", "teach": "Premiere Pro, pacing, and captions", "learn": "Photography lighting"},
    {"student_name": "Leo Martin", "title": "English Conversation", "category": "Languages", "description": "Practice natural conversation and gain confidence for classes, interviews, and everyday life.", "teach": "Conversation practice and pronunciation", "learn": "Spanish"},
    {"student_name": "Sam Rivera", "title": "Photography", "category": "Creative", "description": "Explore composition and camera basics while finding your own visual point of view.", "teach": "Portraits, composition, and Lightroom", "learn": "Guitar songwriting"},
    {"student_name": "Noah Kim", "title": "Web Development", "category": "Technology", "description": "Go from idea to a responsive website using HTML, CSS, and JavaScript fundamentals.", "teach": "HTML, CSS, JavaScript, and Flask", "learn": "Illustration"},
]


class LocalSkillRepository:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "skills.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([Skill.new(id=str(uuid.uuid4()), **skill).to_dict() for skill in SEED_SKILLS])

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, items):
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def list(self):
        return self._read()

    def get(self, skill_id):
        return next((item for item in self._read() if item["id"] == skill_id), None)

    def create(self, skill):
        items = self._read()
        items.insert(0, skill.to_dict())
        self._write(items)
        return skill.to_dict()


class DynamoDBSkillRepository:
    def __init__(self, table_name, region):
        import boto3
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def list(self):
        return self.table.scan().get("Items", [])

    def get(self, skill_id):
        return self.table.get_item(Key={"id": skill_id}).get("Item")

    def create(self, skill):
        item = skill.to_dict()
        self.table.put_item(Item=item)
        return item