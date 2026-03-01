"""WhatsApp routes — connection, webhook, auth sub-routers."""

from fastapi import APIRouter

from src.api.routes.channel.whatsapp.connection import router as connection_router
from src.api.routes.channel.whatsapp.webhook import router as webhook_router
from src.api.routes.channel.whatsapp.auth import router as auth_router

router = APIRouter(prefix="/channel/whatsapp", tags=["whatsapp"])

router.include_router(connection_router)
router.include_router(webhook_router)
router.include_router(auth_router)
