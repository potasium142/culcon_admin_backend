from dataclasses import dataclass
from pydantic import BaseModel
from db.postgresql.models import product as p


@dataclass
class ProductCreation(BaseModel):
    product_name: str
    available_quantity: int
    product_type: p.ProductType
    price: float
    sale_percent: float = 0.0
