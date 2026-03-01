"""Voice Agent — simple single-call LLM for fast voice responses.

No ReAct loop, no tools, no RAG lookup at runtime.
All knowledge is baked into the system prompt.
Optimized for <2 second response time on voice calls.
"""

import json
from typing import Any

from src.core.logging import log
from src.llm import get_llm_client
from src.agent.prompts.voice import VOICE_CATALOGUE_PROMPT


class VoiceAgent:
    """Fast voice agent — single LLM call, no tools."""

    def __init__(
        self,
        user_id: str,
        session_id: str,
        mse_id: str | None = None,
        mse_context: str = "",
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.mse_id = mse_id
        self.mse_context = mse_context
        self.llm = get_llm_client()

    def _build_history_context(self, history: list[dict[str, Any]]) -> str:
        """Extract previously collected fields from conversation history."""
        if not history:
            return ""

        extracted_fields: dict[str, str] = {}
        for msg in history:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            if "[FIELDS]" in content and "[/FIELDS]" in content:
                try:
                    fields_str = content.split("[FIELDS]")[1].split("[/FIELDS]")[0]
                    extracted_fields.update(json.loads(fields_str))
                except (json.JSONDecodeError, IndexError):
                    pass

        if not extracted_fields:
            return ""

        parts = ["## Fields already collected:"]
        for key, value in extracted_fields.items():
            parts.append(f"  - {key}: {value}")
        parts.append("\nDo NOT ask for these again. Ask the next missing field.")
        return "\n".join(parts)

    def _build_messages(
        self,
        user_message: str,
        history: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build message list: system + context + conversation."""
        system_content = VOICE_CATALOGUE_PROMPT

        # Inject MSE profile (name, registered mobile for verification)
        if self.mse_context:
            system_content += f"\n\n{self.mse_context}"

        # Inject already-collected fields
        history_ctx = self._build_history_context(history)
        if history_ctx:
            system_content += f"\n\n{history_ctx}"

        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (only user + assistant, skip tool messages)
        for msg in history:
            role = msg.get("role")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": user_message})
        return messages

    async def process_message(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Process a voice message with a single LLM call."""
        history = history or []

        log.info(
            f"VoiceAgent: user={self.user_id[:8]}... "
            f"session={self.session_id[:8]}... "
            f"history={len(history)}"
        )

        try:
            messages = self._build_messages(user_message, history)

            # Single LLM call — no tools, no loop
            response = await self.llm.chat_completion(
                messages=messages,
                tools=None,
                temperature=0.7,
                max_tokens=300,  # Voice responses must be short
            )

            return {
                "content": response.content or "",
                "usage": response.usage,
                "iterations": 1,
                "model": response.model,
                "tool_calls_made": [],
                "error": None,
            }

        except Exception as e:
            log.exception(f"VoiceAgent processing failed: {e}")
            return {
                "content": "Sorry, kuch error aa gaya. Dobara try karein.",
                "usage": {},
                "iterations": 0,
                "model": "",
                "tool_calls_made": [],
                "error": str(e),
            }
