# Medical AI Assistant

FastAPI-powered medical assistant with RAG search and Gemini AI chat.

## Features

- **RAG Search** — Query medical sources (Altibbi, Mayo Clinic, Mawdoo3) with AI-powered answers
- **Gemini Chat** — Direct conversation with Google Gemini, with image upload and voice transcription
- **Chat History** — MongoDB-backed session management with soft delete and summaries
- **Settings** — Configurable API keys, models, language, and context window (MySQL-backed)

## Project Structure

```
├── main.py                    # FastAPI app entry point
├── app/
│   ├── config.py              # Environment variables & constants
│   ├── database/
│   │   ├── mysql.py           # MySQL engine, ORM model, session
│   │   └── mongodb.py         # MongoDB collections
│   ├── schemas/
│   │   ├── chat.py            # Chat & session schemas
│   │   ├── rag.py             # RAG request/response schemas
│   │   └── settings.py        # Settings schemas
│   ├── services/
│   │   └── scraper.py         # Web scraping & Serper search
│   └── routers/
│       ├── gemini.py          # /gemini/chat, /gemini/transcribe
│       ├── rag.py             # /rag/query
│       ├── settings.py        # /settings/
│       └── chat_sessions.py   # /sessions/ CRUD & summary
├── frontend/
│   ├── index.html             # Home page
│   ├── chat.html              # Chat page
│   ├── rag.html               # RAG search page
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript
├── migrations/                # Alembic migrations (settings DB)
├── uploads/                   # User-uploaded images
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                       # Secrets (not committed)
```

## Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env  # Edit with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

## Docker

```bash
docker compose up --build
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Motor (async MongoDB)
- **AI**: Google Gemini API
- **Search**: Serper API + BeautifulSoup
- **Databases**: MySQL (settings), MongoDB (chat sessions)
- **Frontend**: Vanilla HTML/CSS/JS (RTL Arabic UI)
