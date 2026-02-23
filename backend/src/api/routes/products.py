"""Product catalogue routes."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from src.api.dependencies import DBSession, CurrentUserId
from src.core.logging import log
from src.db.models.product import Product, ProductStatus
from src.db.models.mse import MSE, OnboardingStatus

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    raw_description: str
    source: str = "web"


class ProductUpdate(BaseModel):
    product_name: str | None = None
    ondc_category_code: str | None = None
    subcategory: str | None = None
    attributes: dict | None = None
    status: str | None = None


async def _get_mse(user_id: str, db) -> MSE:
    """Helper to get MSE for current user."""
    result = await db.execute(select(MSE).where(MSE.user_id == uuid.UUID(user_id)))
    mse = result.scalar_one_or_none()
    if not mse:
        raise HTTPException(status_code=404, detail="MSE profile not found")
    return mse


@router.post("/")
async def add_product(req: ProductCreate, db: DBSession, user_id: CurrentUserId):
    """Add a new product — triggers AI cataloguing."""
    mse = await _get_mse(user_id, db)

    product = Product(
        id=uuid.uuid4(),
        mse_id=mse.id,
        raw_description=req.raw_description,
        source=req.source,
        status=ProductStatus.DRAFT.value,
        attributes={},
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)

    try:
        from src.tools.core.classify_product import ClassifyProductTool
        from src.tools.core.extract_attributes import ExtractAttributesTool
        from src.tools.core.validate_catalogue import ValidateCatalogueTool

        classify_tool = ClassifyProductTool()
        extract_tool = ExtractAttributesTool()
        validate_tool = ValidateCatalogueTool()

        classify_result = await classify_tool.execute(
            {"description": req.raw_description}, {}
        )
        category_code = classify_result.get("category_code", "ONDC:RET16")
        subcategory = classify_result.get("subcategory", "General")

        extract_result = await extract_tool.execute(
            {"description": req.raw_description, "category_code": category_code}, {}
        )
        attributes = extract_result.get("attributes", {})
        missing_fields = extract_result.get("missing_fields", [])

        validate_result = await validate_tool.execute(
            {"attributes": attributes, "category_code": category_code}, {}
        )
        compliance_score = validate_result.get("compliance_score", 0.0)

        product.product_name = attributes.get("product_name") or req.raw_description[:50]
        product.ondc_category_code = category_code
        product.subcategory = subcategory
        product.attributes = attributes
        product.compliance_score = compliance_score
        product.missing_fields = missing_fields

        if compliance_score == 100:
            product.status = ProductStatus.READY.value

        await db.flush()

    except Exception as e:
        log.error(f"AI cataloguing failed for product {product.id}: {e}")

    return {
        "id": str(product.id),
        "product_name": product.product_name,
        "ondc_category_code": product.ondc_category_code,
        "subcategory": product.subcategory,
        "attributes": product.attributes,
        "compliance_score": product.compliance_score,
        "missing_fields": product.missing_fields,
        "status": product.status,
    }


@router.get("/")
async def list_products(db: DBSession, user_id: CurrentUserId):
    """List all products for the current MSE."""
    mse = await _get_mse(user_id, db)

    result = await db.execute(
        select(Product).where(Product.mse_id == mse.id).order_by(Product.created_at.desc())
    )
    products = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "product_name": p.product_name,
            "raw_description": p.raw_description,
            "ondc_category_code": p.ondc_category_code,
            "subcategory": p.subcategory,
            "attributes": p.attributes,
            "compliance_score": p.compliance_score,
            "missing_fields": p.missing_fields,
            "status": p.status,
            "source": p.source,
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]


@router.put("/{product_id}")
async def update_product(
    product_id: str, req: ProductUpdate, db: DBSession, user_id: CurrentUserId
):
    """Update a product."""
    mse = await _get_mse(user_id, db)

    result = await db.execute(
        select(Product).where(
            Product.id == uuid.UUID(product_id),
            Product.mse_id == mse.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in req.model_dump(exclude_none=True).items():
        if field == "attributes" and value:
            product.attributes = {**(product.attributes or {}), **value}
        else:
            setattr(product, field, value)

    if req.attributes or req.ondc_category_code:
        from src.tools.core.validate_catalogue import ValidateCatalogueTool
        validate_tool = ValidateCatalogueTool()
        validate_result = await validate_tool.execute(
            {
                "attributes": product.attributes,
                "category_code": product.ondc_category_code or "ONDC:RET16",
            },
            {},
        )
        product.compliance_score = validate_result.get("compliance_score", 0.0)
        product.missing_fields = validate_result.get("missing_fields", [])
        if product.compliance_score == 100:
            product.status = ProductStatus.READY.value

    await db.flush()
    return {"success": True, "compliance_score": product.compliance_score}


@router.delete("/{product_id}")
async def delete_product(product_id: str, db: DBSession, user_id: CurrentUserId):
    """Delete a product."""
    mse = await _get_mse(user_id, db)

    result = await db.execute(
        select(Product).where(
            Product.id == uuid.UUID(product_id),
            Product.mse_id == mse.id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    return {"success": True}


@router.get("/catalogue-status")
async def catalogue_status(db: DBSession, user_id: CurrentUserId):
    """Get overall catalogue readiness for this MSE."""
    mse = await _get_mse(user_id, db)

    result = await db.execute(
        select(Product).where(Product.mse_id == mse.id)
    )
    products = result.scalars().all()

    if not products:
        return {
            "total_products": 0,
            "ready_products": 0,
            "draft_products": 0,
            "avg_compliance_score": 0,
            "catalogue_ready": False,
        }

    ready = [p for p in products if p.status == ProductStatus.READY.value]
    avg_score = sum(p.compliance_score or 0 for p in products) / len(products)
    catalogue_ready = len(ready) >= 1

    if catalogue_ready and mse.onboarding_status == "profile_complete":
        mse.onboarding_status = OnboardingStatus.CATALOGUE_READY.value
        await db.flush()

    return {
        "total_products": len(products),
        "ready_products": len(ready),
        "draft_products": len(products) - len(ready),
        "avg_compliance_score": round(avg_score, 1),
        "catalogue_ready": catalogue_ready,
    }
