from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field


class BlogDoc(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: str
    markdown_text: str
    infos: dict[str, str]
    thumbnail_url: str
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
