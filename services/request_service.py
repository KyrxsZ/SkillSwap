import uuid

from models.request import ExchangeRequest


class RequestService:
    def __init__(self, repository):
        self.repository = repository

    def list_requests(self):
        return self.repository.list()

    def count_pending(self):
        return sum(request["status"] == "Pending" for request in self.repository.list())

    def validate_form(self, form):
        required = {"requester_name": "Your name", "message": "Message", "exchange_skill": "Skill you want to exchange"}
        return [f"{label} is required." for field, label in required.items() if not form.get(field, "").strip()]

    def create_request(self, form, skill):
        return self.repository.create(ExchangeRequest.new(id=str(uuid.uuid4()), requester_name=form["requester_name"].strip(), skill_id=skill["id"], skill_title=skill["title"], message=form["message"].strip(), exchange_skill=form["exchange_skill"].strip()))

    def update_status(self, request_id, status):
        return self.repository.update_status(request_id, status)