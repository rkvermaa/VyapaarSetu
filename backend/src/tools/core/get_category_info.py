"""Get ONDC category information and required attributes."""

from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

ONDC_CATEGORY_INFO = {
    "ONDC:RET10": {
        "code": "ONDC:RET10",
        "name": "Grocery",
        "mse_types": ["Spices manufacturers", "Pulses packers", "Rice millers", "Oil manufacturers"],
        "required_attributes": ["product_name", "mrp", "net_weight_or_volume", "expiry_date", "fssai_license_no", "country_of_origin", "manufacturer_name", "brand"],
        "optional_attributes": ["organic_certification", "ingredients", "nutritional_info"],
        "example_products": ["Red chilli powder", "Turmeric", "Basmati rice", "Mustard oil", "Dal"],
    },
    "ONDC:RET11": {
        "code": "ONDC:RET11",
        "name": "Food & Beverages",
        "mse_types": ["Packaged food makers", "Pickle producers", "Snack manufacturers"],
        "required_attributes": ["product_name", "mrp", "net_weight", "expiry_date", "fssai_license_no", "ingredients", "country_of_origin", "manufacturer_name"],
        "optional_attributes": ["allergen_info", "nutritional_facts", "storage_instructions"],
        "example_products": ["Mango pickle", "Papad", "Namkeen", "Fruit juice", "Murabba"],
    },
    "ONDC:RET12": {
        "code": "ONDC:RET12",
        "name": "Fashion",
        "mse_types": ["Handloom weavers", "Textile manufacturers", "Garment makers"],
        "required_attributes": ["product_name", "mrp", "size", "material_fabric", "colour", "care_instructions", "country_of_origin"],
        "optional_attributes": ["pattern", "occasion", "wash_type", "brand"],
        "example_products": ["Handloom saree", "Khadi kurta", "Block print dupatta", "Silk stole"],
    },
    "ONDC:RET13": {
        "code": "ONDC:RET13",
        "name": "Beauty & Personal Care",
        "mse_types": ["Herbal product makers", "Hair oil producers", "Natural soap makers"],
        "required_attributes": ["product_name", "mrp", "net_weight_or_volume", "ingredients", "shelf_life", "manufacturer_name", "country_of_origin"],
        "optional_attributes": ["skin_type", "certifications", "usage_instructions"],
        "example_products": ["Herbal hair oil", "Natural soap", "Ubtan powder", "Aloe vera gel"],
    },
    "ONDC:RET14": {
        "code": "ONDC:RET14",
        "name": "Electronics",
        "mse_types": ["Electronic component makers", "Accessories manufacturers"],
        "required_attributes": ["product_name", "mrp", "brand", "model_number", "warranty_period", "country_of_origin"],
        "optional_attributes": ["compatibility", "certifications", "package_contents"],
        "example_products": ["USB cables", "LED bulbs", "Phone accessories"],
    },
    "ONDC:RET15": {
        "code": "ONDC:RET15",
        "name": "Appliances",
        "mse_types": ["Small appliance manufacturers", "Kitchen equipment makers"],
        "required_attributes": ["product_name", "mrp", "brand", "warranty", "power_consumption", "voltage", "country_of_origin"],
        "optional_attributes": ["energy_rating", "package_contents"],
        "example_products": ["Mixer grinder", "Electric kettle", "Water purifier parts"],
    },
    "ONDC:RET16": {
        "code": "ONDC:RET16",
        "name": "Home & Decor",
        "mse_types": ["Brass artisans", "Wooden craft makers", "Pottery artists", "Handicraft producers"],
        "required_attributes": ["product_name", "mrp", "material", "dimensions_cm", "colour", "country_of_origin", "moq"],
        "optional_attributes": ["finish_type", "weight_kg", "care_instructions", "customization_available"],
        "example_products": ["Brass diyas", "Wooden toys", "Terracotta pots", "Jute baskets", "Marble items"],
    },
    "ONDC:RET17": {
        "code": "ONDC:RET17",
        "name": "Toys & Games",
        "mse_types": ["Handmade toy makers", "Wooden toy artisans"],
        "required_attributes": ["product_name", "mrp", "age_group", "material", "country_of_origin"],
        "optional_attributes": ["educational_value", "battery_required", "dimensions"],
        "example_products": ["Wooden alphabet blocks", "Channapatna toys", "Clay toys"],
    },
    "ONDC:RET18": {
        "code": "ONDC:RET18",
        "name": "Health & Wellness",
        "mse_types": ["Herbal manufacturers", "Ayurvedic item makers"],
        "required_attributes": ["product_name", "mrp", "net_weight", "ingredients", "manufacturer_name", "country_of_origin"],
        "optional_attributes": ["usage_instructions", "contraindications", "ayush_license"],
        "example_products": ["Chyawanprash", "Herbal kadha", "Immunity supplements"],
    },
    "ONDC:RET19": {
        "code": "ONDC:RET19",
        "name": "Pharma",
        "mse_types": ["Licensed pharmaceutical manufacturers"],
        "required_attributes": ["product_name", "mrp", "composition", "manufacturer_name", "batch_number", "expiry_date", "drug_license_no"],
        "optional_attributes": [],
        "example_products": ["Medicines", "Healthcare products"],
    },
}


class GetCategoryInfoTool(BaseTool):
    """Get ONDC category details and required attributes."""

    name = "get_category_info"
    description = (
        "Get full details about an ONDC product category including required attributes, "
        "example products, and MSE types. Use when you need category-specific guidance."
    )
    parameters = {
        "type": "object",
        "properties": {
            "category_code": {
                "type": "string",
                "description": "ONDC category code e.g. ONDC:RET16 or just RET16",
            }
        },
        "required": ["category_code"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        code = arguments.get("category_code", "").upper().strip()

        if not code.startswith("ONDC:"):
            code = f"ONDC:{code}"

        info = ONDC_CATEGORY_INFO.get(code)
        if info:
            return info

        try:
            from src.rag.qdrant_search import QdrantSearch, TAXONOMY_COLLECTION
            results = QdrantSearch.search(
                query=f"ONDC category {code}",
                collection_name=TAXONOMY_COLLECTION,
                limit=3,
            )
            if results:
                return {
                    "code": code,
                    "rag_context": [r["content"] for r in results],
                }
        except Exception as e:
            log.warning(f"RAG search for category failed: {e}")

        return {"error": f"Category {code} not found"}
