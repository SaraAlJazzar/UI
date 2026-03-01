from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.celery_client import celery_client

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    result = AsyncResult(job_id, app=celery_client)

    # Return a normalized response shape consumed by frontend pollers.
    if result.state == "PENDING":
        return {"job_id": job_id, "status": "queued", "result": None, "error": None}
    if result.state in {"STARTED", "RETRY"}:
        return {"job_id": job_id, "status": "running", "result": None, "error": None}
    if result.state == "SUCCESS":
        return {"job_id": job_id, "status": "completed", "result": result.result, "error": None}
    if result.state == "FAILURE":
        return {"job_id": job_id, "status": "failed", "result": None, "error": str(result.result)}

    raise HTTPException(status_code=404, detail="المهمة غير موجودة")

