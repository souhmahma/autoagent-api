from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, agent, admin

# Import models so SQLAlchemy registers them before create_all
from app.models import user, session  

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    yield
    print("👋 Shutting down AutoAgent API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🤖 AutoAgent API

An autonomous AI agent API powered by **Gemini** using the **ReAct** (Reasoning + Acting) pattern.

### Features
- 🔐 JWT Authentication with role-based access (user / admin)
- 🧠 ReAct agent loop: Think → Act → Observe → Repeat
- 🛠️ 4 built-in tools: Web Search, Calculator, Weather, Summarizer
- 💾 Full session history persisted in SQLite
- 👮 Admin panel to manage users and view all sessions

### Quick Start
1. `POST /auth/register` — Create your account
2. `POST /auth/login` — Get your JWT tokens
3. `POST /agent/run` — Send a task to the agent
4. `GET /agent/sessions` — View your session history
    """,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
