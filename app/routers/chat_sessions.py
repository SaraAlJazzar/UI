from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from app.database import chat_sessions_collection, chat_messages_collection
from app.schemas import SessionSummary, SessionDetail, ChatMessage, MessageUpdate

router = APIRouter()


@router.get("/", response_model=list[SessionSummary])
async def list_sessions():
    sessions = []
    cursor = chat_sessions_collection.find(
        {}, {"session_id": 1, "title": 1, "updated_at": 1, "_id": 0}
    ).sort("updated_at", -1)
    async for doc in cursor:
        sessions.append(SessionSummary(**doc))
    return sessions


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    doc = await chat_sessions_collection.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")

    messages = []
    cursor = chat_messages_collection.find(
        {"session_id": session_id},
        {"_id": 1, "role": 1, "text": 1, "updated_at": 1}
    ).sort("created_at", 1)
    async for msg in cursor:
        messages.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "text": msg["text"],
            "updated_at": msg.get("updated_at"),
        })

    return SessionDetail(
        session_id=doc["session_id"],
        title=doc["title"],
        messages=messages,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


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


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    result = await chat_sessions_collection.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الجلسة غير موجودة")
    await chat_messages_collection.delete_many({"session_id": session_id})
    return {"detail": "تم حذف الجلسة"}
