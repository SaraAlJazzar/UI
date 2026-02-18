from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_settings_db, SettingsDB
from app.schemas import SettingsUpdate, SettingsResponse

router = APIRouter()


def get_or_create_settings(db: Session) -> SettingsDB:
    settings = db.query(SettingsDB).filter(SettingsDB.id == 1).first()
    if not settings:
        settings = SettingsDB(
            id=1,
            api_key="",
            model="gemini-2.5-flash-lite",
            language="ar",
            context_messages=4,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_settings_db)):
    settings = get_or_create_settings(db)
    return settings


@router.put("/", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_settings_db)):
    settings = get_or_create_settings(db)

    if data.api_key is not None:
        settings.api_key = data.api_key
    if data.model is not None:
        settings.model = data.model
    if data.language is not None:
        settings.language = data.language
    if data.context_messages is not None:
        settings.context_messages = data.context_messages

    db.commit()
    db.refresh(settings)
    return settings
