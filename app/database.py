import motor.motor_asyncio
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import SETTINGS_MYSQL_URL, MONGO_URL, MONGO_DB_NAME


# MongoDB — Chat
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client[MONGO_DB_NAME]
chat_sessions_collection = mongo_db["chat_sessions"]
chat_messages_collection = mongo_db["chat_messages"]


# MySQL — Settings database
settings_engine = create_engine(SETTINGS_MYSQL_URL)
SettingsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=settings_engine)
SettingsBase = declarative_base()


# MySQL Model — settings_db
class SettingsDB(SettingsBase):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    api_key = Column(String(255), nullable=True, default="")
    model = Column(String(100), nullable=False, default="gemini-2.5-flash-lite")
    language = Column(String(10), nullable=False, default="ar")
    context_messages = Column(Integer, nullable=False, default=4)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


# Dependency
def get_settings_db():
    """MySQL session dependency — settings_db"""
    db = SettingsSessionLocal()
    try:
        yield db
    finally:
        db.close()
