import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


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