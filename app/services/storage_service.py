import uuid
from datetime import timedelta
from google.cloud import storage
from app.core.config import settings
from google.oauth2 import service_account


class StorageService:
    def __init__(self):
        self.bucket_credential = service_account.Credentials.from_service_account_file(settings.GOOGLE_BUCKET_CREDENTIALS)
        self.storage_client = storage.Client(credentials=self.bucket_credential)
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def generate_upload_url(self, user_id: int, file_name: str) -> tuple[str, str]:
        """
        Generates a presigned URL for uploading a file to GCS.

        Args:
            user_id: The ID of the user uploading the file.
            file_name: The original name of the file.

        Returns:
            A tuple containing the presigned URL and the destination blob name.
        """
        # Create a unique blob name to avoid collisions
        blob_name = f"user_{user_id}/{uuid.uuid4()}/{file_name}"

        blob = self.bucket.blob(blob_name)
        
        MIN_UPLOAD_SIZE = 1 * 1024  # 1 KB
        MAX_UPLOAD_SIZE = 30 * 1024 * 1024  # 10 MB
        
        conditions = [
            ["content-length-range", MIN_UPLOAD_SIZE, MAX_UPLOAD_SIZE]
        ]

        # Generate the presigned URL, valid for 15 minutes
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="POST",
            content_type="application/octet-stream",
            conditions=conditions
        )

        # The final URL of the object after upload
        object_url = f"gs://{self.bucket_name}/{blob_name}"

        return url, object_url
