from typing import Annotated

from fastapi import APIRouter, Depends
import auth


Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/api/staff", tags=["Staff"])

oauth2_scheme = auth.oauth2_scheme


@router.get("/permission_test")
async def test(permission: Permission):
    return "ok"
