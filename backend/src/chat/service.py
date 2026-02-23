"""Chat Service — session and message management."""

from datetime import datetime, timezone, timedelta
from typing import Any
import uuid

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import log
from src.db.models.session import Session, SessionStatus, SessionType
from src.db.models.message import Message, MessageRole


class ChatService:
    """Manages chat sessions and message history."""

    SESSION_TIMEOUT_HOURS = 24
    HISTORY_LIMIT_FOR_AGENT = 40

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(
        self,
        user_id: str,
        channel: str = "web",
        session_type: str = "general",
    ) -> Session:
        """Get existing active session or create new one."""
        timeout_threshold = datetime.now(timezone.utc) - timedelta(hours=self.SESSION_TIMEOUT_HOURS)

        conditions = [
            Session.user_id == uuid.UUID(user_id),
            Session.channel == channel,
            Session.status == SessionStatus.ACTIVE.value,
        ]

        result = await self.db.execute(
            select(Session)
            .where(and_(*conditions))
            .order_by(desc(Session.last_message_at))
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if session and session.last_message_at and session.last_message_at > timeout_threshold:
            log.debug(f"Found existing session: {session.id}")
            return session

        session = Session(
            user_id=uuid.UUID(user_id),
            channel=channel,
            session_type=session_type,
            status=SessionStatus.ACTIVE.value,
            last_message_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        log.info(f"Created new session: {session.id}")
        return session

    async def save_message(
        self,
        session_id: str | uuid.UUID,
        role: str,
        content: str,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
        tool_call_data: dict | None = None,
        channel_source: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> Message:
        """Save a message to the session."""
        message = Message(
            session_id=uuid.UUID(str(session_id)),
            role=role,
            content=content,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_call_data=tool_call_data,
            channel_source=channel_source,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self.db.add(message)

        result = await self.db.execute(
            select(Session).where(Session.id == uuid.UUID(str(session_id)))
        )
        session = result.scalar_one_or_none()
        if session:
            session.last_message_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(message)

        log.debug(f"Saved message: {message.id} role={role}")
        return message

    async def get_history_for_agent(
        self,
        session_id: str | uuid.UUID,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation history formatted for agent."""
        limit = limit or self.HISTORY_LIMIT_FOR_AGENT

        result = await self.db.execute(
            select(Session).where(Session.id == uuid.UUID(str(session_id)))
        )
        session = result.scalar_one_or_none()
        if not session:
            return []

        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == uuid.UUID(str(session_id)))
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()

        history = []

        if session.context_summary:
            history.append({
                "role": "system",
                "content": f"[Conversation summary]\n{session.context_summary}",
            })

        for msg in messages:
            if msg.role in (MessageRole.USER.value, MessageRole.ASSISTANT.value):
                history.append({"role": msg.role, "content": msg.content or ""})
            elif msg.role == MessageRole.TOOL_CALL.value:
                history.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": msg.tool_call_data.get("tool_calls", []) if msg.tool_call_data else [],
                })
            elif msg.role == MessageRole.TOOL_RESULT.value:
                history.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or "",
                    "content": msg.content or "",
                })

        return history

    async def get_session_messages(
        self,
        session_id: str | uuid.UUID,
        limit: int = 50,
    ) -> list[dict]:
        """Get messages for display (not for agent)."""
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == uuid.UUID(str(session_id)))
            .order_by(Message.created_at)
            .limit(limit)
        )
        messages = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "tool_name": m.tool_name,
                "channel_source": m.channel_source,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
