from typing import Annotated

from fastapi import APIRouter, Depends
import auth


router = APIRouter(
    prefix="/api/staff",
    tags=["Staff"]
)

oauth2_scheme = auth.oauth2_scheme


@router.get("/permission_test")
async def test(token: Annotated[str, Depends(oauth2_scheme)]):
    return "ok"
