"""SNP portal routes."""

import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from src.api.dependencies import DBSession, CurrentUserId
from src.db.models.snp import SNP
from src.db.models.mse_match import MSEMatch, MatchStatus
from src.db.models.mse import MSE
from src.db.models.product import Product

router = APIRouter(prefix="/snp", tags=["snp"])


@router.get("/profile")
async def get_snp_profile(db: DBSession, user_id: CurrentUserId):
    """Get SNP profile for the logged-in SNP user."""
    from src.db.models.user import User
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.role != "snp":
        raise HTTPException(status_code=403, detail="SNP access only")

    result = await db.execute(select(SNP).limit(1))
    snp = result.scalar_one_or_none()
    if not snp:
        return {"message": "SNP profile not set up yet"}

    return {
        "id": str(snp.id),
        "name": snp.name,
        "supported_categories": snp.supported_categories,
        "b2b": snp.b2b,
        "b2c": snp.b2c,
        "avg_onboarding_days": snp.avg_onboarding_days,
    }


@router.get("/leads")
async def get_leads(db: DBSession, user_id: CurrentUserId):
    """Get AI-matched MSE leads for this SNP."""
    result = await db.execute(
        select(MSEMatch)
        .where(MSEMatch.status == MatchStatus.SUGGESTED.value)
        .order_by(MSEMatch.match_score.desc())
        .limit(20)
    )
    matches = result.scalars().all()

    leads = []
    for match in matches:
        mse_result = await db.execute(select(MSE).where(MSE.id == match.mse_id))
        mse = mse_result.scalar_one_or_none()
        if mse:
            leads.append({
                "match_id": str(match.id),
                "mse_id": str(mse.id),
                "business_name": mse.business_name,
                "state": mse.state,
                "onboarding_status": mse.onboarding_status,
                "match_score": match.match_score,
                "match_reasons": match.match_reasons,
            })
    return leads


@router.put("/leads/{mse_id}/accept")
async def accept_lead(mse_id: str, db: DBSession, user_id: CurrentUserId):
    """Accept an MSE lead."""
    result = await db.execute(
        select(MSEMatch).where(MSEMatch.mse_id == uuid.UUID(mse_id))
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = MatchStatus.SELECTED.value
    await db.flush()
    return {"success": True}


@router.put("/leads/{mse_id}/reject")
async def reject_lead(mse_id: str, db: DBSession, user_id: CurrentUserId, reason: str = ""):
    """Reject an MSE lead."""
    result = await db.execute(
        select(MSEMatch).where(MSEMatch.mse_id == uuid.UUID(mse_id))
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = MatchStatus.REJECTED.value
    await db.flush()
    return {"success": True}
