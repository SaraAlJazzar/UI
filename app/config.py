import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------- File Upload ----------
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_AUDIO_MIME = {"audio/webm", "audio/mp3", "audio/mpeg", "audio/mp4", "audio/wav", "audio/ogg", "audio/x-m4a"}

# ---------- MySQL (Settings DB) ----------
MYSQL_USER = os.getenv("MYSQL_USER", "fastapi_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB_SETTINGS = os.getenv("MYSQL_DB_SETTINGS", "settings_db")

_encoded_password = quote_plus(MYSQL_PASSWORD)
SETTINGS_MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{_encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_SETTINGS}"

# ---------- MongoDB ----------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chatbot_db")

# ---------- Google Gemini API ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_DEFAULT_MODEL = os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash-lite")

# ---------- Serper (Google Search) API ----------
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_API_URL = os.getenv("SERPER_API_URL", "https://google.serper.dev/search")

# ---------- Gemini Chat ----------
LANGUAGE_INSTRUCTIONS = {
    "ar": "أجب باللغة العربية فقط.",
    "en": "Answer in English only.",
    "fr": "Répondez en français uniquement.",
    "es": "Responde solo en español.",
    "tr": "Sadece Türkçe cevap ver.",
    "de": "Antworte nur auf Deutsch.",
}

# ---------- Summary ----------
MAX_SUMMARY_MESSAGES = 50
MAX_CONVERSATION_CHARS = 15000
GEMINI_TIMEOUT_SECONDS = 60
