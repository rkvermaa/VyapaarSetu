"""Extract ONDC-required attributes from product description using LLM NER."""

import json
from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

CATEGORY_REQUIRED_ATTRIBUTES = {
    "ONDC:RET10": ["product_name", "mrp", "net_weight_or_volume", "expiry_date", "fssai_license_no", "country_of_origin", "manufacturer_name", "brand"],
    "ONDC:RET11": ["product_name", "mrp", "net_weight", "expiry_date", "fssai_license_no", "ingredients", "country_of_origin", "manufacturer_name"],
    "ONDC:RET12": ["product_name", "mrp", "size", "material_fabric", "colour", "care_instructions", "country_of_origin"],
    "ONDC:RET13": ["product_name", "mrp", "net_weight_or_volume", "ingredients", "shelf_life", "manufacturer_name", "country_of_origin"],
    "ONDC:RET14": ["product_name", "mrp", "brand", "model_number", "warranty_period", "country_of_origin"],
    "ONDC:RET15": ["product_name", "mrp", "brand", "warranty", "power_consumption", "voltage", "country_of_origin"],
    "ONDC:RET16": ["product_name", "mrp", "material", "dimensions_cm", "colour", "country_of_origin", "moq"],
    "ONDC:RET17": ["product_name", "mrp", "age_group", "material", "country_of_origin"],
    "ONDC:RET18": ["product_name", "mrp", "net_weight", "ingredients", "manufacturer_name", "country_of_origin"],
    "ONDC:RET19": ["product_name", "mrp", "composition", "manufacturer_name", "batch_number", "expiry_date", "drug_license_no"],
}


class ExtractAttributesTool(BaseTool):
    """Extract ONDC-required product attributes from a description using NER."""

    name = "extract_attributes"
    description = (
        "Extract all ONDC-required product attributes (MRP, material, dimensions, MOQ, HSN code, etc.) "
        "from a product description for a given category. Returns structured attributes and missing fields."
    )
    parameters = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Product description in any language",
            },
            "category_code": {
                "type": "string",
                "description": "ONDC category code e.g. ONDC:RET16",
            },
        },
        "required": ["description", "category_code"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        description = arguments.get("description", "")
        category_code = arguments.get("category_code", "ONDC:RET16")

        required_fields = CATEGORY_REQUIRED_ATTRIBUTES.get(category_code, [
            "product_name", "mrp", "country_of_origin"
        ])

        try:
            from src.llm import get_llm_client
            llm = get_llm_client()

            fields_list = ", ".join(required_fields)
            prompt = f"""You are an ONDC product data extraction expert.

Product Description: {description}
ONDC Category: {category_code}
Required fields to extract: {fields_list}

Extract all available information from the description. For fields not mentioned, use null.

Respond ONLY in JSON format with all required fields:
{{
  "product_name": "...",
  "mrp": 150,
  "country_of_origin": "India",
  ... (all required fields)
}}

Also include "hsn_code" if mentioned or inferrable from context."""

            response = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            content = response.content or "{}"
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            attributes = json.loads(content.strip())
            missing = [f for f in required_fields if not attributes.get(f)]

            return {
                "attributes": attributes,
                "required_fields": required_fields,
                "missing_fields": missing,
                "extracted_count": len(required_fields) - len(missing),
                "total_required": len(required_fields),
            }

        except Exception as e:
            log.error(f"extract_attributes failed: {e}")
            return {
                "attributes": {"product_name": description[:50]},
                "required_fields": required_fields,
                "missing_fields": required_fields[1:],
                "extracted_count": 1,
                "total_required": len(required_fields),
                "error": str(e),
            }
