import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from datetime import datetime
import google.generativeai as genai

from app.config import (
    GEMINI_API_KEY, GEMINI_DEFAULT_MODEL,
    MAX_SUMMARY_MESSAGES, MAX_CONVERSATION_CHARS, GEMINI_TIMEOUT_SECONDS,
)
from app.database import (
    chat_sessions_collection,
    chat_messages_collection,
    SettingsDB,
    SettingsSessionLocal,
)
from app.schemas import SessionSummary, SessionDetail, MessageUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


async def _generate_summary_for_session(session_id: str, refresh: bool):
    doc = await chat_sessions_collection.find_one(
        {"session_id": session_id, "is_deleted": {"$ne": True}}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    cached = doc.get("summary")
    if cached and not refresh:
        cached_generated_at = cached.get("generated_at")
        if hasattr(cached_generated_at, "isoformat"):
            cached_generated_at = cached_generated_at.isoformat()
        return {
            "session_id": session_id,
            "title": doc.get("title", ""),
            "summary": cached.get("text", ""),
            "generated_at": cached_generated_at,
            "model_name": cached.get("model_name"),
            "cached": True,
        }

    raw_messages = []
    cursor = chat_messages_collection.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "text": 1, "images": 1, "image_path": 1},
    ).sort("created_at", -1).limit(MAX_SUMMARY_MESSAGES)
    async for msg in cursor:
        raw_messages.append(msg)

    raw_messages.reverse()

    if not raw_messages:
        raise HTTPException(status_code=400, detail="لا توجد رسائل لتلخيصها")

    lines = []
    for msg in raw_messages:
        label = "المستخدم" if msg["role"] == "user" else "المساعد"
        text = msg.get("text", "")
        has_images = bool(msg.get("images")) or bool(msg.get("image_path"))
        if has_images:
            text = f"{text} [تم إرفاق صورة]" if text else "[تم إرفاق صورة]"
        lines.append(f"{label}: {text}")

    conversation = "\n".join(lines)

    if len(conversation) > MAX_CONVERSATION_CHARS:
        conversation = conversation[:MAX_CONVERSATION_CHARS] + "\n... (تم اقتطاع بقية المحادثة)"

    db = SettingsSessionLocal()
    try:
        settings = db.query(SettingsDB).filter(SettingsDB.id == 1).first()
    finally:
        db.close()

    api_key = (settings.api_key if settings and settings.api_key else None) or GEMINI_API_KEY
    model_name = (settings.model if settings else None) or GEMINI_DEFAULT_MODEL
    lang = settings.language if settings else "ar"

    lang_label = "العربية" if lang == "ar" else lang

    prompt = (
        f"لخّص المحادثة التالية في فقرة واحدة واضحة ومركزة.\n\n"
        f"ركز على:\n"
        f"- المشكلة أو السؤال الأساسي\n"
        f"- التحليل أو المناقشة التي تمت\n"
        f"- النتيجة النهائية أو التوصيات\n\n"
        f"اكتب بلغة {lang_label}.\n\n"
        f"المحادثة:\n{conversation}"
    )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=GEMINI_TIMEOUT_SECONDS,
        )
        summary_text = response.text if response.text else "لم يتم توليد ملخص."
    except asyncio.TimeoutError:
        logger.error("Summary generation timed out for session %s", session_id)
        raise HTTPException(status_code=504, detail="انتهت مهلة توليد الملخص. حاول مرة أخرى.")
    except Exception as e:
        logger.error("Summary generation failed for session %s: %s", session_id, str(e))
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء توليد الملخص.")

    now = datetime.utcnow()
    summary_doc = {
        "text": summary_text,
        "model_name": model_name,
        "generated_at": now,
        "message_count": len(raw_messages),
        "chars_sent": len(conversation),
    }

    await chat_sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": {"summary": summary_doc}},
    )

    return {
        "session_id": session_id,
        "title": doc.get("title", ""),
        "summary": summary_text,
        "generated_at": now.isoformat(),
        "model_name": model_name,
        "cached": False,
    }

#Display all the sessions
@router.get("/", response_model=list[SessionSummary])
async def list_sessions():
    sessions = []
    cursor = chat_sessions_collection.find(
        {"is_deleted": {"$ne": True}},
        {"session_id": 1, "title": 1, "updated_at": 1, "_id": 0},
    ).sort("updated_at", -1)
    async for doc in cursor:
        sessions.append(SessionSummary(**doc))
    return sessions

#get a specific session and guarantee images are displayed
@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    doc = await chat_sessions_collection.find_one(
        {"session_id": session_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    messages = []
    cursor = chat_messages_collection.find(
        {"session_id": session_id},
        {"_id": 1, "role": 1, "text": 1, "created_at": 1, "updated_at": 1, "images": 1, "image_path": 1},
    ).sort("created_at", 1)
    async for msg in cursor:
        imgs = msg.get("images", [])
        if not imgs and msg.get("image_path"):
            imgs = [{
                "path": msg["image_path"],
                "filename": msg["image_path"].split("/")[-1],
                "content_type": "image/jpeg",
                "size": 0,
                "uploaded_at": msg.get("created_at", datetime.utcnow()),
            }]
        messages.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "text": msg["text"],
            "updated_at": msg.get("updated_at"),
            "images": imgs,
        })

    return SessionDetail(
        session_id=doc["session_id"],
        title=doc["title"],
        messages=messages,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )

#update a message (not used in the frontend)
@router.put("/messages/{message_id}")
async def update_message(message_id: str, data: MessageUpdate):
    try:
        oid = ObjectId(message_id)
    except Exception:
        raise HTTPException(status_code=400, detail="معرف الرسالة غير صالح")

    now = datetime.utcnow()
    result = await chat_messages_collection.update_one(
        {"_id": oid},
        {"$set": {"text": data.text, "updated_at": now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="الرسالة غير موجودة")

    msg = await chat_messages_collection.find_one({"_id": oid})
    if msg:
        await chat_sessions_collection.update_one(
            {"session_id": msg["session_id"]},
            {"$set": {"updated_at": now}},
        )

    return {"detail": "تم تحديث الرسالة", "updated_at": now.isoformat()}

#summarize a session
@router.get("/{session_id}/summary")
async def summarize_session(
    session_id: str,
    refresh: bool = Query(False, description="Force regenerate summary"),
):
    return await _generate_summary_for_session(session_id, refresh)

#Soft delete a session
@router.delete("/{session_id}")
async def delete_session(session_id: str):
    now = datetime.utcnow()
    result = await chat_sessions_collection.update_one(
        {"session_id": session_id, "is_deleted": {"$ne": True}},
        {"$set": {"is_deleted": True, "deleted_at": now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    return {"detail": "تم حذف الجلسة"}
