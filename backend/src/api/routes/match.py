"""SNP matching routes."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, delete

from src.api.dependencies import DBSession, CurrentUserId
from src.core.logging import log
from src.db.models.mse import MSE
from src.db.models.mse_match import MSEMatch, MatchStatus
from src.db.models.product import Product, ProductStatus

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/generate", include_in_schema=True)
@router.post("/generate/", include_in_schema=False)
async def generate_matches(db: DBSession, user_id: CurrentUserId):
    """Run AI matching for MSE — saves top 3 to MSEMatch table."""
    result = await db.execute(select(MSE).where(MSE.user_id == uuid.UUID(user_id)))
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    result = await db.execute(
        select(Product).where(
            Product.mse_id == mse.id,
            Product.ondc_category_code.isnot(None),
        )
    )
    products = result.scalars().all()
    categories = list(set(p.ondc_category_code for p in products if p.ondc_category_code))

    if not categories:
        return {"error": "No product categories found. Please add products first."}

    from src.tools.core.match_snp import MatchSNPTool
    match_tool = MatchSNPTool()
    match_result = await match_tool.execute(
        {
            "product_categories": categories,
            "transaction_type": mse.transaction_type or "b2c",
            "target_states": mse.target_states or [],
            "mse_state": mse.state or "",
        },
        {},
    )

    matches = match_result.get("matches", [])
    if not matches:
        return {"error": "No SNP matches found for your categories"}

    await db.execute(
        delete(MSEMatch).where(
            MSEMatch.mse_id == mse.id,
            MSEMatch.status == MatchStatus.SUGGESTED.value,
        )
    )

    saved_matches = []
    for match in matches[:3]:
        from src.db.models.snp import SNP
        result = await db.execute(select(SNP).where(SNP.name == match["snp_name"]))
        snp = result.scalar_one_or_none()

        if not snp:
            snp = SNP(
                id=uuid.uuid4(),
                name=match["snp_name"],
                platform_name=match["snp_name"],
                supported_categories=categories,
                supported_states=["All India"],
                b2b=match.get("b2b", False),
                b2c=match.get("b2c", True),
                avg_onboarding_days=match.get("avg_onboarding_days", 7),
                capability_score=match.get("match_score", 75.0),
            )
            db.add(snp)
            await db.flush()

        mse_match = MSEMatch(
            id=uuid.uuid4(),
            mse_id=mse.id,
            snp_id=snp.id,
            match_score=match["match_score"],
            match_reasons=match["match_reasons"],
            category_overlap_score=match.get("category_overlap", 0.0),
            geography_score=match.get("geography_score", 0.0),
            transaction_type_score=match.get("transaction_score", 0.0),
            capacity_score=match.get("capacity_score", 0.0),
            status=MatchStatus.SUGGESTED.value,
        )
        db.add(mse_match)
        saved_matches.append(match)

    await db.flush()
    log.info(f"Generated {len(saved_matches)} matches for MSE {mse.id}")

    return {
        "success": True,
        "matches_generated": len(saved_matches),
        "matches": saved_matches,
    }


@router.get("/recommendations", include_in_schema=True)
@router.get("/recommendations/", include_in_schema=False)
async def get_recommendations(db: DBSession, user_id: CurrentUserId):
    """Get saved SNP recommendations for current MSE."""
    from src.db.models.snp import SNP

    result = await db.execute(select(MSE).where(MSE.user_id == uuid.UUID(user_id)))
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    result = await db.execute(
        select(MSEMatch, SNP)
        .join(SNP, MSEMatch.snp_id == SNP.id)
        .where(MSEMatch.mse_id == mse.id)
        .order_by(MSEMatch.match_score.desc())
    )
    rows = result.all()

    return [
        {
            "id": str(m.id),
            "snp_id": str(m.snp_id),
            "snp_name": snp.name,
            "match_score": m.match_score,
            "match_reasons": m.match_reasons,
            "category_overlap_score": m.category_overlap_score,
            "geography_score": m.geography_score,
            "status": m.status,
            "avg_onboarding_days": snp.avg_onboarding_days,
        }
        for m, snp in rows
    ]
