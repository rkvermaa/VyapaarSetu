"""NSIC Admin portal routes."""

import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from src.api.dependencies import DBSession, CurrentUserId
from src.db.models.mse import MSE, OnboardingStatus
from src.db.models.product import Product
from src.db.models.mse_match import MSEMatch

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(db: DBSession, user_id: CurrentUserId):
    """Get dashboard statistics."""
    statuses = [
        "registered", "profile_complete", "catalogue_ready",
        "snp_selected", "submitted", "under_review", "live"
    ]

    counts = {}
    for status in statuses:
        result = await db.execute(
            select(func.count(MSE.id)).where(MSE.onboarding_status == status)
        )
        counts[status] = result.scalar() or 0

    total_result = await db.execute(select(func.count(MSE.id)))
    total = total_result.scalar() or 0

    product_result = await db.execute(select(func.count(Product.id)))
    total_products = product_result.scalar() or 0

    return {
        "total_mses": total,
        "total_products": total_products,
        "status_breakdown": counts,
        "live_count": counts.get("live", 0),
        "pipeline_count": total - counts.get("live", 0),
    }


@router.get("/queue")
async def get_verification_queue(db: DBSession, user_id: CurrentUserId):
    """Get MSEs pending verification."""
    result = await db.execute(
        select(MSE)
        .where(MSE.onboarding_status.in_(["catalogue_ready", "snp_selected", "submitted"]))
        .order_by(MSE.updated_at.desc())
        .limit(50)
    )
    mses = result.scalars().all()

    queue = []
    for mse in mses:
        prod_result = await db.execute(
            select(func.count(Product.id)).where(Product.mse_id == mse.id)
        )
        product_count = prod_result.scalar() or 0

        queue.append({
            "mse_id": str(mse.id),
            "business_name": mse.business_name,
            "state": mse.state,
            "onboarding_status": mse.onboarding_status,
            "product_count": product_count,
            "udyam_number": mse.udyam_number,
            "created_at": mse.created_at.isoformat(),
        })

    return queue


@router.put("/verify/{mse_id}")
async def verify_mse(mse_id: str, action: str, db: DBSession, user_id: CurrentUserId):
    """Approve or reject an MSE application."""
    result = await db.execute(select(MSE).where(MSE.id == uuid.UUID(mse_id)))
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE not found")

    if action == "approve":
        mse.onboarding_status = OnboardingStatus.LIVE.value
    elif action == "reject":
        mse.onboarding_status = OnboardingStatus.REGISTERED.value
    else:
        raise HTTPException(status_code=400, detail="action must be approve or reject")

    await db.flush()
    return {"success": True, "new_status": mse.onboarding_status}
