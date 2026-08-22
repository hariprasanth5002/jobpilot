"""
JobPilot FastAPI Application
-----------------------------
Entry point for the JobPilot API server.

Endpoints:
    POST /api/documents/resume          – Upload resume PDF
    POST /api/documents/job-description – Upload job description PDF
    POST /api/profile                   – Submit structured user details
    POST /api/chat                      – Ask a job-related question (full RAG pipeline)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.documents import router as documents_router
from api.routes.chat import router as chat_router
from api.routes.profile import router as profile_router

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="JobPilot API",
    description=(
        "RAG-powered job application assistant. "
        "Upload resume and job description, then ask questions about your fit, "
        "skill gaps, interview prep, and project guidance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# Allow the React dev server (Vite default: 5173, CRA default: 3000).
# Only local origins are whitelisted — not a wildcard open policy.
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(profile_router)
