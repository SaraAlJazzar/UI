from celery import Celery

from app.config import REDIS_URL


celery_client = Celery(
    "fastapi_client",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

