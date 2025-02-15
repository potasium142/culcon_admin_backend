from pydantic import BaseModel
from enum import Enum


class ChatType(str, Enum):
    STAFF = "STAFF"
    AI_CHEFT = "AI_CHEFT"


class ChatRequest(BaseModel):
    type: ChatType
    jwt_token: str
