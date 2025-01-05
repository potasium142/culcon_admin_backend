from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field
from db.postgresql.models.product import ProductType


@dataclass
class MealkitDoc(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    infos: dict[str, str]
    tags: list[str]
    images_url: list[str]
    price: float
    sale_percent: float
    day_before_expiry: int
    article_md: str
    type: ProductType
    instructions: list[str]
    ingredients: list[str]
    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True
    )
