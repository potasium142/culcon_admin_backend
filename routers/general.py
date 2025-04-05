from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from db.postgresql.db_session import get_session
from db.postgresql.models.product import ProductType
from etc.local_error import HandledError
from etc.prog_tracker import ProgressTrackerManager, get_prog_tracker
from services import product as ps
from services import coupon as coupon_service
from fastapi.responses import StreamingResponse
import auth


from fastapi import APIRouter, Depends
from db.postgresql.paging import page_param, Page

Paging = Annotated[Page, Depends(page_param)]
Session = Annotated[AsyncSession, Depends(get_session)]
ProgTracker = Annotated[dict[str, ProgressTrackerManager], Depends(get_prog_tracker)]
router = APIRouter(prefix="/api/general", tags=["General"])

oauth2_scheme = auth.oauth2_scheme


@router.get(
    "/product/fetch",
    tags=["Product"],
)
async def get_product(
    prod_id: str,
    session: Session,
):
    return await ps.get_product(prod_id, session)


@router.get(
    "/product/fetch/ingredients",
    tags=["Product"],
)
async def get_ingredients(
    prod_id: str,
    session: Session,
    pg: Paging,
):
    return await ps.get_ingredients(prod_id, session, pg)


@router.get("/product/fetch_all", tags=["Product"])
async def get_all_product(
    pg: Paging,
    session: Session,
    type: ProductType | None = None,
):
    return await ps.get_list_product(pg, session, type)


@router.get("/progress/get")
async def get_progress(prog_id: str, ptm: ProgTracker):
    if prog_id not in ptm:
        raise HandledError("Progress is already complete or not exist")
    return StreamingResponse(
        ptm[prog_id].stream(),
        media_type="text/event-stream",
    )


@router.get("/coupon/fetch", tags=["Coupon"])
async def get_coupon(
    id: str,
    ss: Session,
):
    return await coupon_service.get_coupon(id, ss)


@router.get("/coupon/fetch/all", tags=["Coupon"])
async def get_all_coupon(
    pg: Paging,
    ss: Session,
):
    return await coupon_service.get_all_coupons(pg, ss)
