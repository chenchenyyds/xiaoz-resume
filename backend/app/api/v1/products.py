"""商品 API - 1 个"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import order_service
from app.schemas.product import ProductListResp, ProductItem

router = APIRouter(prefix="/products", tags=["商品"])


@router.get("", summary="商品列表", response_model=ProductListResp)
async def list_products(db: Session = Depends(get_db)):
    items = order_service.get_product_list(db)
    return ProductListResp(items=[ProductItem(**i) for i in items])
