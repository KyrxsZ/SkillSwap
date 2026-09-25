import uuid

from models.request import ExchangeRequest


class RequestService:
    def __init__(self, repository):
        self.repository = repository

    def get_received_requests(self, student_id):
        return self.repository.get_received(student_id)

    def get_sent_requests(self, student_id):
        return self.repository.get_sent(student_id)

    def count_pending(self, student_id=None):
        if not student_id:
            return 0
        return sum(item.get("status") == "Pending" for item in self.get_received_requests(student_id))

    def validate_form(self, form):
        required = {"message": "Message", "exchange_skill": "Skill you want to exchange"}
        return [f"{label} is required." for field, label in required.items() if not form.get(field, "").strip()]

    def create_request(self, form, skill, user):
        if not skill.get("owner_student_id"):
            raise ValueError("This legacy skill has no owner and cannot receive requests.")
        if skill["owner_student_id"] == user["student_id"]:
            raise ValueError("You cannot send an exchange request to yourself.")
        return self.repository.create(ExchangeRequest.new(id=str(uuid.uuid4()), requester_student_id=user["student_id"], requester_name=user["name"], target_student_id=skill["owner_student_id"], target_student_name=skill["student_name"], skill_id=skill["id"], skill_title=skill["title"], message=form["message"].strip(), exchange_skill=form["exchange_skill"].strip()))

    def update_status(self, request_id, status, student_id):
        item = self.repository.get(request_id)
        if not item:
            return None
        if item.get("target_student_id") != student_id:
            raise PermissionError("You are not authorized to update this request.")
        return self.repository.update_status(request_id, status)