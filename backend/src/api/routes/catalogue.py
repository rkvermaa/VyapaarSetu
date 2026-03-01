"""Catalogue chat route — AI chat for product description."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.dependencies import DBSession, CurrentUserId
from src.core.logging import log
from src.db.models.mse import MSE
from src.chat.service import ChatService
from src.agent.engine import AgentEngine
from sqlalchemy import select
import uuid

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


class CatalogueChat(BaseModel):
    message: str
    channel: str = "web"
    new_session: bool = False


@router.post("/chat")
async def catalogue_chat(req: CatalogueChat, db: DBSession, user_id: CurrentUserId):
    """AI chat for product cataloguing."""
    result = await db.execute(select(MSE).where(MSE.user_id == uuid.UUID(user_id)))
    mse = result.scalar_one_or_none()

    chat_service = ChatService(db)

    # Force new session — close existing ones so history starts fresh
    if req.new_session:
        await chat_service.close_active_sessions(
            user_id=user_id, channel=req.channel, session_type="cataloguing",
        )

    session = await chat_service.get_or_create_session(
        user_id=user_id,
        channel=req.channel,
        session_type="cataloguing",
    )

    history = await chat_service.get_history_for_agent(session.id)

    engine = AgentEngine(
        user_id=user_id,
        session_id=str(session.id),
        channel=req.channel,
        mse_id=str(mse.id) if mse else None,
    )

    result_data = await engine.process_message(req.message, history)

    await chat_service.save_message(session.id, "user", req.message)
    await chat_service.save_message(
        session.id, "assistant", result_data.get("content", ""),
        input_tokens=result_data.get("usage", {}).get("input_tokens"),
        output_tokens=result_data.get("usage", {}).get("output_tokens"),
    )

    await db.commit()

    return {
        "response": result_data.get("content", ""),
        "session_id": str(session.id),
        "tool_calls_made": result_data.get("tool_calls_made", []),
        "iterations": result_data.get("iterations", 0),
    }
