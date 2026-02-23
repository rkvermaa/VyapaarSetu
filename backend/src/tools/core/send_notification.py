"""Send WhatsApp notification via Baileys service."""

from typing import Any
import httpx

from src.tools.base import BaseTool
from src.core.logging import log
from src.config import settings


class SendNotificationTool(BaseTool):
    """Send WhatsApp notification to MSE at key onboarding milestones."""

    name = "send_notification"
    description = (
        "Send a WhatsApp notification to an MSE at milestone events: "
        "registration complete, catalogue ready, SNP matched, onboarding confirmed."
    )
    parameters = {
        "type": "object",
        "properties": {
            "whatsapp_number": {
                "type": "string",
                "description": "WhatsApp number with country code e.g. 919876543210",
            },
            "message": {
                "type": "string",
                "description": "Message to send in Hindi/English",
            },
            "milestone": {
                "type": "string",
                "enum": ["registration", "catalogue_ready", "snp_matched", "onboarding_confirmed"],
                "description": "Milestone type for tracking",
            },
        },
        "required": ["whatsapp_number", "message"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        whatsapp_number = arguments.get("whatsapp_number", "")
        message = arguments.get("message", "")
        milestone = arguments.get("milestone", "general")

        log.info(f"send_notification: to={whatsapp_number} milestone={milestone}")

        try:
            baileys_url = settings.get("BAILEYS_SERVICE_URL", "http://127.0.0.1:3001")
            api_key = settings.get("BAILEYS_API_KEY", "baileys-secret-key")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{baileys_url}/send",
                    json={"number": whatsapp_number, "message": message},
                    headers={"X-API-Key": api_key},
                )
                if response.status_code == 200:
                    return {"success": True, "milestone": milestone, "number": whatsapp_number}
                else:
                    log.warning(f"Baileys returned {response.status_code}")
                    return {"success": False, "error": f"Baileys service returned {response.status_code}"}

        except httpx.ConnectError:
            log.warning(f"WhatsApp service not available — notification not sent to {whatsapp_number}")
            return {"success": False, "error": "WhatsApp service not available (demo mode)"}
        except Exception as e:
            log.error(f"send_notification failed: {e}")
            return {"success": False, "error": str(e)}
