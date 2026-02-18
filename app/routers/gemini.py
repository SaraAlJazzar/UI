from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import google.generativeai as genai
import uuid
from datetime import datetime
from app.schemas import ChatRequest, ChatResponse
from app.config import GEMINI_API_KEY, GEMINI_DEFAULT_MODEL
from app.database import get_settings_db, SettingsDB, chat_sessions_collection, chat_messages_collection

router = APIRouter()

LANGUAGE_INSTRUCTIONS = {
    "ar": "أجب باللغة العربية فقط.",
    "en": "Answer in English only.",
    "fr": "Répondez en français uniquement.",
    "es": "Responde solo en español.",
    "tr": "Sadece Türkçe cevap ver.",
    "de": "Antworte nur auf Deutsch.",
}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_gpt(request: ChatRequest, db: Session = Depends(get_settings_db)):
#Depends(get_settings_db) opens a MySQL session to settings_db and injects it as db

    try:
        api_key = request.api_key or GEMINI_API_KEY
        model_name = request.model or GEMINI_DEFAULT_MODEL

        genai.configure(api_key=api_key)
        #If the user sent a custom key from settings, use it. Otherwise fall back to the default from .env. Then configure the Google SDK with that key.
        
        # Read context_messages limit from settings DB
        settings = db.query(SettingsDB).filter(SettingsDB.id == 1).first()
        context_limit = settings.context_messages if settings else 4

        # Resolve session
        session_id = request.session_id
        is_new_session = False

        if session_id:
            doc = await chat_sessions_collection.find_one({"session_id": session_id})
            if not doc:
                is_new_session = True
        else:
            session_id = str(uuid.uuid4())
            is_new_session = True

        # Load history from chat_messages collection
        full_history = []
        if not is_new_session:
            cursor = chat_messages_collection.find(
                {"session_id": session_id}, {"_id": 0, "role": 1, "text": 1}
            ).sort("created_at", 1) #Sort the messages by created_at in ascending order
            async for msg in cursor:
                full_history.append({"role": msg["role"], "text": msg["text"]})

        # Trim history for Gemini context window
        trimmed_history = []
        if full_history and context_limit > 0:
            max_entries = context_limit * 2
            trimmed_history = full_history[-max_entries:]

        lang = request.language or "ar"
        lang_instruction = LANGUAGE_INSTRUCTIONS.get(lang, f"Answer in {lang} only.")

        system_prompt = f"""
        You are a professional AI assistant.
        {lang_instruction}
        Keep answers clear and well structured.
        If a limit is required, keep response under 300 words.
        """

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt
        )

        history = []
        if trimmed_history:
            for msg in trimmed_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["text"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(request.message)
        answer = response.text if response.text else "لم يتم توليد رد."

        # Save to MongoDB
        now = datetime.utcnow()

        if is_new_session:
            await chat_sessions_collection.insert_one({
                "session_id": session_id,
                "title": request.message[:60].strip(),
                "created_at": now,
                "updated_at": now,
            })

        # Insert each message as its own document
        await chat_messages_collection.insert_many([
            {"session_id": session_id, "role": "user", "text": request.message, "created_at": now, "updated_at": now},
            {"session_id": session_id, "role": "bot", "text": answer, "created_at": now, "updated_at": now},
        ])

        # Update session timestamp
        if not is_new_session:
            await chat_sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"updated_at": now}},
            )

        return ChatResponse(
            message=request.message,
            response=answer,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API Error: {str(e)}"
        )
