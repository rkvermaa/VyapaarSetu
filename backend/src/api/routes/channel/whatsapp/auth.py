"""WhatsApp auth — Baileys credential storage API.

These endpoints are called by the Baileys service (not by the frontend).
They store/retrieve Baileys auth state in PostgreSQL.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from src.core.logging import log

router = APIRouter(prefix="/auth")


class CredsUpdate(BaseModel):
    """Update Baileys credentials."""

    creds: dict


class KeysReplace(BaseModel):
    """Replace all signal protocol keys."""

    keys: dict


class KeysPatch(BaseModel):
    """Merge/delete specific signal protocol keys."""

    set_keys: dict | None = None
    delete_keys: list[str] | None = None


@router.get("/restorable")
async def list_restorable():
    """List sessions that can be auto-restored on Baileys startup."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(WhatsAppAuth))
        all_auth = result.scalars().all()

        restorable = []
        for auth in all_auth:
            if auth.has_credentials:
                restorable.append({
                    "session_id": str(auth.id),
                    "user_id": str(auth.user_id),
                    "phone_number": auth.phone_number,
                })

    return {"sessions": restorable}


@router.get("/{session_id}")
async def get_auth(session_id: str):
    """Get stored credentials and keys for a Baileys session."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(WhatsAppAuth).where(WhatsAppAuth.id == session_id)
        )
        auth = result.scalar_one_or_none()

        if not auth:
            raise HTTPException(status_code=404, detail="Auth not found")

        return {
            "creds": auth.creds or {},
            "keys": auth.keys or {},
            "has_credentials": auth.has_credentials,
        }


@router.put("/{session_id}/creds")
async def update_creds(session_id: str, req: CredsUpdate):
    """Update Baileys auth credentials (called by Baileys on creds.update)."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(WhatsAppAuth).where(WhatsAppAuth.id == session_id)
        )
        auth = result.scalar_one_or_none()

        if not auth:
            raise HTTPException(status_code=404, detail="Auth not found")

        auth.creds = req.creds
        auth.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

    return {"success": True}


@router.put("/{session_id}/keys")
async def replace_keys(session_id: str, req: KeysReplace):
    """Replace all signal protocol keys."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(WhatsAppAuth).where(WhatsAppAuth.id == session_id)
        )
        auth = result.scalar_one_or_none()

        if not auth:
            raise HTTPException(status_code=404, detail="Auth not found")

        auth.keys = req.keys
        auth.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

    return {"success": True}


@router.patch("/{session_id}/keys")
async def patch_keys(session_id: str, req: KeysPatch):
    """Merge/delete specific signal protocol keys."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(WhatsAppAuth).where(WhatsAppAuth.id == session_id)
        )
        auth = result.scalar_one_or_none()

        if not auth:
            raise HTTPException(status_code=404, detail="Auth not found")

        current_keys = dict(auth.keys or {})

        if req.set_keys:
            current_keys.update(req.set_keys)

        if req.delete_keys:
            for key in req.delete_keys:
                current_keys.pop(key, None)

        auth.keys = current_keys
        auth.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

    return {"success": True}


@router.delete("/{session_id}")
async def delete_auth(session_id: str):
    """Delete auth on logout — Baileys calls this when session is fully logged out."""
    from src.db.session import get_session_factory
    from src.db.models.whatsapp_auth import WhatsAppAuth

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(
            select(WhatsAppAuth).where(WhatsAppAuth.id == session_id)
        )
        auth = result.scalar_one_or_none()

        if auth:
            auth.creds = {}
            auth.keys = {}
            auth.status = "disconnected"
            auth.phone_number = None
            await db.commit()

    return {"success": True}
