"""MSE profile routes."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.api.dependencies import DBSession, CurrentUserId
from src.core.logging import log
from src.db.models.mse import MSE, OnboardingStatus
from src.db.models.user import User

router = APIRouter(prefix="/mse", tags=["mse"])


class MSEProfileUpdate(BaseModel):
    business_name: str | None = None
    owner_name: str | None = None
    nic_code: str | None = None
    major_activity: str | None = None
    state: str | None = None
    district: str | None = None
    address: str | None = None
    turnover: float | None = None
    employee_count: int | None = None
    transaction_type: str | None = None
    target_states: list[str] | None = None
    whatsapp_number: str | None = None


@router.get("/profile")
async def get_profile(db: DBSession, user_id: CurrentUserId):
    """Get MSE business profile."""
    result = await db.execute(
        select(MSE).where(MSE.user_id == uuid.UUID(user_id))
    )
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    return {
        "id": str(mse.id),
        "udyam_number": mse.udyam_number,
        "business_name": mse.business_name,
        "owner_name": mse.owner_name,
        "nic_code": mse.nic_code,
        "major_activity": mse.major_activity,
        "state": mse.state,
        "district": mse.district,
        "address": mse.address,
        "turnover": mse.turnover,
        "employee_count": mse.employee_count,
        "transaction_type": mse.transaction_type,
        "target_states": mse.target_states,
        "whatsapp_number": mse.whatsapp_number,
        "onboarding_status": mse.onboarding_status,
        "selected_snp_id": str(mse.selected_snp_id) if mse.selected_snp_id else None,
    }


@router.put("/profile")
async def update_profile(req: MSEProfileUpdate, db: DBSession, user_id: CurrentUserId):
    """Update MSE business profile."""
    result = await db.execute(
        select(MSE).where(MSE.user_id == uuid.UUID(user_id))
    )
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(mse, field, value)

    # Auto-advance onboarding status
    if mse.onboarding_status == OnboardingStatus.REGISTERED.value:
        if all([mse.business_name, mse.state, mse.transaction_type]):
            mse.onboarding_status = OnboardingStatus.PROFILE_COMPLETE.value

    await db.flush()
    log.info(f"Updated MSE profile: {mse.id}")
    return {"success": True, "onboarding_status": mse.onboarding_status}


@router.get("/status")
async def get_status(db: DBSession, user_id: CurrentUserId):
    """Get MSE onboarding status with timeline."""
    result = await db.execute(
        select(MSE).where(MSE.user_id == uuid.UUID(user_id))
    )
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    status_steps = [
        {"step": "registered", "label": "Registered", "completed": True},
        {"step": "profile_complete", "label": "Profile Complete",
         "completed": mse.onboarding_status not in ["registered"]},
        {"step": "catalogue_ready", "label": "Catalogue Ready",
         "completed": mse.onboarding_status in ["catalogue_ready", "snp_selected", "submitted", "under_review", "live"]},
        {"step": "snp_selected", "label": "SNP Selected",
         "completed": mse.onboarding_status in ["snp_selected", "submitted", "under_review", "live"]},
        {"step": "submitted", "label": "Application Submitted",
         "completed": mse.onboarding_status in ["submitted", "under_review", "live"]},
        {"step": "under_review", "label": "Under Review",
         "completed": mse.onboarding_status in ["under_review", "live"]},
        {"step": "live", "label": "Live on ONDC",
         "completed": mse.onboarding_status == "live"},
    ]

    return {
        "onboarding_status": mse.onboarding_status,
        "steps": status_steps,
        "mse_id": str(mse.id),
    }


@router.put("/select-snp")
async def select_snp(snp_id: str, db: DBSession, user_id: CurrentUserId):
    """Select an SNP from recommendations."""
    result = await db.execute(
        select(MSE).where(MSE.user_id == uuid.UUID(user_id))
    )
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")

    mse.selected_snp_id = uuid.UUID(snp_id)
    mse.onboarding_status = OnboardingStatus.SNP_SELECTED.value

    await db.flush()
    log.info(f"MSE {mse.id} selected SNP {snp_id}")
    return {"success": True, "message": "SNP selected successfully"}
