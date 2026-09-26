from flask import Flask, flash, redirect, render_template, request, session, url_for

from config import Config
from repositories.request_repository import DynamoDBRequestRepository, LocalRequestRepository
from repositories.skill_repository import DynamoDBSkillRepository, LocalSkillRepository
from repositories.user_repository import DynamoDBUserRepository, LocalUserRepository
from services.auth_service import AuthService, login_required
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
        user_repository = DynamoDBUserRepository(app.config["DYNAMODB_USERS_TABLE"], app.config["AWS_REGION"])
        storage_service = S3StorageService(app.config["S3_BUCKET_NAME"], app.config["AWS_REGION"])
    else:
        skill_repository = LocalSkillRepository(app.config["DATA_DIR"])
        request_repository = LocalRequestRepository(app.config["DATA_DIR"])
        user_repository = LocalUserRepository(app.config["DATA_DIR"])
        storage_service = LocalStorageService(app.config["UPLOAD_FOLDER"])
    app.extensions["auth_service"] = AuthService(user_repository)
    app.extensions["skill_service"] = SkillService(skill_repository, storage_service)
    app.extensions["request_service"] = RequestService(request_repository)

    @app.context_processor
    def inject_counts():
        return {"pending_request_count": app.extensions["request_service"].count_pending(session.get("student_id")), "current_user_name": session.get("user_name")}

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("student_id"):
            return redirect(url_for("index"))
        if request.method == "POST":
            service = app.extensions["auth_service"]
            errors = service.validate_registration(request.form)
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("register.html", form=request.form), 400
            if not service.register(request.form):
                flash("That Student ID is already registered.", "error")
                return render_template("register.html", form=request.form), 400
            flash("Registration complete. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html", form={})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("student_id"):
            return redirect(url_for("index"))
        if request.method == "POST":
            user = app.extensions["auth_service"].authenticate(request.form.get("student_id", ""), request.form.get("password", ""))
            if not user:
                flash("Student ID or password is incorrect.", "error")
                return render_template("login.html", form=request.form), 401
            session.clear()
            session["student_id"] = user["student_id"]
            session["user_name"] = user["name"]
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("index")
            return redirect(next_url)
        return render_template("login.html", form={})

    @app.get("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

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
       
    @app.route("/media/<path:key>")
    def media(key):
        from urllib.parse import urlparse
        import boto3

        if key.startswith("http://") or key.startswith("https://"):
            key = urlparse(key).path.lstrip("/")

        s3 = boto3.client(
            "s3",
            region_name=app.config["AWS_REGION"],
        )

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": app.config["S3_BUCKET_NAME"],
                "Key": key,
            },
            ExpiresIn=3600,
        )

        return redirect(url)

    @app.route("/skills/new", methods=["GET", "POST"])
    @login_required
    def add_skill():
        if request.method == "POST":
            service = app.extensions["skill_service"]
            errors = service.validate_form(request.form, request.files.get("portfolio_image"))
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("add_skill.html", form=request.form), 400
            skill = service.create_skill(request.form, request.files.get("portfolio_image"), {"student_id": session["student_id"], "name": session["user_name"]})
            flash("Your skill is now live on SkillSwap.", "success")
            return redirect(url_for("skill_detail", skill_id=skill["id"]))
        return render_template("add_skill.html", form={})

    @app.route("/skills/<skill_id>/request", methods=["GET", "POST"])
    @login_required
    def request_exchange(skill_id):
        skill = app.extensions["skill_service"].get_skill(skill_id)
        if skill is None:
            return render_template("404.html"), 404
        if not skill.get("owner_student_id"):
            flash("This older skill does not have an owner yet, so it cannot receive requests.", "error")
            return redirect(url_for("skill_detail", skill_id=skill_id))
        if request.method == "POST":
            service = app.extensions["request_service"]
            errors = service.validate_form(request.form)
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("request_form.html", skill=skill, form=request.form), 400
            try:
                service.create_request(request.form, skill, {"student_id": session["student_id"], "name": session["user_name"]})
            except ValueError as error:
                flash(str(error), "error")
                return render_template("request_form.html", skill=skill, form=request.form), 400
            flash("Exchange request sent. You can track it from Requests.", "success")
            return redirect(url_for("requests"))
        return render_template("request_form.html", skill=skill, form={})

    @app.route("/requests")
    @login_required
    def requests():
        service = app.extensions["request_service"]
        student_id = session["student_id"]
        return render_template("requests.html", received_requests=service.get_received_requests(student_id), sent_requests=service.get_sent_requests(student_id))

    @app.post("/requests/<request_id>/<action>")
    @login_required
    def update_request(request_id, action):
        if action not in {"accept", "reject"}:
            return render_template("404.html"), 404
        status = "Accepted" if action == "accept" else "Rejected"
        try:
            updated = app.extensions["request_service"].update_status(request_id, status, session["student_id"])
        except PermissionError:
            return "Forbidden", 403
        if not updated:
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
    app.run(host="0.0.0.0", port=5000, debug=False)
