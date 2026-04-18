from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, agent, auth
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


def create_admin_user():
    db = SessionLocal()
    try:
        admin_obj = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()

        if not admin_obj:
            print("🚀 Creating initial admin user...")
            new_admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(new_admin)
            db.commit()
            print(f"✅ Admin '{settings.ADMIN_USERNAME}' created successfully.")
        else:
            print(f"ℹ️ Admin user '{settings.ADMIN_USERNAME}' already exists.")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    create_admin_user()

    print("✅ Database tables ready")
    yield
    print("👋 Shutting down AutoAgent API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🤖 AutoAgent API
An autonomous AI agent API powered by **Gemini** using the **ReAct** pattern.
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

# Inclusion des routes
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
