"""Classify product to ONDC RET category using LLM."""

import json
from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

ONDC_CATEGORIES = {
    "ONDC:RET10": "Grocery (spices, pulses, rice, oils, condiments)",
    "ONDC:RET11": "Food & Beverages (packaged food, pickles, snacks, beverages, jam, chutney)",
    "ONDC:RET12": "Fashion (handloom, textiles, sarees, kurtas, garments, embroidery, dupatta)",
    "ONDC:RET13": "Beauty & Personal Care (herbal, hair oil, natural soap, ubtan, aloe vera)",
    "ONDC:RET14": "Electronics (USB cables, LED bulbs, phone accessories, components)",
    "ONDC:RET15": "Appliances (mixer grinder, water purifier, kettle, kitchen equipment)",
    "ONDC:RET16": "Home & Decor (brass, handicrafts, wooden toys, terracotta, jute, marble)",
    "ONDC:RET17": "Toys & Games (handmade toys, wooden blocks, Channapatna toys, clay toys)",
    "ONDC:RET18": "Health & Wellness (Ayurvedic, herbal supplements, chyawanprash, kadha)",
    "ONDC:RET19": "Pharma (medicines, licensed pharmaceutical products)",
}


class ClassifyProductTool(BaseTool):
    """Classify a product description to ONDC RET category."""

    name = "classify_product"
    description = (
        "Classify a product description to the correct ONDC retail category (RET10-RET19). "
        "Returns category code, subcategory, and confidence score."
    )
    parameters = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Product description in Hindi, English, or Hinglish",
            }
        },
        "required": ["description"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        description = arguments.get("description", "")

        try:
            from src.llm import get_llm_client
            llm = get_llm_client()

            categories_list = "\n".join(
                f"- {code}: {desc}" for code, desc in ONDC_CATEGORIES.items()
            )

            prompt = f"""You are an ONDC product categorization expert.

ONDC Retail Categories:
{categories_list}

Product Description: {description}

Classify this product into the most appropriate ONDC category.
Also determine a specific subcategory within that category.

Respond ONLY in JSON format:
{{"category_code": "ONDC:RET16", "category_name": "Home & Decor", "subcategory": "Brass Handicrafts", "confidence": 0.95, "reasoning": "This is a brass decorative item"}}"""

            response = await llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            content = response.content or "{}"
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result

        except json.JSONDecodeError:
            log.warning("JSON parse failed for classify_product, using fallback")
            return {
                "category_code": "ONDC:RET16",
                "category_name": "Home & Decor",
                "subcategory": "General",
                "confidence": 0.5,
                "reasoning": "Could not classify precisely",
            }
        except Exception as e:
            log.error(f"classify_product failed: {e}")
            return {"error": str(e)}
