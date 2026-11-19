from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models  # Ensures SQLAlchemy knows all models before creating tables
from app.api.routes.auth import router as auth_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.github import router as github_router
from app.api.routes.google_drive import router as google_drive_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.orchestrator import router as orchestrator_router
from app.api.routes.mcp import router as mcp_router
from app.config.settings import settings
from app.database.connection import create_tables
from app.database.session import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables automatically when the server starts
    create_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Allow the React frontend to send requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth_router)
app.include_router(google_drive_router)
app.include_router(github_router)
app.include_router(discovery_router)
app.include_router(knowledge_router)
app.include_router(jobs_router)
app.include_router(orchestrator_router)
app.include_router(mcp_router)


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
