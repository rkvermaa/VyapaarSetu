"""WhatsApp webhook — incoming messages via Baileys service."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from src.core.logging import log

router = APIRouter(prefix="/channel/whatsapp", tags=["whatsapp"])


class WhatsAppMessage(BaseModel):
    from_number: str
    message_type: str = "text"
    text: str | None = None
    media_url: str | None = None


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from Baileys service."""
    try:
        body = await request.json()
        log.info(f"WhatsApp webhook: {body}")

        from_number = body.get("from", "")
        message_type = body.get("type", "text")
        text = body.get("text", {}).get("body", "") if message_type == "text" else ""

        if not from_number:
            return {"status": "ignored"}

        from src.db.session import get_session_factory
        from src.db.models.mse import MSE
        from src.db.models.user import User

        session_factory = get_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(MSE).where(MSE.whatsapp_number == from_number)
            )
            mse = result.scalar_one_or_none()

            if not mse:
                log.info(f"Unknown WhatsApp user: {from_number}")
                return {"status": "unknown_user"}

            from src.agent.engine import AgentEngine
            from src.chat.service import ChatService

            chat_service = ChatService(db)
            session = await chat_service.get_or_create_session(
                user_id=str(mse.user_id),
                channel="whatsapp",
                session_type="cataloguing",
            )

            history = await chat_service.get_history_for_agent(session.id)

            engine = AgentEngine(
                user_id=str(mse.user_id),
                session_id=str(session.id),
                channel="whatsapp",
                mse_id=str(mse.id),
            )

            if text.lower().strip() in ["done", "ho gaya", "complete", "finish"]:
                text = "Mera catalogue ready hai. Ab mujhe SNP match karo."

            result_data = await engine.process_message(text or "Hello", history)

            await chat_service.save_message(session.id, "user", text or "")
            await chat_service.save_message(
                session.id, "assistant", result_data.get("content", "")
            )

            await db.commit()

            response_text = result_data.get("content", "")
            if response_text:
                from src.tools.core.send_notification import SendNotificationTool
                notif_tool = SendNotificationTool()
                await notif_tool.execute(
                    {"whatsapp_number": from_number, "message": response_text},
                    {},
                )

        return {"status": "processed"}

    except Exception as e:
        log.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "detail": str(e)}
