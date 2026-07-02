from celery import Celery
from app.settings.config import settings

celery_app = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)


@celery_app.task
def send_welcome_email(user_email: str, temp_password: str):
    pass


@celery_app.task
def send_password_reset_email(user_email: str, reset_link: str):
    pass
