import uuid
from datetime import timedelta
from google.cloud import storage
from fastapi import Depends

from app.core.config import settings


class StorageService:
    def __init__(self, bucket_name: str):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
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

        # Generate the presigned URL, valid for 15 minutes
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type="application/octet-stream",  # Or be more specific if possible
        )

        # The final URL of the object after upload
        object_url = f"gs://{self.bucket_name}/{blob_name}"

        return url, object_url
