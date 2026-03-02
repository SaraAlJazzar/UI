import os
import uuid
import shutil
import logging
import asyncio
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
import google.generativeai as genai

from app.config import (
    GEMINI_API_KEY, GEMINI_DEFAULT_MODEL,
    UPLOAD_DIR, ALLOWED_IMAGE_MIME, ALLOWED_AUDIO_MIME,
    LANGUAGE_INSTRUCTIONS,
)
from app.database import (
    get_settings_db,
    SettingsDB,
    SettingsSessionLocal,
    chat_sessions_collection,
    chat_messages_collection,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _transcribe_audio_bytes(
    audio_bytes: bytes,
    base_mime: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    db = SettingsSessionLocal()
    try:
        settings = db.query(SettingsDB).filter(SettingsDB.id == 1).first()
    finally:
        db.close()

    key = api_key or (settings.api_key if settings and settings.api_key else None) or GEMINI_API_KEY
    model_name = model or (settings.model if settings else None) or GEMINI_DEFAULT_MODEL

    genai.configure(api_key=key)

    mime = base_mime
    if mime == "audio/mp3":
        mime = "audio/mpeg"

    gen_model = genai.GenerativeModel(model_name=model_name)
    response = await asyncio.to_thread(
        gen_model.generate_content,
        [
            "Transcribe this audio exactly as spoken. Return ONLY the transcript text, nothing else. No labels, no quotes, no explanations.",
            {"mime_type": mime, "data": audio_bytes},
        ],
    )
    transcript = response.text.strip() if response.text else ""
    return {"transcript": transcript}

#chat with the model , images included
@router.post("/chat")
async def chat_with_gpt(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_settings_db),
):
    try:
        key = api_key or GEMINI_API_KEY
        model_name = model or GEMINI_DEFAULT_MODEL
        genai.configure(api_key=key)

        settings = db.query(SettingsDB).filter(SettingsDB.id == 1).first()
        context_limit = settings.context_messages if settings else 4

        is_new_session = False
        if session_id:
            doc = await chat_sessions_collection.find_one(
                {"session_id": session_id, "is_deleted": {"$ne": True}}
            )
            if not doc:
                is_new_session = True
        else:
            session_id = str(uuid.uuid4())
            is_new_session = True

        full_history = []
        if not is_new_session:
            cursor = chat_messages_collection.find(
                {"session_id": session_id}, {"_id": 0, "role": 1, "text": 1}
            ).sort("created_at", 1) #sort the messages by the created_at field in ascending order (oldest to newest) , -1 for descending order (newest to oldest)
            async for msg in cursor:
                full_history.append({"role": msg["role"], "text": msg["text"]})

        trimmed_history = []
        if full_history and context_limit > 0:
            max_entries = context_limit * 2
            trimmed_history = full_history[-max_entries:]

        lang = language or "ar"
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(lang, f"Answer in {lang} only.")

        system_prompt = (
            "You are a professional AI assistant.\n"
            f"{lang_instruction}\n"
            "Keep answers clear and well structured.\n"
            "If a limit is required, keep response under 300 words."
        )

        gen_model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )

        history = []
        for msg in trimmed_history:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["text"]]})

        chat = gen_model.start_chat(history=history)

        now = datetime.utcnow()
        saved_images = []
        parts = []

        for img in images:
            if not img.filename:
                continue
            if img.content_type not in ALLOWED_IMAGE_MIME:
                raise HTTPException(
                    status_code=400,
                    detail=f"نوع الملف {img.filename} غير مدعوم. يُسمح بـ JPEG, PNG, GIF, WEBP فقط.",
                )

            ext = os.path.splitext(img.filename)[1] or ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)

            with open(filepath, "wb") as buf:
                shutil.copyfileobj(img.file, buf)

            file_size = os.path.getsize(filepath)
            saved_images.append({
                "path": f"/uploads/{filename}",
                "filename": filename,
                "content_type": img.content_type,
                "size": file_size,
                "uploaded_at": now,
            })

            image_bytes = open(filepath, "rb").read()
            parts.append({"mime_type": img.content_type, "data": image_bytes})

        if message:
            parts.append(message)

        response = chat.send_message(parts)
        answer = response.text if response.text else "لم يتم توليد رد."

        if is_new_session:
            await chat_sessions_collection.insert_one({
                "session_id": session_id,
                "title": message[:60].strip(),
                "created_at": now,
                "updated_at": now,
            })

        user_doc = {
            "session_id": session_id,
            "role": "user",
            "text": message,
            "images": saved_images,
            "created_at": now,
            "updated_at": now,
        }
        bot_doc = {
            "session_id": session_id,
            "role": "bot",
            "text": answer,
            "images": [],
            "created_at": now,
            "updated_at": now,
        }
        await chat_messages_collection.insert_many([user_doc, bot_doc])

        if not is_new_session:
            await chat_sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"updated_at": now}},
            )

        return {
            "message": message,
            "response": answer,
            "session_id": session_id,
            "images": saved_images,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Gemini chat error: %s", e)
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")


#transcribe audio
@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
):
    raw_mime = audio.content_type or ""
    base_mime = raw_mime.split(";")[0].strip()

    if base_mime not in ALLOWED_AUDIO_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"نوع الملف الصوتي غير مدعوم: {raw_mime}",
        )

    try:
        audio_bytes = await audio.read()
        return await _transcribe_audio_bytes(audio_bytes, base_mime, api_key=api_key, model=model)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Transcription error: %s", e)
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")