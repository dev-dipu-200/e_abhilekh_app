from celery import Celery
from app.settings.config import settings

celery_app = Celery(__name__, broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)


@celery_app.task
def sync_organization_data(org_id: str):
    pass
