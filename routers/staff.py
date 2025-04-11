from datetime import date, time
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from db.postgresql.db_session import get_session
from db.postgresql.models.order_history import OrderStatus
from db.postgresql.models.user_account import (
    CommentStatus,
    CommentType,
    UserAccountStatus,
)
from dtos.request import product as prod
from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from dtos.request.blog import BlogCreation
from dtos.request.user_account import EditCustomerAccount, EditCustomerInfo
from services import product as ps, product_, shipper
from services import blog
from services import customer as c_ss
from services import order as ord_ss
from db.postgresql.models import product
from db.postgresql.paging import page_param, Page
import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/api/staff", tags=["Staff function"])

oauth2_scheme = auth.oauth2_scheme

Paging = Annotated[Page, Depends(page_param)]

Session = Annotated[AsyncSession, Depends(get_session)]

Id = Annotated[str, Depends(auth.staff_id)]


@router.get("/permission_test")
async def test(_permission: Permission):
    return "ok"


@router.post(
    "/product/create",
    tags=["Product"],
    response_model=None,
)
async def create_product(
    _: Permission,
    req: Request,
    bg_task: BackgroundTasks,
    product_detail: prod.ProductCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    ss: Session,
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for f in additional_images:
            img = await f.read()
            additional_images_preload.append(img)

    return await product_.product_creation(
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        ss,
        bg_task,
    )


@router.post(
    "/mealkit/create",
    tags=["Product"],
)
async def create_mealkit(
    _: Permission,
    req: Request,
    bg_task: BackgroundTasks,
    product_detail: prod.MealKitCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    ss: Session,
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for f in additional_images:
            img = await f.read()
            additional_images_preload.append(img)

    return await product_.product_creation(
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        ss,
        bg_task,
    )


@router.get("/mealkit/create/fetch/ingredients", tags=["Product"])
async def fetch_ingredients(
    _: Permission,
    ss: Session,
    pg: Paging,
    search: str = "",
):
    return await product_.get_ingredients_list(search, pg, ss)


@router.post(
    "/product/update/info/prod",
    tags=["Product"],
)
async def update_info_prod(
    _: Permission,
    req: Request,
    prod_id: str,
    info: prod.ProductUpdate,
    ss: Session,
):
    clip_model = req.state.ai_models["clip"]
    return await ps.update_info(
        prod_id,
        info,
        clip_model,
        ss,
    )


@router.post(
    "/product/update/info/mealkit",
    tags=["Product"],
)
async def update_info_mk(
    _: Permission,
    req: Request,
    prod_id: str,
    info: prod.MealKitUpdate,
    ss: Session,
):
    clip_model = req.state.ai_models["clip"]
    return await ps.update_info(
        prod_id,
        info,
        clip_model,
        ss,
    )


@router.patch(
    "/product/update/status",
    tags=["Product"],
)
async def update_status(
    _: Permission,
    prod_id: str,
    status: product.ProductStatus,
    ss: Session,
):
    return await ps.update_status(prod_id, status, ss)


@router.patch(
    "/product/update/quantity",
    tags=["Product"],
)
async def update_quantity(
    _: Permission,
    prod_id: str,
    quantity: int,
    in_price: float,
    ss: Session,
):
    return await ps.restock_product(prod_id, quantity, in_price, ss)


@router.put(
    "/product/update/price",
    tags=["Product"],
)
async def update_price(
    _: Permission,
    product_id: str,
    price: float,
    sale_percent: float,
    ss: Session,
):
    return await ps.update_price(product_id, price, sale_percent, ss)


@router.post(
    "/blog/create",
    tags=["Blog"],
)
async def create_blog(
    _: Permission,
    req: Request,
    blog_info: BlogCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    ss: Session,
):
    clip_model = req.state.ai_models["clip"]
    main_image_preload = await main_image.read()

    return await blog.create(
        blog_info,
        clip_model,
        main_image_preload,
        ss,
    )


@router.post(
    "/blog/edit",
    tags=["Blog"],
)
async def edit_blog(
    _: Permission,
    req: Request,
    id: str,
    blog_info: BlogCreation,
    ss: Session,
):
    clip_model = req.state.ai_models["clip"]
    return await blog.edit(id, clip_model, blog_info, ss)


@router.get(
    "/comment/fetch/all",
    tags=["Blog", "Comment"],
)
async def get_all_comment(
    _: Permission,
    pg: Paging,
    ss: Session,
    status: CommentStatus | None = None,
    type: CommentType | None = None,
):
    return await blog.get_comment_by_status(pg, ss, status, type)


@router.get(
    "/comment/fetch",
    tags=["Blog", "Comment"],
)
async def get_blog_comment(
    _: Permission,
    id: str,
    pg: Paging,
    ss: Session,
):
    return await blog.get_comment(id, pg, ss)


@router.delete(
    "/comment/delete",
    tags=["Blog", "Comment"],
)
async def delete_comment(
    _: Permission,
    id: str,
    ss: Session,
):
    return await blog.change_comment_status(id, CommentStatus.DELETED, ss)


@router.patch(
    "/comment/report/unflag",
    tags=["Blog", "Comment"],
)
async def unflag_comment(
    _: Permission,
    id: str,
    ss: Session,
):
    return await blog.change_comment_status(id, CommentStatus.NORMAL, ss)


@router.get(
    "/comment/report/fetch/{id}",
    tags=["Blog", "Comment"],
)
async def get_blog_report_cmt(
    _: Permission,
    id: str,
    pg: Paging,
    ss: Session,
):
    return await blog.get_reported_comment_of_blog(id, pg, ss)


@router.get(
    "/blog/fetch/all",
    tags=["Blog"],
)
async def get_blogs(
    _: Permission,
    pg: Paging,
    ss: Session,
    title: str = "",
):
    return await blog.get_blog_list(pg, ss, title)


@router.get(
    "/blog/fetch/{id}",
    tags=["Blog"],
)
async def get_blog(
    _: Permission,
    id: str,
    ss: Session,
):
    return await blog.get(id, ss)


@router.get(
    "/customer/fetch/comment",
    tags=["Blog", "Comment", "Customer"],
)
async def get_customer_comment(
    _: Permission,
    id: str,
    pg: Paging,
    ss: Session,
):
    return await blog.get_comment_by_customer(id, pg, ss)


@router.get(
    "/customer/fetch/all",
    tags=["Customer"],
)
async def get_list_customer(
    _: Permission,
    pg: Paging,
    ss: Session,
    id: str = "",
):
    return await c_ss.get_all_customer(pg, ss, id)


@router.get(
    "/customer/fetch/cart/{id}",
    tags=["Customer"],
)
async def get_customer_cart(
    _: Permission,
    pg: Paging,
    id: str,
    ss: Session,
):
    return await c_ss.get_customer_cart(id, pg, ss)


@router.get(
    "/customer/fetch/id/{id}",
    tags=["Customer"],
)
async def get_customer(
    _: Permission,
    id: str,
    ss: Session,
):
    return await c_ss.get_customer(id, ss)


@router.get(
    "/customer/fetch/order/{id}",
    tags=["Customer"],
)
async def get_customer_order(
    _: Permission,
    id: str,
    ss: Session,
    pg: Paging,
):
    return await c_ss.get_customer_order_history(id, ss, pg)


@router.patch(
    "/customer/edit/status",
    tags=["Customer"],
)
async def change_customer_status(
    _: Permission,
    id: str,
    status: UserAccountStatus,
    ss: Session,
):
    return await c_ss.set_account_status(id, status, ss)


@router.patch(
    "/customer/edit/account",
    tags=["Customer"],
)
async def change_customer_account(
    _: Permission,
    id: str,
    info: EditCustomerAccount,
    ss: Session,
):
    return await c_ss.edit_customer_account(id, info, ss)


@router.patch(
    "/customer/edit/info",
    tags=["Customer"],
)
async def change_customer_info(
    _: Permission,
    id: str,
    info: EditCustomerInfo,
    ss: Session,
):
    return await c_ss.edit_customer_info(id, info, ss)


@router.get("/product/history/stock", tags=["Product"])
async def fetch_product_stock_history(
    _: Permission,
    prod_id: str,
    pg: Paging,
    ss: Session,
):
    return await ps.get_product_stock_history(prod_id, pg, ss)


@router.get("/product/history/price", tags=["Product"])
async def fetch_product_price_history(
    _: Permission,
    prod_id: str,
    pg: Paging,
    ss: Session,
):
    return await ps.get_product_price_history(prod_id, pg, ss)


@router.get(
    "/order/fetch/all",
    tags=["Order"],
)
async def get_all_orders(
    _: Permission,
    pg: Paging,
    ss: Session,
    id: str = "",
    status: OrderStatus | None = None,
):
    return await ord_ss.get_all_orders(pg, ss, id, status)


@router.get(
    "/order/fetch/status",
    tags=["Order"],
)
async def get_order_by_status(
    _: Permission,
    status: OrderStatus,
    pg: Paging,
    ss: Session,
):
    return await ord_ss.get_orders_with_status(status, pg, ss)


@router.get(
    "/order/fetch/{id}",
    tags=["Order"],
)
async def get_order(
    _: Permission,
    id: str,
    ss: Session,
):
    return await ord_ss.get_order_detail(id, ss)


@router.get(
    "/order/fetch/{id}/items",
    tags=["Order"],
)
async def get_order_items(
    _: Permission,
    id: str,
    pg: Paging,
    ss: Session,
):
    return await ord_ss.get_order_items(id, pg, ss)


@router.post(
    "/order/accept/{id}",
    tags=["Order"],
)
async def accept_order(
    _: Permission,
    id: str,
    ss: Session,
    self_id: Id,
):
    return await ord_ss.accept_order(id, ss, self_id)


@router.post(
    "/order/ship/{id}",
    tags=["Order"],
)
async def ship_order(
    _: Permission,
    id: str,
    ss: Session,
):
    return await ord_ss.change_order_status(
        id,
        ss,
        OrderStatus.ON_PROCESSING,
        OrderStatus.ON_SHIPPING,
    )


@router.post(
    "/order/cancel/{id}",
    tags=["Order"],
)
async def cancel_order(
    _: Permission,
    id: str,
    ss: Session,
):
    return await ord_ss.cancel_order(id, ss)


@router.get("/shipper/non_shift", tags=["Shipper"])
async def fetch_non_shift(
    _: Permission,
    ss: Session,
    pg: Paging,
):
    return await shipper.fetch_non_assign_shifttime(
        ss,
        pg,
    )


@router.get("/shipper/fetch", tags=["Shipper"])
async def fetch_shipper(
    _: Permission,
    ss: Session,
    pg: Paging,
    occupied: bool | None = None,
    start_shift: time | None = None,
    end_shift: time | None = None,
):
    return await shipper.fetch_shipper(
        ss,
        pg,
        occupied,
        start_shift,
        end_shift,
    )


@router.get(
    "/shipment/fetch",
    tags=["Order", "Shipper"],
)
async def fetch_order(
    _: Permission,
    pg: Paging,
    ss: Session,
    shipper_id: str,
    staff_id: str,
    start_date_confirm: date | None = None,
    end_date_confirm: date | None = None,
    start_date_shipping: date | None = None,
    end_date_shipping: date | None = None,
):
    return await shipper.fetch_shippment_from_range(
        pg,
        ss,
        start_date_confirm,
        end_date_confirm,
        start_date_shipping,
        end_date_shipping,
        shipper_id,
        staff_id,
    )


@router.put("/shipper/assign", tags=["Shipper"])
async def assign_shipper(
    _: Permission,
    ss: Session,
    bg_task: BackgroundTasks,
    order_id: str,
    shipper_id: str,
):
    return await shipper.assign_shipper(order_id, shipper_id, ss, bg_task)
