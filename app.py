from flask import Flask, flash, redirect, render_template, request, url_for

from config import Config
from repositories.request_repository import DynamoDBRequestRepository, LocalRequestRepository
from repositories.skill_repository import DynamoDBSkillRepository, LocalSkillRepository
from services.request_service import RequestService
from services.skill_service import SkillService
from services.storage_service import LocalStorageService, S3StorageService


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    use_aws = app.config["STORAGE_MODE"] == "aws" and app.config["S3_BUCKET_NAME"]
    if use_aws:
        skill_repository = DynamoDBSkillRepository(app.config["DYNAMODB_SKILLS_TABLE"], app.config["AWS_REGION"])
        request_repository = DynamoDBRequestRepository(app.config["DYNAMODB_REQUESTS_TABLE"], app.config["AWS_REGION"])
        storage_service = S3StorageService(app.config["S3_BUCKET_NAME"], app.config["AWS_REGION"])
    else:
        skill_repository = LocalSkillRepository(app.config["DATA_DIR"])
        request_repository = LocalRequestRepository(app.config["DATA_DIR"])
        storage_service = LocalStorageService(app.config["UPLOAD_FOLDER"])
    app.extensions["skill_service"] = SkillService(skill_repository, storage_service)
    app.extensions["request_service"] = RequestService(request_repository)

    @app.context_processor
    def inject_counts():
        return {"pending_request_count": app.extensions["request_service"].count_pending()}

    @app.route("/")
    def index():
        skills = app.extensions["skill_service"].list_skills()[:3]
        return render_template("index.html", featured_skills=skills)

    @app.route("/skills")
    def skills():
        query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        service = app.extensions["skill_service"]
        return render_template(
            "skills.html",
            skills=service.list_skills(query=query, category=category),
            categories=service.categories(),
            query=query,
            selected_category=category,
        )

    @app.route("/skills/<skill_id>")
    def skill_detail(skill_id):
        skill = app.extensions["skill_service"].get_skill(skill_id)
        if skill is None:
            return render_template("404.html"), 404
        return render_template("skill_detail.html", skill=skill)

    @app.route("/skills/new", methods=["GET", "POST"])
    def add_skill():
        if request.method == "POST":
            service = app.extensions["skill_service"]
            errors = service.validate_form(request.form, request.files.get("portfolio_image"))
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("add_skill.html", form=request.form), 400
            skill = service.create_skill(request.form, request.files.get("portfolio_image"))
            flash("Your skill is now live on SkillSwap.", "success")
            return redirect(url_for("skill_detail", skill_id=skill["id"]))
        return render_template("add_skill.html", form={})

    @app.route("/skills/<skill_id>/request", methods=["GET", "POST"])
    def request_exchange(skill_id):
        skill = app.extensions["skill_service"].get_skill(skill_id)
        if skill is None:
            return render_template("404.html"), 404
        if request.method == "POST":
            service = app.extensions["request_service"]
            errors = service.validate_form(request.form)
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("request_form.html", skill=skill, form=request.form), 400
            service.create_request(request.form, skill)
            flash("Exchange request sent. You can track it from Requests.", "success")
            return redirect(url_for("requests"))
        return render_template("request_form.html", skill=skill, form={})

    @app.route("/requests")
    def requests():
        return render_template("requests.html", requests=app.extensions["request_service"].list_requests())

    @app.post("/requests/<request_id>/<action>")
    def update_request(request_id, action):
        if action not in {"accept", "reject"}:
            return render_template("404.html"), 404
        status = "Accepted" if action == "accept" else "Rejected"
        if not app.extensions["request_service"].update_status(request_id, status):
            return render_template("404.html"), 404
        flash(f"Request {status.lower()}.", "success")
        return redirect(url_for("requests"))

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("500.html"), 500

    @app.errorhandler(413)
    def file_too_large(_error):
        flash("That image is too large. Please choose a file under 5MB.", "error")
        return redirect(url_for("add_skill"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])