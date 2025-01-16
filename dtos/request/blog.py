from pydantic import BaseModel, model_validator
from pydantic_core import from_json


class BlogCreation(BaseModel):
    title: str
    description: str
    markdown_text: str
    infos: dict[str, str]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return from_json(value)
        return value
