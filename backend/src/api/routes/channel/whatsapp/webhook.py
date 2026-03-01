"""WhatsApp webhook — incoming messages from Baileys service."""

import json
import re
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select

from src.core.logging import log

router = APIRouter(prefix="/webhook")


class WebhookMessage(BaseModel):
    """Incoming message from Baileys service."""

    userId: str
    from_field: str | None = None
    fromName: str | None = None
    fromJid: str | None = None
    message: str
    messageId: str | None = None
    timestamp: int | None = None
    channel: str = "whatsapp"

    class Config:
        populate_by_name = True


def _clean_response(text: str) -> str:
    """Strip agent tags from response before sending to WhatsApp."""
    text = re.sub(r"\[FIELDS\][\s\S]*?\[/FIELDS\]", "", text)
    text = re.sub(r"\[PRODUCT_DONE\]", "", text)
    text = re.sub(r"\[CATALOGUE_COMPLETE\]", "", text)
    return text.strip()


def _normalize_phone(number: str) -> str:
    """Ensure phone number has 91 country code prefix."""
    number = re.sub(r"[^0-9]", "", number)
    if len(number) == 10:
        number = "91" + number
    return number


def _extract_fields(text: str) -> dict:
    """Extract [FIELDS]{...}[/FIELDS] JSON from agent response."""
    if "[FIELDS]" in text and "[/FIELDS]" in text:
        try:
            fields_str = text.split("[FIELDS]")[1].split("[/FIELDS]")[0]
            return json.loads(fields_str)
        except (json.JSONDecodeError, IndexError):
            pass
    return {}


async def _update_product_from_fields(
    db, mse_id: uuid.UUID, fields: dict
) -> None:
    """Update the most recent draft product with extracted field values."""
    from src.db.models.product import Product

    result = await db.execute(
        select(Product)
        .where(Product.mse_id == mse_id, Product.status == "draft")
        .order_by(Product.created_at.desc())
    )
    product = result.scalar_one_or_none()
    if not product:
        log.info(f"No draft product for MSE {mse_id} — skipping field update")
        return

    # Merge new field values into product attributes
    attrs = dict(product.attributes or {})
    updated = False

    for key, value in fields.items():
        if key in ("mobile_verified",):
            continue
        if value and str(value).strip():
            attrs[key] = str(value).strip()
            updated = True

    if not updated:
        return

    product.attributes = attrs

    # Re-validate compliance after attribute update
    try:
        from src.tools.core.validate_catalogue import ValidateCatalogueTool

        validate_tool = ValidateCatalogueTool()
        validate_result = await validate_tool.execute(
            {
                "attributes": attrs,
                "category_code": product.ondc_category_code or "ONDC:RET16",
            },
            {},
        )
        product.compliance_score = validate_result.get("compliance_score", 0.0)
        product.missing_fields = validate_result.get("missing_fields", [])

        if product.compliance_score == 100:
            product.status = "ready"
            log.info(f"Product {product.id} is now READY (100% compliance)")
    except Exception as e:
        log.warning(f"Re-validation failed for product {product.id}: {e}")

    await db.flush()
    log.info(
        f"Updated product {product.id} attributes from WhatsApp: "
        f"score={product.compliance_score}, missing={product.missing_fields}"
    )


@router.post("/message")
async def whatsapp_message(request: Request):
    """Handle incoming WhatsApp message forwarded by Baileys service."""
    try:
        body = await request.json()
        log.info(
            f"WhatsApp webhook message: from={body.get('from')}, "
            f"senderPn={body.get('senderPn', '')}, "
            f"msg={body.get('message', '')[:50]}"
        )

        sender = body.get("from", "")
        sender_pn = body.get("senderPn", "")  # Real phone from LID messages
        from_jid = body.get("fromJid", "")
        message_text = body.get("message", "")
        baileys_session_id = body.get("userId", "")

        if not message_text:
            return {"status": "ignored"}

        # Determine the real phone number — prefer senderPn over LID
        phone_for_lookup = sender_pn or sender
        if not phone_for_lookup:
            return {"status": "ignored"}

        from src.db.session import get_session_factory
        from src.db.models.mse import MSE
        from src.db.models.whatsapp_auth import WhatsAppAuth

        session_factory = get_session_factory()
        async with session_factory() as db:
            # Find MSE by phone number
            normalized = _normalize_phone(phone_for_lookup)
            mse = await _find_mse_by_phone(db, normalized)

            if not mse:
                log.info(f"Unknown WhatsApp sender: phone={phone_for_lookup}, from={sender}")
                return {"status": "unknown_user"}

            log.info(f"Matched MSE: {mse.id} (owner={mse.owner_name})")

            # Get or create chat session
            from src.chat.service import ChatService
            from src.agent.engine import AgentEngine

            chat_service = ChatService(db)
            chat_session = await chat_service.get_or_create_session(
                user_id=str(mse.user_id),
                channel="whatsapp",
                session_type="cataloguing",
            )

            history = await chat_service.get_history_for_agent(chat_session.id)

            # Translate "done" keywords
            if message_text.lower().strip() in [
                "done", "ho gaya", "complete", "finish", "bas",
            ]:
                message_text = "Mera catalogue ready hai. Ab mujhe SNP match karo."

            # Process with agent engine
            engine = AgentEngine(
                user_id=str(mse.user_id),
                session_id=str(chat_session.id),
                channel="whatsapp",
                mse_id=str(mse.id),
            )

            result_data = await engine.process_message(message_text, history)

            # Save messages
            await chat_service.save_message(chat_session.id, "user", message_text)
            response_text = result_data.get("content", "")
            await chat_service.save_message(
                chat_session.id, "assistant", response_text
            )

            # Extract fields from agent response and update product
            extracted = _extract_fields(response_text)
            if extracted:
                await _update_product_from_fields(db, mse.id, extracted)

            await db.commit()

            # Send reply back via Baileys — use fromJid for LID-based replies
            clean_reply = _clean_response(response_text)
            if clean_reply and baileys_session_id:
                # For LID-based senders, reply to the JID directly
                reply_to = from_jid if from_jid else f"{normalized}@s.whatsapp.net"
                from src.tools.core.send_notification import SendNotificationTool

                notif_tool = SendNotificationTool()
                await notif_tool.execute(
                    {
                        "whatsapp_number": reply_to,
                        "message": clean_reply,
                        "session_id": baileys_session_id,
                    },
                    {},
                )

        return {"status": "processed"}

    except Exception as e:
        log.error(f"WhatsApp webhook error: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}


async def _find_mse_by_phone(db, normalized: str):
    """Find MSE by phone number, trying multiple formats."""
    from src.db.models.mse import MSE

    # Try full normalized number (with country code)
    result = await db.execute(
        select(MSE).where(MSE.whatsapp_number == normalized)
    )
    mse = result.scalar_one_or_none()
    if mse:
        return mse

    # Try without country code (91)
    if normalized.startswith("91") and len(normalized) > 10:
        short = normalized[2:]
        result = await db.execute(
            select(MSE).where(MSE.whatsapp_number == short)
        )
        mse = result.scalar_one_or_none()
        if mse:
            return mse

    # Try with country code added
    if len(normalized) == 10:
        with_code = "91" + normalized
        result = await db.execute(
            select(MSE).where(MSE.whatsapp_number == with_code)
        )
        mse = result.scalar_one_or_none()
        if mse:
            return mse

    return None


@router.post("/status")
async def whatsapp_status(request: Request):
    """Handle status updates from Baileys service (connected/disconnected)."""
    try:
        body = await request.json()
        session_id = body.get("userId", "")
        event = body.get("event", "")
        phone_number = body.get("phoneNumber", "")

        log.info(
            f"WhatsApp status: session={session_id} event={event} phone={phone_number}"
        )

        if not session_id:
            return {"status": "ignored"}

        from src.db.session import get_session_factory
        from src.db.models.whatsapp_auth import WhatsAppAuth

        session_factory = get_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(WhatsAppAuth).where(
                    WhatsAppAuth.id == session_id
                )
            )
            auth = result.scalar_one_or_none()

            if auth:
                if event == "connected":
                    auth.status = "connected"
                    if phone_number:
                        auth.phone_number = phone_number
                elif event == "disconnected":
                    auth.status = "disconnected"

                await db.commit()
                log.info(
                    f"Updated WhatsAppAuth {session_id}: status={auth.status}"
                )
            else:
                log.warning(
                    f"WhatsAppAuth not found for session: {session_id}"
                )

        return {"status": "ok"}

    except Exception as e:
        log.error(f"WhatsApp status webhook error: {e}")
        return {"status": "error", "detail": str(e)}
