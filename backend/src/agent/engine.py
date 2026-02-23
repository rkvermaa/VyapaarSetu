"""Agent Engine - orchestrates skill discovery and ReAct loop."""

from typing import Any

from src.core.logging import log
from src.agent.react_agent import ReactAgent


class AgentEngine:
    """Thin orchestrator - delegates to ReactAgent.

    Maintains consistent interface for all callers (chat.py, webhooks).
    """

    def __init__(
        self,
        user_id: str,
        session_id: str,
        channel: str = "web",
        mse_id: str | None = None,
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.channel = channel
        self.mse_id = mse_id

        self._agent = ReactAgent(
            user_id=user_id,
            session_id=session_id,
            channel=channel,
            mse_id=mse_id,
        )

        log.info(f"AgentEngine: channel={channel} user={user_id[:8]}...")

    async def process_message(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Process message by delegating to ReactAgent."""
        return await self._agent.process_message(
            user_message=user_message,
            history=history,
        )
