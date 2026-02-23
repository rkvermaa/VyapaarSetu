"""Fetch Udyam registration data — mocked for PoC."""

import random
from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

# Mock Udyam data for demo personas
MOCK_UDYAM_DATA = {
    "UDYAM-MH-01-0012345": {
        "udyam_number": "UDYAM-MH-01-0012345",
        "business_name": "Sharma Brass Works",
        "owner_name": "Rajesh Sharma",
        "nic_code": "25910",
        "major_activity": "manufacturing",
        "state": "Maharashtra",
        "district": "Pune",
        "address": "Plot 12, MIDC Bhosari, Pune - 411026",
        "turnover": 5000000,
        "employee_count": 12,
    },
    "UDYAM-TN-05-0067890": {
        "udyam_number": "UDYAM-TN-05-0067890",
        "business_name": "Priya Textiles",
        "owner_name": "Priya Venkataraman",
        "nic_code": "13111",
        "major_activity": "manufacturing",
        "state": "Tamil Nadu",
        "district": "Kanchipuram",
        "address": "No. 45, Silk Weavers Colony, Kanchipuram - 631502",
        "turnover": 3500000,
        "employee_count": 8,
    },
    "UDYAM-UP-09-0034567": {
        "udyam_number": "UDYAM-UP-09-0034567",
        "business_name": "Organic Farms Co",
        "owner_name": "Ramesh Kumar",
        "nic_code": "10750",
        "major_activity": "manufacturing",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "address": "Village Mallpur, Lucknow - 226012",
        "turnover": 2000000,
        "employee_count": 5,
    },
}


class FetchUdyamDataTool(BaseTool):
    """Fetch MSE business details from Udyam Registration Number (mocked for PoC)."""

    name = "fetch_udyam_data"
    description = (
        "Fetch MSE business details from Udyam Registration Number. "
        "Returns business name, owner name, NIC code, state, district, turnover, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "udyam_number": {
                "type": "string",
                "description": "Udyam Registration Number (e.g. UDYAM-MH-01-0012345)",
            }
        },
        "required": ["udyam_number"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        udyam_number = arguments.get("udyam_number", "").strip().upper()
        log.info(f"FetchUdyamData: looking up {udyam_number}")

        # Check mock data
        if udyam_number in MOCK_UDYAM_DATA:
            return {"success": True, "data": MOCK_UDYAM_DATA[udyam_number]}

        # Validate format
        if not udyam_number.startswith("UDYAM-"):
            return {
                "success": False,
                "error": "Invalid Udyam number format. Should be like UDYAM-MH-01-0012345",
            }

        # Return generic mock for any valid-format number
        parts = udyam_number.split("-")
        state_code = parts[1] if len(parts) > 1 else "XX"
        state_map = {
            "MH": "Maharashtra", "TN": "Tamil Nadu", "UP": "Uttar Pradesh",
            "RJ": "Rajasthan", "GJ": "Gujarat", "KA": "Karnataka",
            "WB": "West Bengal", "DL": "Delhi", "MP": "Madhya Pradesh",
        }

        return {
            "success": True,
            "data": {
                "udyam_number": udyam_number,
                "business_name": "Sample Business",
                "owner_name": "Business Owner",
                "nic_code": "25910",
                "major_activity": "manufacturing",
                "state": state_map.get(state_code, "Maharashtra"),
                "district": "District",
                "address": "Business Address",
                "turnover": 3000000,
                "employee_count": 10,
            },
        }
