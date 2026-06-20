"""
FastAPI Application - AI Candidate Ranking System

Production-ready backend with search, ranking, and explanation endpoints.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.settings import get_settings
from .models.schemas import HealthResponse, ErrorResponse
from .services.search_service import get_candidate_count

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: load candidates on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Candidates path: %s", settings.PROCESSED_CANDIDATES_PATH)

    # Pre-load candidates
    from .services.search_service import ensure_loaded
    count = ensure_loaded()
    logger.info("Loaded %d candidates into memory", count)

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered candidate ranking system with semantic search, "
                "multi-factor scoring, and explainable AI recommendations.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": "VALIDATION_ERROR"},
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
from .routers import search, rank, explain, candidate  # noqa: E402

app.include_router(search.router)
app.include_router(rank.router)
app.include_router(explain.router)
app.include_router(candidate.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        candidates_loaded=get_candidate_count(),
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "search": "POST /search",
            "rank": "POST /rank",
            "explain": "POST /explain",
            "explain_compare": "POST /explain/compare",
            "candidate": "GET /candidate/{id}",
            "health": "GET /health",
        },
    }
