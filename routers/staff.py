from typing import Annotated

from dtos.request import product as prod

from fastapi import APIRouter, Depends, File, UploadFile
import auth


Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/api/staff", tags=["Staff"])

oauth2_scheme = auth.oauth2_scheme


@router.get("/permission_test")
async def test(permission: Permission):
    return "ok"


@router.post("/product/create")
async def create_product(
    form: prod.ProductCreation,
    main_images: Annotated[UploadFile, File(media_type="image")],
    additional_images: None
    | Annotated[list[UploadFile], File(media_type="image")] = None,
):
    pass
