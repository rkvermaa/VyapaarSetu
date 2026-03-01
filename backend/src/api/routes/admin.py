"""NSIC Admin portal routes."""

import uuid

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from src.api.dependencies import DBSession, CurrentUserId
from src.config import settings
from src.core.logging import log
from src.db.models.mse import MSE, OnboardingStatus
from src.db.models.product import Product
from src.db.models.mse_match import MSEMatch
from src.db.models.whatsapp_auth import WhatsAppAuth

router = APIRouter(prefix="/admin", tags=["admin"])

BAILEYS_URL = settings.get("BAILEYS_SERVICE_URL", "http://127.0.0.1:3001")
BAILEYS_KEY = settings.get("BAILEYS_API_KEY", "baileys-secret-key")
BAILEYS_HEADERS = {"X-API-Key": BAILEYS_KEY, "Content-Type": "application/json"}


@router.get("/stats")
async def get_stats(db: DBSession, user_id: CurrentUserId):
    """Get dashboard statistics."""
    statuses = [
        "registered", "profile_complete", "catalogue_ready",
        "snp_selected", "submitted", "under_review", "live"
    ]

    counts = {}
    for status in statuses:
        result = await db.execute(
            select(func.count(MSE.id)).where(MSE.onboarding_status == status)
        )
        counts[status] = result.scalar() or 0

    total_result = await db.execute(select(func.count(MSE.id)))
    total = total_result.scalar() or 0

    product_result = await db.execute(select(func.count(Product.id)))
    total_products = product_result.scalar() or 0

    return {
        "total_mses": total,
        "total_products": total_products,
        "status_breakdown": counts,
        "live_count": counts.get("live", 0),
        "pipeline_count": total - counts.get("live", 0),
    }


@router.get("/queue")
async def get_verification_queue(db: DBSession, user_id: CurrentUserId):
    """Get MSEs pending verification."""
    result = await db.execute(
        select(MSE)
        .where(MSE.onboarding_status.in_(["catalogue_ready", "snp_selected", "submitted"]))
        .order_by(MSE.updated_at.desc())
        .limit(50)
    )
    mses = result.scalars().all()

    queue = []
    for mse in mses:
        prod_result = await db.execute(
            select(func.count(Product.id)).where(Product.mse_id == mse.id)
        )
        product_count = prod_result.scalar() or 0

        queue.append({
            "mse_id": str(mse.id),
            "business_name": mse.business_name,
            "state": mse.state,
            "onboarding_status": mse.onboarding_status,
            "product_count": product_count,
            "udyam_number": mse.udyam_number,
            "created_at": mse.created_at.isoformat(),
        })

    return queue


@router.put("/verify/{mse_id}")
async def verify_mse(mse_id: str, action: str, db: DBSession, user_id: CurrentUserId):
    """Approve or reject an MSE application."""
    result = await db.execute(select(MSE).where(MSE.id == uuid.UUID(mse_id)))
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE not found")

    if action == "approve":
        mse.onboarding_status = OnboardingStatus.LIVE.value
    elif action == "reject":
        mse.onboarding_status = OnboardingStatus.REGISTERED.value
    else:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    await db.flush()
    return {"success": True, "new_status": mse.onboarding_status}


# ─── WhatsApp Bot Management ────────────────────────────────────────────


class ConnectBotRequest(BaseModel):
    """Request to connect a new WhatsApp bot."""

    label: str = "WhatsApp Bot"


@router.get("/whatsapp/bots")
async def list_bots(db: DBSession, user_id: CurrentUserId):
    """List all WhatsApp bots for this admin."""
    result = await db.execute(
        select(WhatsAppAuth)
        .where(WhatsAppAuth.user_id == uuid.UUID(user_id))
        .order_by(WhatsAppAuth.created_at.desc())
    )
    bots = result.scalars().all()

    return [
        {
            "id": str(b.id),
            "label": b.label,
            "phone_number": b.phone_number,
            "status": b.status,
            "created_at": b.created_at.isoformat(),
        }
        for b in bots
    ]


@router.post("/whatsapp/bots")
async def connect_bot(req: ConnectBotRequest, db: DBSession, user_id: CurrentUserId):
    """Create a WhatsApp bot entry and start Baileys session. Returns QR code."""
    bot = WhatsAppAuth(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        label=req.label,
        status="connecting",
    )
    db.add(bot)
    await db.flush()
    await db.refresh(bot)

    bot_id = str(bot.id)

    # Start Baileys session
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{bot_id}/start",
                headers=BAILEYS_HEADERS,
            )
            data = resp.json()

            return {
                "bot_id": bot_id,
                "connected": data.get("status") == "connected",
                "phone_number": data.get("phoneNumber"),
                "qr_code": data.get("qr"),
            }
    except httpx.ConnectError:
        bot.status = "disconnected"
        await db.flush()
        raise HTTPException(status_code=503, detail="Baileys service not available")
    except Exception as e:
        log.error(f"Failed to start bot session: {e}")
        bot.status = "disconnected"
        await db.flush()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/bots/{bot_id}/status")
async def get_bot_status(bot_id: str, db: DBSession, user_id: CurrentUserId):
    """Get connection status for a specific bot (polls Baileys service)."""
    result = await db.execute(
        select(WhatsAppAuth).where(
            WhatsAppAuth.id == uuid.UUID(bot_id),
            WhatsAppAuth.user_id == uuid.UUID(user_id),
        )
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Poll Baileys for latest status
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BAILEYS_URL}/sessions/{bot_id}/status",
                headers=BAILEYS_HEADERS,
            )
            data = resp.json()

            # Sync status to DB
            new_status = data.get("status", "disconnected")
            phone = data.get("phoneNumber")
            if new_status in ("connected", "disconnected", "qr", "connecting"):
                if new_status == "qr":
                    bot.status = "connecting"
                else:
                    bot.status = new_status
                if phone:
                    bot.phone_number = phone
                await db.flush()

            return {
                "connected": data.get("connected", False),
                "phone_number": data.get("phoneNumber"),
                "status": new_status,
                "qr_code": data.get("qr"),
            }
    except httpx.ConnectError:
        return {"connected": False, "status": "service_unavailable", "qr_code": None}
    except Exception as e:
        log.error(f"Bot status check failed: {e}")
        return {"connected": False, "status": "error", "qr_code": None}


@router.post("/whatsapp/bots/{bot_id}/disconnect")
async def disconnect_bot(bot_id: str, db: DBSession, user_id: CurrentUserId):
    """Disconnect a WhatsApp bot (keeps credentials for resume)."""
    result = await db.execute(
        select(WhatsAppAuth).where(
            WhatsAppAuth.id == uuid.UUID(bot_id),
            WhatsAppAuth.user_id == uuid.UUID(user_id),
        )
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{BAILEYS_URL}/sessions/{bot_id}/disconnect",
                headers=BAILEYS_HEADERS,
            )
    except httpx.ConnectError:
        pass

    bot.status = "disconnected"
    await db.flush()
    return {"success": True}


@router.post("/whatsapp/bots/{bot_id}/reset")
async def reset_bot(bot_id: str, db: DBSession, user_id: CurrentUserId):
    """Reset a WhatsApp bot (clears credentials, requires QR re-scan)."""
    result = await db.execute(
        select(WhatsAppAuth).where(
            WhatsAppAuth.id == uuid.UUID(bot_id),
            WhatsAppAuth.user_id == uuid.UUID(user_id),
        )
    )
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Clear stored credentials
    bot.creds = {}
    bot.keys = {}
    bot.status = "connecting"
    bot.phone_number = None
    await db.flush()

    # Reset on Baileys side
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{bot_id}/reset",
                headers=BAILEYS_HEADERS,
            )
            data = resp.json()
            return {
                "bot_id": bot_id,
                "connected": data.get("status") == "connected",
                "qr_code": data.get("qr"),
            }
    except httpx.ConnectError:
        bot.status = "disconnected"
        await db.flush()
        raise HTTPException(status_code=503, detail="Baileys service not available")


@router.get("/bot-numbers")
async def get_bot_numbers(db: DBSession):
    """Return active bot phone numbers (public — used by frontend to show bot contact)."""
    result = await db.execute(
        select(WhatsAppAuth).where(WhatsAppAuth.status == "connected")
    )
    bots = result.scalars().all()
    return [
        {"phone_number": b.phone_number, "label": b.label}
        for b in bots
        if b.phone_number
    ]
