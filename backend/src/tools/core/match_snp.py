"""Match MSE to best-fit SNPs using scoring algorithm + semantic similarity."""

import json
from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log

SNP_DATA = [
    {
        "id": "snp_globallinker",
        "name": "GlobalLinker",
        "supported_categories": ["ONDC:RET10", "ONDC:RET12", "ONDC:RET13", "ONDC:RET14", "ONDC:RET15", "ONDC:RET16", "ONDC:RET18"],
        "supported_states": ["All India"],
        "b2b": True,
        "b2c": True,
        "avg_onboarding_days": 7,
        "description": "Broad category coverage, strong in manufacturing sector, B2B focus. Best for handicrafts, fashion, multi-category MSEs.",
    },
    {
        "id": "snp_plotch",
        "name": "Plotch",
        "supported_categories": ["ONDC:RET10", "ONDC:RET12", "ONDC:RET13", "ONDC:RET14", "ONDC:RET15", "ONDC:RET16", "ONDC:RET18"],
        "supported_states": ["All India"],
        "b2b": False,
        "b2c": True,
        "avg_onboarding_days": 5,
        "description": "Fast onboarding, consumer-focused, catalogue quality support. Best for B2C MSEs wanting quick go-live.",
    },
    {
        "id": "snp_sellerapp",
        "name": "SellerApp",
        "supported_categories": ["ONDC:RET10", "ONDC:RET12", "ONDC:RET14", "ONDC:RET16"],
        "supported_states": ["All India"],
        "b2b": True,
        "b2c": True,
        "avg_onboarding_days": 10,
        "description": "Strong analytics, seller performance tools. Best for electronics and tech-forward MSEs.",
    },
    {
        "id": "snp_esamudaay",
        "name": "eSamudaay",
        "supported_categories": ["ONDC:RET11"],
        "supported_states": ["All India"],
        "b2b": False,
        "b2c": True,
        "avg_onboarding_days": 4,
        "description": "Specialist in Food and Beverages. Fastest onboarding. Best for pickle, snack, packaged food MSEs.",
    },
    {
        "id": "snp_dotpe",
        "name": "DotPe",
        "supported_categories": ["ONDC:RET10", "ONDC:RET11", "ONDC:RET12", "ONDC:RET13", "ONDC:RET16"],
        "supported_states": ["All India"],
        "b2b": False,
        "b2c": True,
        "avg_onboarding_days": 6,
        "description": "Strong consumer reach, popular with food and fashion. Best for multi-category B2C MSEs.",
    },
    {
        "id": "snp_mystore",
        "name": "MyStore",
        "supported_categories": ["ONDC:RET10", "ONDC:RET12", "ONDC:RET13", "ONDC:RET14", "ONDC:RET16"],
        "supported_states": ["All India"],
        "b2b": False,
        "b2c": True,
        "avg_onboarding_days": 7,
        "description": "Easy-to-use seller interface, good for first-time digital sellers. Best for Home and Decor, Fashion.",
    },
]


class MatchSNPTool(BaseTool):
    """Match MSE profile to best-fit SNPs using scoring algorithm."""

    name = "match_snp"
    description = (
        "Find the best-fit SNPs (Seller Network Participants) for an MSE based on "
        "product categories, geography, B2B/B2C preference. Returns top 3 matches with scores."
    )
    parameters = {
        "type": "object",
        "properties": {
            "product_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ONDC category codes the MSE sells in e.g. [ONDC:RET16, ONDC:RET12]",
            },
            "transaction_type": {
                "type": "string",
                "enum": ["b2b", "b2c", "both"],
                "description": "MSE preferred transaction type",
            },
            "target_states": {
                "type": "array",
                "items": {"type": "string"},
                "description": "States where MSE wants to sell",
            },
            "mse_state": {
                "type": "string",
                "description": "State where MSE is located",
            },
        },
        "required": ["product_categories"],
    }

    def _calculate_category_overlap(self, mse_categories: list[str], snp_categories: list[str]) -> float:
        """Calculate category overlap score (0-100)."""
        if not mse_categories:
            return 0.0
        matched = sum(1 for c in mse_categories if c in snp_categories)
        return (matched / len(mse_categories)) * 100

    def _calculate_geography_score(
        self, target_states: list[str], snp_states: list[str], mse_state: str
    ) -> float:
        """Calculate geography coverage score (0-100)."""
        if "All India" in snp_states:
            return 100.0
        if not target_states:
            return 50.0
        matched = sum(1 for s in target_states if s in snp_states)
        return (matched / len(target_states)) * 100

    def _calculate_transaction_score(
        self, mse_transaction_type: str, snp_b2b: bool, snp_b2c: bool
    ) -> float:
        """Calculate transaction type alignment score (0-100)."""
        if mse_transaction_type == "b2b":
            return 100.0 if snp_b2b else 0.0
        elif mse_transaction_type == "b2c":
            return 100.0 if snp_b2c else 0.0
        elif mse_transaction_type == "both":
            if snp_b2b and snp_b2c:
                return 100.0
            elif snp_b2b or snp_b2c:
                return 50.0
            return 0.0
        return 50.0

    def _calculate_capacity_score(self, avg_onboarding_days: int) -> float:
        """Calculate capacity/speed score (0-100)."""
        score = max(0, min(100, ((10 - avg_onboarding_days) / 6) * 100))
        return round(score, 1)

    def _generate_match_reasons(
        self, snp: dict, mse_categories: list[str], transaction_type: str, avg_days: int,
    ) -> list[str]:
        """Generate human-readable match reasons."""
        reasons = []
        matched_cats = [c for c in mse_categories if c in snp["supported_categories"]]
        cat_names = {
            "ONDC:RET10": "Grocery", "ONDC:RET11": "Food and Beverages",
            "ONDC:RET12": "Fashion", "ONDC:RET13": "Beauty and Personal Care",
            "ONDC:RET14": "Electronics", "ONDC:RET15": "Appliances",
            "ONDC:RET16": "Home and Decor", "ONDC:RET17": "Toys",
            "ONDC:RET18": "Health and Wellness", "ONDC:RET19": "Pharma",
        }
        if matched_cats:
            names = [cat_names.get(c, c) for c in matched_cats]
            reasons.append(f"Supports your categories: {chr(44).join(names)}")
        if "All India" in snp["supported_states"]:
            reasons.append("Covers all India - your products will reach buyers nationwide")
        if transaction_type == "b2b" and snp["b2b"]:
            reasons.append("Supports B2B transactions matching your business model")
        elif transaction_type == "b2c" and snp["b2c"]:
            reasons.append("Strong B2C consumer reach")
        elif transaction_type == "both" and snp["b2b"] and snp["b2c"]:
            reasons.append("Supports both B2B and B2C - matches your flexible model")
        reasons.append(f"Average onboarding time: {avg_days} days")
        return reasons

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        mse_categories = arguments.get("product_categories", [])
        transaction_type = arguments.get("transaction_type", "b2c")
        target_states = arguments.get("target_states", [])
        mse_state = arguments.get("mse_state", "")

        if not mse_categories:
            return {"error": "No product categories provided"}

        scored_snps = []
        for snp in SNP_DATA:
            cat_score = self._calculate_category_overlap(mse_categories, snp["supported_categories"])
            geo_score = self._calculate_geography_score(target_states, snp["supported_states"], mse_state)
            txn_score = self._calculate_transaction_score(transaction_type, snp["b2b"], snp["b2c"])
            cap_score = self._calculate_capacity_score(snp["avg_onboarding_days"])

            total_score = (
                cat_score * 0.45 +
                geo_score * 0.25 +
                txn_score * 0.20 +
                cap_score * 0.10
            )

            if cat_score == 0:
                continue

            reasons = self._generate_match_reasons(
                snp, mse_categories, transaction_type, snp["avg_onboarding_days"]
            )

            scored_snps.append({
                "snp_id": snp["id"],
                "snp_name": snp["name"],
                "match_score": round(total_score, 1),
                "match_reasons": reasons,
                "category_overlap": round(cat_score, 1),
                "geography_score": round(geo_score, 1),
                "transaction_score": round(txn_score, 1),
                "capacity_score": round(cap_score, 1),
                "avg_onboarding_days": snp["avg_onboarding_days"],
                "b2b": snp["b2b"],
                "b2c": snp["b2c"],
                "description": snp["description"],
            })

        scored_snps.sort(key=lambda x: x["match_score"], reverse=True)
        top_3 = scored_snps[:3]

        return {
            "matches": top_3,
            "total_snps_evaluated": len(SNP_DATA),
            "categories_searched": mse_categories,
            "transaction_type": transaction_type,
        }
