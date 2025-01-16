from pydantic import BaseModel, ConfigDict, Field


class MealkitDoc(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    infos: dict[str, str]
    images_url: list[str]
    article_md: str
    instructions: list[str]
    ingredients: list[str]
    day_before_expiry: int
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
