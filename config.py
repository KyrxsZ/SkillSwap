import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-dev-change-me")
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    STORAGE_MODE = os.getenv("STORAGE_MODE", "local").lower()
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_SKILLS_TABLE = os.getenv("DYNAMODB_SKILLS_TABLE", "skillswap-skills")
    DYNAMODB_REQUESTS_TABLE = os.getenv("DYNAMODB_REQUESTS_TABLE", "skillswap-requests")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"