from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename


class LocalStorageService:
    def __init__(self, upload_folder):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def save(self, file):
        if not file or not file.filename:
            return None
        filename = f"{uuid4().hex}_{secure_filename(file.filename)}"
        file.save(self.upload_folder / filename)
        return f"uploads/{filename}"


class S3StorageService:
    def __init__(self, bucket_name, region):
        import boto3
        self.bucket_name = bucket_name
        self.client = boto3.client("s3", region_name=region)

    def save(self, file):
        filename = f"portfolio/{uuid4().hex}_{secure_filename(file.filename)}"
        self.client.upload_fileobj(file, self.bucket_name, filename, ExtraArgs={"ContentType": file.content_type or "application/octet-stream"})
        return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"