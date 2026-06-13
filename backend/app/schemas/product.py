"""商品列表 schema"""

from pydantic import BaseModel
from typing import List
from decimal import Decimal


class ProductItem(BaseModel):
    code: str
    name: str
    price: Decimal
    points: int
    valid_days: int  # 0=永久
    description: str


class ProductListResp(BaseModel):
    items: List[ProductItem]
