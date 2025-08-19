import uuid
import json
from datetime import timedelta
from google.cloud import storage
from app.core.config import settings
from google.oauth2 import service_account


class StorageService:
    def __init__(self):
        if settings.APP_ENV == "local":
            self.bucket_credential = (
                service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_BUCKET_CREDENTIALS
                )
            )
        else:
            credential_info = json.loads(settings.GOOGLE_BUCKET_CREDENTIALS)
            self.bucket_credential = (
                service_account.Credentials.from_service_account_info(credential_info)
            )
        self.storage_client = storage.Client(credentials=self.bucket_credential)
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.bucket = self.storage_client.bucket(self.bucket_name)

    async def generate_upload_url(
        self, user_id: int, file_name: str
    ) -> tuple[str, str]:
        """
        Generates a presigned URL for uploading a file to GCS.
        """
        blob_name = f"user_{user_id}/{uuid.uuid4()}/{file_name}"
        blob = self.bucket.blob(blob_name)

        MIN_UPLOAD_SIZE = 1 * 1024  # 1 KB
        MAX_UPLOAD_SIZE = 30 * 1024 * 1024  # 30 MB

        conditions = [["content-length-range", MIN_UPLOAD_SIZE, MAX_UPLOAD_SIZE]]

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="POST",
            conditions=conditions,
        )

        object_url = f"gs://{self.bucket_name}/{blob_name}"
        return url, object_url

    async def download_as_bytes(self, gcs_url: str) -> bytes:
        """
        Downloads a file from GCS and returns its content as bytes.
        """
        if not gcs_url.startswith(f"gs://{self.bucket_name}/"):
            raise ValueError("Invalid GCS URL for this bucket.")

        blob_name = gcs_url.replace(f"gs://{self.bucket_name}/", "")
        blob = self.bucket.blob(blob_name)

        try:
            return blob.download_as_bytes()
        except Exception as e:
            print(f"Error downloading file {gcs_url}: {e}")
            raise FileNotFoundError(
                f"File not found or access denied: {gcs_url}"
            ) from e
