from pydantic import BaseModel, model_validator
from pydantic_core import from_json
from db.postgresql.models import product as p


class ProductCreation(BaseModel):
    product_name: str
    available_quantity: int
    product_type: p.ProductType
    price: float
    sale_percent: float
    day_before_expiry: int
    description: str
    article_md: str
    infos: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class MealKitCreation(ProductCreation):
    instructions: list[str]
    ingredients: list[str]

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
    infos: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value


class MealKitUpdate(ProductUpdate):
    instructions: list[str]
    ingredients: list[str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value
