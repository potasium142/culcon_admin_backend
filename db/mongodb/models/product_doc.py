from pydantic import BaseModel, ConfigDict, Field
from db.postgresql.models.product import ProductType


class ProductDoc(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    infos: dict[str, str]
    images_url: list[str]
    article_md: str
    type: ProductType
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
