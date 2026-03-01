"""WhatsApp connection management — connect/disconnect/send/status via Baileys."""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.core.logging import log

router = APIRouter()

BAILEYS_URL = settings.get("BAILEYS_SERVICE_URL", "http://127.0.0.1:3001")
BAILEYS_KEY = settings.get("BAILEYS_API_KEY", "baileys-secret-key")
HEADERS = {"X-API-Key": BAILEYS_KEY, "Content-Type": "application/json"}


class SendRequest(BaseModel):
    """Request to send a WhatsApp message."""

    session_id: str
    to: str
    message: str


@router.post("/connect")
async def connect(session_id: str, label: str = "WhatsApp Bot"):
    """Start a Baileys session and return QR or connected status."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{session_id}/start",
                headers=HEADERS,
            )
            data = resp.json()
            return data
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Baileys service not available")
    except Exception as e:
        log.error(f"WhatsApp connect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(session_id: str):
    """Get connection status for a Baileys session."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BAILEYS_URL}/sessions/{session_id}/status",
                headers=HEADERS,
            )
            return resp.json()
    except httpx.ConnectError:
        return {"status": "service_unavailable", "connected": False}
    except Exception as e:
        log.error(f"WhatsApp status error: {e}")
        return {"status": "error", "connected": False}


@router.post("/send")
async def send_message(req: SendRequest):
    """Send a WhatsApp message via Baileys session."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{req.session_id}/send",
                headers=HEADERS,
                json={"to": req.to, "message": req.message},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Send failed")
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Baileys service not available")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect(session_id: str):
    """Soft disconnect a Baileys session (keeps credentials)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{session_id}/disconnect",
                headers=HEADERS,
            )
            return resp.json()
    except httpx.ConnectError:
        return {"success": True, "message": "Service not running"}
    except Exception as e:
        log.error(f"WhatsApp disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_session(session_id: str):
    """Hard reset a Baileys session (clears credentials, needs QR re-scan)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{BAILEYS_URL}/sessions/{session_id}/reset",
                headers=HEADERS,
            )
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Baileys service not available")
    except Exception as e:
        log.error(f"WhatsApp reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
