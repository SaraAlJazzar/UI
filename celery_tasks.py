import asyncio
import base64

from celery import Celery

from app.config import REDIS_URL
from app.routers.chat_sessions import _generate_summary_for_session
from app.routers.gemini import _transcribe_audio_bytes
from app.routers.rag import _run_rag_query
from app.schemas import RAGRequest


celery_app = Celery(
    "fastapi_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="tasks.ping")
def ping():
    return {"status": "ok", "message": "pong"}


@celery_app.task(name="tasks.generate_summary")
def generate_summary_task(session_id: str, refresh: bool = False):
    return asyncio.run(_generate_summary_for_session(session_id, refresh))


@celery_app.task(name="tasks.rag_query")
def rag_query_task(payload: dict):
    request = RAGRequest(**payload)
    result = asyncio.run(_run_rag_query(request))
    return {
        "query": result.query,
        "source": result.source,
        "response": result.response,
        "used_links": [
            {"url": link.url, "title": link.title, "snippet": link.snippet}
            for link in result.used_links
        ],
    }


@celery_app.task(name="tasks.transcribe_audio")
def transcribe_audio_task(audio_base64: str, base_mime: str, api_key: str | None = None, model: str | None = None):
    audio_bytes = base64.b64decode(audio_base64)
    return asyncio.run(
        _transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            base_mime=base_mime,
            api_key=api_key,
            model=model,
        )
    )

