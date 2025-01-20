from fastapi import APIRouter
from services import product as ps
from services import coupon as coupon_service
from fastapi.responses import StreamingResponse
from etc.progress_tracker import pp

import auth


router = APIRouter(prefix="/api/general", tags=["General"])

oauth2_scheme = auth.oauth2_scheme


@router.get(
    "/product/fetch",
    tags=["Product"],
)
async def get_product(prod_id: str):
    return ps.get_product(prod_id)


@router.get("/product/fetch_all", tags=["Product"])
async def get_all_product():
    return ps.get_list_product()


@router.get("/progress/get")
async def get_progress(prog_id: int):
    return StreamingResponse(
        pp.get(prog_id),
        media_type="text/event-stream",
    )


@router.get("/coupon/fetch", tags=["Coupon"])
async def get_coupon(id: str):
    return coupon_service.get_coupon(id)


@router.get("/coupon/fetch/all", tags=["Coupon"])
async def get_all_coupon():
    return coupon_service.get_all_coupons()
