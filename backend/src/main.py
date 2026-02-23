"""VyapaarSetu — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.logging import log, setup_logging
from src.db.base import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    setup_logging()
    log.info("Starting VyapaarSetu...")

    engine = get_engine()
    log.info(f"Database engine initialized: {engine.url}")

    try:
        from src.skills.loader import SkillLoader
        skills = SkillLoader.load_all_skills()
        log.info(f"Loaded {len(skills)} skills: {list(skills.keys())}")
    except Exception as e:
        log.warning(f"Skill loading failed: {e}")

    try:
        from src.rag.qdrant_search import QdrantSearch, TAXONOMY_COLLECTION, SNP_COLLECTION, KNOWLEDGE_COLLECTION
        QdrantSearch.ensure_collection(TAXONOMY_COLLECTION)
        QdrantSearch.ensure_collection(SNP_COLLECTION)
        QdrantSearch.ensure_collection(KNOWLEDGE_COLLECTION)
        log.info("Qdrant collections initialized")
    except Exception as e:
        log.warning(f"Qdrant initialization failed (non-fatal): {e}")

    log.info("VyapaarSetu startup complete.")
    yield

    log.info("VyapaarSetu shutting down...")
    await engine.dispose()


app = FastAPI(
    title="VyapaarSetu API",
    description="AI-powered MSE Agent Mapping Tool for ONDC TEAM Initiative",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes.auth import router as auth_router
from src.api.routes.mse import router as mse_router
from src.api.routes.products import router as products_router
from src.api.routes.catalogue import router as catalogue_router
from src.api.routes.match import router as match_router
from src.api.routes.snp import router as snp_router
from src.api.routes.admin import router as admin_router
from src.api.routes.chat import router as chat_router
from src.api.routes.channel.whatsapp import router as whatsapp_router

PREFIX = settings.get("API_PREFIX", "/api/v1")

app.include_router(auth_router, prefix=PREFIX)
app.include_router(mse_router, prefix=PREFIX)
app.include_router(products_router, prefix=PREFIX)
app.include_router(catalogue_router, prefix=PREFIX)
app.include_router(match_router, prefix=PREFIX)
app.include_router(snp_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)
app.include_router(chat_router, prefix=PREFIX)
app.include_router(whatsapp_router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "VyapaarSetu"}


@app.get("/")
async def root():
    return {
        "service": "VyapaarSetu",
        "version": "0.1.0",
        "description": "AI-powered MSE onboarding for ONDC TEAM Initiative",
    }
