import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import json
import base64

class FCMService:
    def __init__(self):
        if not firebase_admin._apps:
            if settings.APP_ENV == "local":
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
            else:
                decoded_creds = base64.b64decode(settings.FIREBASE_CREDENTIALS).decode(
                    "utf-8"
                )
                cred_json = json.loads(decoded_creds)
                cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred)

    def send_notification(self, token: str, title: str, body: str) -> None:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=token,
            )
            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
        except Exception as e:
            print(f"Error sending FCM message: {e}")
            # TODO: Add proper logging

fcm_service = FCMService()
