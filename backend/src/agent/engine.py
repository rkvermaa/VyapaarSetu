"""Agent Engine — orchestrator that picks the right agent based on channel.

- Voice channel → VoiceAgent (single LLM call, fast, no tools)
- Web/WhatsApp  → ReactAgent (ReAct loop with tools)
"""

import uuid
from typing import Any

from sqlalchemy import select

from src.core.logging import log
from src.agent.voice_agent import VoiceAgent
from src.agent.react_agent import ReactAgent


async def _load_mse_profile(user_id: str) -> dict[str, str]:
    """Load MSE profile from DB for injection into voice prompt."""
    try:
        from src.db.session import get_session_factory
        from src.db.models.mse import MSE
        from src.db.models.user import User

        session_factory = get_session_factory()
        async with session_factory() as db:
            # Get user mobile
            user_result = await db.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            user = user_result.scalar_one_or_none()

            # Get MSE details
            mse_result = await db.execute(
                select(MSE).where(MSE.user_id == uuid.UUID(user_id))
            )
            mse = mse_result.scalar_one_or_none()

            profile: dict[str, str] = {}
            if user:
                profile["mobile"] = user.mobile or ""
            if mse:
                profile["business_name"] = mse.business_name or ""
                profile["owner_name"] = mse.owner_name or ""
                profile["udyam_number"] = mse.udyam_number or ""
                profile["state"] = mse.state or ""
                profile["district"] = mse.district or ""
                profile["whatsapp_number"] = mse.whatsapp_number or ""
                profile["mse_id"] = str(mse.id)
            return profile
    except Exception as e:
        log.warning(f"Failed to load MSE profile for voice: {e}")
        return {}


def build_mse_context(profile: dict[str, str]) -> str:
    """Format MSE profile as text block for prompt injection."""
    if not profile or not profile.get("mobile"):
        return ""

    parts = ["## MSE (LOGGED-IN USER) INFO — from database"]
    if profile.get("owner_name"):
        parts.append(f"Name: {profile['owner_name']}")
    if profile.get("mobile"):
        parts.append(f"Registered Mobile: {profile['mobile']}")
    if profile.get("business_name"):
        parts.append(f"Business: {profile['business_name']}")
    if profile.get("udyam_number"):
        parts.append(f"Udyam Number: {profile['udyam_number']}")
    if profile.get("state"):
        loc = profile["state"]
        if profile.get("district"):
            loc += f", {profile['district']}"
        parts.append(f"Location: {loc}")

    parts.append("")
    parts.append(
        "Use this info to greet the MSE by name. "
        "For verification, compare the mobile number the user gives "
        "with the Registered Mobile above. Only proceed if it matches."
    )
    return "\n".join(parts)


async def _load_product_context(mse_id: str) -> str:
    """Load draft products with missing fields for WhatsApp prompt injection."""
    try:
        from src.db.session import get_session_factory
        from src.db.models.product import Product

        session_factory = get_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(Product)
                .where(
                    Product.mse_id == uuid.UUID(mse_id),
                    Product.status == "draft",
                )
                .order_by(Product.created_at.desc())
            )
            products = result.scalars().all()

            if not products:
                return ""

            parts = ["## PRODUCTS WITH MISSING FIELDS"]
            for p in products:
                name = p.product_name or p.raw_description[:40] if p.raw_description else "Unknown"
                category = p.ondc_category_code or "Unknown"
                score = p.compliance_score or 0
                missing = p.missing_fields or []
                attrs = p.attributes or {}

                parts.append(f"\n### Product: {name}")
                parts.append(f"Category: {category}")
                parts.append(f"Compliance: {score:.0f}%")
                if attrs:
                    parts.append("Already collected:")
                    for k, v in attrs.items():
                        parts.append(f"  - {k}: {v}")
                if missing:
                    parts.append(f"MISSING fields (ask these): {', '.join(missing)}")

            parts.append(
                "\nAsk for the FIRST missing field of the FIRST product. "
                "One field per message."
            )
            return "\n".join(parts)
    except Exception as e:
        log.warning(f"Failed to load product context: {e}")
        return ""


class AgentEngine:
    """Thin orchestrator — delegates to VoiceAgent or ReactAgent.

    Maintains the same interface so callers (catalogue.py, chat.py) don't change.
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

        # All agents are lazy-created now
        self._agent: VoiceAgent | ReactAgent | None = None

        log.info(
            f"AgentEngine: channel={channel} → "
            f"{'VoiceAgent' if channel == 'voice' else 'ReactAgent'} (lazy)"
        )

    async def _create_voice_agent(self) -> VoiceAgent:
        """Create VoiceAgent with MSE profile context from DB."""
        mse_profile = await _load_mse_profile(self.user_id)
        mse_context = build_mse_context(mse_profile)

        return VoiceAgent(
            user_id=self.user_id,
            session_id=self.session_id,
            mse_id=self.mse_id,
            mse_context=mse_context,
        )

    async def _create_react_agent(self) -> ReactAgent:
        """Create ReactAgent, with product context for WhatsApp channel."""
        product_context = ""
        if self.channel == "whatsapp" and self.mse_id:
            product_context = await _load_product_context(self.mse_id)
            if product_context:
                log.info(f"Injected product context for WhatsApp agent")

        return ReactAgent(
            user_id=self.user_id,
            session_id=self.session_id,
            channel=self.channel,
            mse_id=self.mse_id,
            product_context=product_context,
        )

    async def process_message(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Process message by delegating to the appropriate agent."""
        # Lazy-create agent on first message
        if self._agent is None:
            if self.channel == "voice":
                self._agent = await self._create_voice_agent()
            else:
                self._agent = await self._create_react_agent()

        return await self._agent.process_message(
            user_message=user_message,
            history=history,
        )
