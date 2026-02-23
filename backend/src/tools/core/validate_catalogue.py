"""Validate product catalogue against ONDC compliance rules."""

from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

CATEGORY_REQUIRED_ATTRIBUTES = {
    "ONDC:RET10": ["product_name", "mrp", "net_weight_or_volume", "fssai_license_no", "country_of_origin"],
    "ONDC:RET11": ["product_name", "mrp", "net_weight", "fssai_license_no", "ingredients", "country_of_origin"],
    "ONDC:RET12": ["product_name", "mrp", "size", "material_fabric", "colour", "country_of_origin"],
    "ONDC:RET13": ["product_name", "mrp", "net_weight_or_volume", "ingredients", "shelf_life", "country_of_origin"],
    "ONDC:RET14": ["product_name", "mrp", "brand", "model_number", "warranty_period", "country_of_origin"],
    "ONDC:RET15": ["product_name", "mrp", "brand", "warranty", "power_consumption", "country_of_origin"],
    "ONDC:RET16": ["product_name", "mrp", "material", "dimensions_cm", "colour", "country_of_origin", "moq"],
    "ONDC:RET17": ["product_name", "mrp", "age_group", "material", "country_of_origin"],
    "ONDC:RET18": ["product_name", "mrp", "net_weight", "ingredients", "country_of_origin"],
    "ONDC:RET19": ["product_name", "mrp", "composition", "manufacturer_name", "batch_number", "expiry_date", "drug_license_no"],
}


class ValidateCatalogueTool(BaseTool):
    """Validate product attributes against ONDC compliance rules."""

    name = "validate_catalogue"
    description = (
        "Validate product attributes against ONDC E-Commerce Rules 2020 and Legal Metrology Act 2011. "
        "Returns compliance score (0-100), missing mandatory fields, and warnings."
    )
    parameters = {
        "type": "object",
        "properties": {
            "attributes": {
                "type": "object",
                "description": "Product attributes dict (mrp, material, dimensions, etc.)",
            },
            "category_code": {
                "type": "string",
                "description": "ONDC category code e.g. ONDC:RET16",
            },
        },
        "required": ["attributes", "category_code"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        attributes = arguments.get("attributes", {})
        category_code = arguments.get("category_code", "ONDC:RET16")

        required_fields = CATEGORY_REQUIRED_ATTRIBUTES.get(category_code, [
            "product_name", "mrp", "country_of_origin"
        ])

        missing_fields = []
        present_fields = []
        for field in required_fields:
            value = attributes.get(field)
            if value is None or value == "" or value == "null":
                missing_fields.append(field)
            else:
                present_fields.append(field)

        if required_fields:
            compliance_score = (len(present_fields) / len(required_fields)) * 100
        else:
            compliance_score = 100.0

        warnings = []
        mrp = attributes.get("mrp")
        if mrp and (not isinstance(mrp, (int, float)) or mrp <= 0):
            warnings.append("MRP must be a positive number")

        country = attributes.get("country_of_origin", "")
        if country and country.lower() not in ["india", "bharat"]:
            warnings.append("Verify country_of_origin — most MSME products should be India")

        if category_code in ("ONDC:RET10", "ONDC:RET11"):
            if not attributes.get("fssai_license_no"):
                warnings.append("FSSAI license number is legally mandatory for food products")

        if compliance_score == 100:
            status = "compliant"
            message = "Product catalogue is fully compliant with ONDC requirements."
        elif compliance_score >= 70:
            status = "partial"
            message = f"Catalogue is {compliance_score:.0f}% complete. Fill missing fields to go live."
        else:
            status = "incomplete"
            message = f"Catalogue needs more information ({compliance_score:.0f}% complete)."

        return {
            "compliance_score": round(compliance_score, 1),
            "status": status,
            "message": message,
            "required_fields": required_fields,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "warnings": warnings,
        }
