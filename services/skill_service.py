import uuid

from models.skill import Skill


class SkillService:
    def __init__(self, repository, storage):
        self.repository = repository
        self.storage = storage

    def list_skills(self, query="", category=""):
        skills = self.repository.list()
        query = query.lower()
        return [skill for skill in skills if (not query or query in " ".join([skill["title"], skill["description"], skill["student_name"]]).lower()) and (not category or skill["category"] == category)]

    def get_skill(self, skill_id):
        return self.repository.get(skill_id)

    def categories(self):
        return sorted({skill["category"] for skill in self.repository.list()})

    def validate_form(self, form, image):
        required = {"title": "Skill title", "category": "Category", "description": "Description", "teach": "What you can teach", "learn": "What you want to learn"}
        errors = [f"{label} is required." for field, label in required.items() if not form.get(field, "").strip()]
        if image and image.filename:
            extension = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else ""
            if extension not in {"png", "jpg", "jpeg", "gif", "webp"}:
                errors.append("Portfolio image must be PNG, JPG, GIF, or WEBP.")
        return errors

    def create_skill(self, form, image, user):
        image_url = self.storage.save(image) if image and image.filename else None
        return self.repository.create(Skill.new(id=str(uuid.uuid4()), owner_student_id=user["student_id"], student_name=user["name"], title=form["title"].strip(), category=form["category"].strip(), description=form["description"].strip(), teach=form["teach"].strip(), learn=form["learn"].strip(), image_url=image_url))