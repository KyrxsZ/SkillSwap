import re
from functools import wraps

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models.user import User


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def validate_registration(self, form):
        name = form.get("name", "").strip()
        student_id = form.get("student_id", "").strip()
        password = form.get("password", "")
        confirm_password = form.get("confirm_password", "")
        errors = []
        if not name:
            errors.append("Name is required.")
        if not re.fullmatch(r"\d{11}", student_id):
            errors.append("Student ID must contain exactly 11 digits.")
        if not password:
            errors.append("Password is required.")
        if password != confirm_password:
            errors.append("Password and Confirm Password must match.")
        if not errors and self.repository.get_by_student_id(student_id):
            errors.append("That Student ID is already registered.")
        return errors

    def register(self, form):
        user = User.new(
            student_id=form["student_id"].strip(),
            name=form["name"].strip(),
            password_hash=generate_password_hash(form["password"]),
        )
        return self.repository.create(user)

    def authenticate(self, student_id, password):
        user = self.repository.get_by_student_id(student_id.strip())
        if not user or not check_password_hash(user["password_hash"], password):
            return None
        return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped