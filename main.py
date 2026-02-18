from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import gemini, rag, settings, chat_sessions


app = FastAPI(title="Medical RAG & Chat")

app.include_router(gemini.router, prefix="/gemini", tags=["Gemini"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])
app.include_router(chat_sessions.router, prefix="/sessions", tags=["Chat Sessions"])

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/rag-page")
def rag_page():
    return FileResponse("frontend/rag.html")

@app.get("/chat-page")
def chat_page():
    return FileResponse("frontend/chat.html")