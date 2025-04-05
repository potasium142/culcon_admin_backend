from pydantic import BaseModel, Field, model_validator
from pydantic_core import from_json
from db.postgresql.models import product as p


class ProductCreation(BaseModel):
    product_name: str
    product_type: p.ProductType
    day_before_expiry: int
    description: str
    article_md: str
    instructions: list[str]
    infos: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class MealKitCreation(ProductCreation):
    ingredients: dict[str, int]
    product_type: p.ProductType = Field(
        exclude=True,
        default=p.ProductType.MEALKIT,
    )

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class ProductUpdate(BaseModel):
    day_before_expiry: int
    description: str
    article_md: str
    instructions: list[str]
    infos: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class MealKitUpdate(ProductUpdate):
    ingredients: dict[str, int]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class ProductRestock(BaseModel):
    product_id: str
    restock_amount: int
    restock_price: float
