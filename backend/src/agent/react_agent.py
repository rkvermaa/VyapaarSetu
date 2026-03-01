"""React Agent -- multi-turn tool-calling agent for VyapaarSetu.

Uses ReAct loop: LLM - tool calls - results - repeat until response.
Supports skill discovery, RAG context, and tool execution.
"""

import json
from typing import Any

from src.config import settings
from src.core.logging import log
from src.llm import get_llm_client
from src.tools.registry import ToolRegistry
from src.skills.loader import SkillLoader
from src.rag.qdrant_search import QdrantSearch, KNOWLEDGE_COLLECTION
from src.agent.prompts.base import BASE_SYSTEM_PROMPT, KNOWLEDGE_PROMPT, WHATSAPP_RULES_PROMPT
from src.agent.prompts.voice import VOICE_CATALOGUE_PROMPT
from src.agent.prompts.whatsapp_catalogue import WHATSAPP_CATALOGUE_PROMPT


class ReactAgent:
    """ReAct loop agent for VyapaarSetu web/WhatsApp channels."""

    MAX_ITERATIONS = 5

    def __init__(
        self,
        user_id: str,
        session_id: str,
        channel: str = "web",
        mse_id: str | None = None,
        product_context: str = "",
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.channel = channel
        self.mse_id = mse_id
        self._product_context = product_context
        self.llm = get_llm_client()
        self.tool_registry = ToolRegistry()
        self._tool_calls_made: list[dict] = []

    def _discover_skill(self, message: str) -> dict[str, Any] | None:
        """Discover most relevant skill based on message keywords."""
        all_skills = SkillLoader.load_all_skills()
        if not all_skills:
            return None

        message_lower = message.lower()

        keyword_map = {
            "cataloguing": [
                "product", "catalogue", "catalog", "item", "sell", "listing",
                "mrp", "price", "material", "brass", "peetal", "saree", "spice",
                "masala", "diya", "handicraft", "category", "classify",
                "product add", "kya bechta", "kya bechte",
            ],
            "matching": [
                "snp", "platform", "which platform", "recommend", "match",
                "globallinker", "plotch", "dotpe", "esamudaay", "mystore",
                "onboard", "register on ondc", "select", "choose platform",
            ],
            "onboarding": [
                "register", "udyam", "eligibility", "team", "scheme",
                "kya hai", "what is", "signup", "how to", "profile",
                "business name", "owner", "district", "state", "turnover",
            ],
        }

        best_skill = None
        best_score = 0

        for skill_slug, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > best_score:
                best_score = score
                best_skill = skill_slug

        if best_skill and best_skill in all_skills:
            return all_skills[best_skill]

        if self.channel == "whatsapp":
            return all_skills.get("cataloguing") or all_skills.get("onboarding")

        return all_skills.get("onboarding")

    def _setup_tools(self, skill: dict[str, Any]) -> None:
        tool_names = skill.get("tools", [])
        skill_slug = skill.get("slug", "")
        enabled = self.tool_registry.enable_tools_for_skill(tool_names, skill_slug)
        log.debug(f"Enabled {enabled} tools for skill: {skill_slug}")

    def _load_rag_context(self, user_message: str) -> str:
        try:
            return QdrantSearch.build_context(
                user_message,
                collection_name=KNOWLEDGE_COLLECTION,
                max_tokens=800,
            )
        except Exception as e:
            log.warning(f"RAG context loading failed: {e}")
            return ""

    def _build_history_context(self, history: list[dict[str, Any]]) -> str:
        if not history:
            return ""

        assistant_msgs = [m for m in history if m.get("role") == "assistant"]
        extracted_fields: dict[str, str] = {}
        for msg in assistant_msgs:
            content = msg.get("content", "")
            if "[FIELDS]" in content and "[/FIELDS]" in content:
                try:
                    fields_str = content.split("[FIELDS]")[1].split("[/FIELDS]")[0]
                    extracted_fields.update(json.loads(fields_str))
                except Exception:
                    pass

        if not extracted_fields:
            return ""

        parts = ["## Fields Already Collected\nDo NOT ask for these again:"]
        for key, value in extracted_fields.items():
            parts.append(f"  - {key}: {value}")

        return "\n".join(parts)

    def _build_system_prompt(
        self,
        skill: dict[str, Any],
        rag_context: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        from datetime import date

        today = date.today().strftime("%d %B %Y")
        skill_name = skill["name"]

        # Voice channel: use dedicated short-response prompt
        if self.channel == "voice":
            log.info("Using VOICE_CATALOGUE_PROMPT (voice channel)")
            parts = [
                VOICE_CATALOGUE_PROMPT,
                f"\n## Today Date: {today}",
            ]
            history_context = self._build_history_context(history or [])
            if history_context:
                parts.append(history_context)
            return "\n\n".join(parts)

        # WhatsApp + cataloguing: use dedicated short WhatsApp prompt
        if self.channel == "whatsapp" and skill.get("slug") == "cataloguing":
            log.info("Using WHATSAPP_CATALOGUE_PROMPT (whatsapp + cataloguing)")
            parts = [
                WHATSAPP_CATALOGUE_PROMPT,
                f"\n## Today Date: {today}",
            ]
            if self._product_context:
                parts.append(self._product_context)
            history_context = self._build_history_context(history or [])
            if history_context:
                parts.append(history_context)
            return "\n\n".join(parts)

        parts = [
            BASE_SYSTEM_PROMPT,
            f"\n## Today Date: {today}",
            f"\n## Current Channel: {self.channel}",
            f"\n## Active Skill: {skill_name}",
            skill.get("system_prompt", ""),
        ]

        if self.mse_id:
            parts.append(f"\n## MSE Context\nMSE ID: {self.mse_id}")

        if rag_context:
            parts.append(f"\n## Reference Context\n{rag_context}")

        history_context = self._build_history_context(history or [])
        if history_context:
            parts.append(history_context)

        parts.append(KNOWLEDGE_PROMPT)

        if self.channel == "whatsapp":
            parts.append(WHATSAPP_RULES_PROMPT)

        return "\n\n".join(parts)

    def _build_tool_context(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "channel": self.channel,
            "mse_id": self.mse_id,
        }

    async def process_message(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        history = history or []
        self._tool_calls_made = []

        log.info(
            f"ReactAgent: user={self.user_id[:8]}... "
            f"channel={self.channel} session={self.session_id[:8]}..."
        )

        try:
            skill = self._discover_skill(user_message)
            if not skill:
                return {
                    "content": "Mujhe samajh nahin aaya. Kya aap phir se batayenge?",
                    "usage": {}, "iterations": 0, "model": "",
                    "tool_calls_made": [], "error": "no_skill_found",
                }

            skill_name = skill["name"]
            log.info(f"Discovered skill: {skill_name}")
            self._setup_tools(skill)
            rag_context = self._load_rag_context(user_message)
            system_prompt = self._build_system_prompt(skill, rag_context, history)

            messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            tools = self.tool_registry.get_tool_definitions()
            log.info(f"Enabled tools: {self.tool_registry.get_enabled_tools()}")

            return await self._react_loop(messages, tools)

        except Exception as e:
            log.exception(f"ReactAgent processing failed: {e}")
            return {
                "content": "Sorry, an error occurred. Please try again.",
                "usage": {}, "iterations": 0, "model": "",
                "tool_calls_made": [], "error": str(e),
            }

    async def _react_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        iteration = 0
        total_input = 0
        total_output = 0

        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            log.debug(f"ReAct iteration {iteration}/{self.MAX_ITERATIONS}")

            response = await self.llm.chat_completion(
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
            )

            total_input += response.usage.get("input_tokens", 0)
            total_output += response.usage.get("output_tokens", 0)

            if response.has_tool_calls:
                tool_results = await self._execute_tools(response.tool_calls)
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [tc.to_dict() for tc in response.tool_calls],
                })
                for tool_call, result in zip(response.tool_calls, tool_results):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                continue

            return {
                "content": response.content or "",
                "usage": {"input_tokens": total_input, "output_tokens": total_output},
                "iterations": iteration,
                "model": response.model,
                "tool_calls_made": self._tool_calls_made,
                "error": None,
            }

        return {
            "content": "I am having trouble. Please try again with a simpler question.",
            "usage": {"input_tokens": total_input, "output_tokens": total_output},
            "iterations": iteration,
            "model": self.llm.model_name,
            "tool_calls_made": self._tool_calls_made,
            "error": "max_iterations_reached",
        }

    async def _execute_tools(self, tool_calls: list) -> list[str]:
        results = []
        tool_context = self._build_tool_context()

        for tc in tool_calls:
            log.info(f"Executing tool: {tc.name} args={tc.arguments}")
            try:
                result = await self.tool_registry.execute_tool(
                    name=tc.name, arguments=tc.arguments, context=tool_context,
                )
                self._tool_calls_made.append({
                    "tool": tc.name, "arguments": tc.arguments, "success": True,
                })
                result_str = json.dumps(result) if isinstance(result, dict) else str(result)
                results.append(result_str)
                log.info(f"Tool {tc.name} result: {result_str[:200]}...")
            except Exception as e:
                log.error(f"Tool {tc.name} failed: {e}")
                self._tool_calls_made.append({
                    "tool": tc.name, "arguments": tc.arguments, "success": False, "error": str(e),
                })
                results.append(json.dumps({"error": str(e)}))

        return results
