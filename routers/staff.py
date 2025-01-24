from typing import Annotated

from db.postgresql.models.user_account import UserAccountStatus
from dtos.request import product as prod
from fastapi import APIRouter, Depends, File, Request, UploadFile, BackgroundTasks
from dtos.request.blog import BlogCreation
from services import product as ps
from services import blog
from services import customer as c_ss
from etc.progress_tracker import pp
from db.postgresql.models import product

import auth

Permission = Annotated[bool, Depends(auth.staff_permission)]

router = APIRouter(prefix="/api/staff", tags=["Staff function"])

oauth2_scheme = auth.oauth2_scheme


@router.get("/permission_test")
async def test(_permission: Permission):
    return "ok"


@router.post(
    "/product/create",
    tags=["Product"],
)
async def create_product(
    _permission: Permission,
    bg_task: BackgroundTasks,
    req: Request,
    product_detail: prod.ProductCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    bg_id = pp.new()
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    mip = pp.new_subtask(bg_id, "Preloaded main")

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for i, f in enumerate(additional_images):
            img = await f.read()
            additional_images_preload.append(img)
            pp.update_subtask(bg_id, mip, progress=i + 1)

    pp.close_subtask(
        bg_id,
        mip,
    )
    bg_task.add_task(
        ps.product_creation,
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        pp,
        bg_id,
    )

    return {
        "progress_id": bg_id,
    }


@router.post(
    "/mealkit/create",
    tags=["Product"],
)
async def create_mealkit(
    _permission: Permission,
    bg_task: BackgroundTasks,
    req: Request,
    product_detail: prod.MealKitCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
    additional_images: list[Annotated[UploadFile, File(media_type="image")]]
    | None = None,
):
    bg_id = pp.new()
    yolo_model = req.state.ai_models["yolo"]
    clip_model = req.state.ai_models["clip"]

    mip = pp.new_subtask(bg_id, "Preloaded main")

    main_image_preload = await main_image.read()

    additional_images_preload: list[bytes] = []

    if additional_images:
        for i, f in enumerate(additional_images):
            img = await f.read()
            additional_images_preload.append(img)
            pp.update_subtask(bg_id, mip, progress=i + 1)

    pp.close_subtask(
        bg_id,
        mip,
    )

    bg_task.add_task(
        ps.product_creation,
        product_detail,
        additional_images_preload,
        main_image_preload,
        yolo_model,
        clip_model,
        pp,
        bg_id,
    )

    return {
        "progress_id": bg_id,
    }


@router.post(
    "/product/update/info/prod",
    tags=["Product"],
)
async def update_info_prod(
    _: Permission,
    prod_id: str,
    info: prod.ProductUpdate,
):
    ps.update_info(
        prod_id,
        info,
    )


@router.post(
    "/product/update/info/mealkit",
    tags=["Product"],
)
async def update_info_mk(
    _: Permission,
    prod_id: str,
    info: prod.MealKitUpdate,
):
    ps.update_info(
        prod_id,
        info,
    )


@router.patch(
    "/product/update/status",
    tags=["Product"],
)
async def update_status(
    _: Permission,
    prod_id: str,
    status: product.ProductStatus,
):
    ps.update_status(prod_id, status)


@router.patch(
    "/product/update/quantity",
    tags=["Product"],
)
async def update_quantity(
    _: Permission,
    prod_id: str,
    quantity: int,
):
    ps.update_quantity(prod_id, quantity)


@router.put(
    "/product/update/price",
    tags=["Product"],
)
async def update_price(
    _permission: Permission,
    product_id: str,
    price: float,
    sale_percent: float,
):
    ps.update_price(
        product_id,
        price,
        sale_percent,
    )
    return {"message": "Price updated"}


@router.post(
    "/blog/create",
    tags=["Blog"],
)
async def create_blog(
    _: Permission,
    blog_info: BlogCreation,
    main_image: Annotated[UploadFile, File(media_type="image")],
):
    main_image_preload = await main_image.read()

    return blog.create(
        blog_info,
        main_image_preload,
    )


@router.post(
    "/blog/edit",
    tags=["Blog"],
)
async def edit_blog(
    _: Permission,
    id: str,
    blog_info: BlogCreation,
):
    blog.edit(id, blog_info)


@router.get(
    "/comment/fetch",
    tags=["Blog", "Comment"],
)
async def get_blog_comment(
    _: Permission,
    id: str,
):
    return blog.get_comment(id)


@router.get(
    "/blog/fetch/all",
    tags=["Blog"],
)
async def get_blogs(
    _: Permission,
):
    return blog.get_blog_list()


@router.get(
    "/blog/fetch/{id}",
    tags=["Blog"],
)
async def get_blog(
    _: Permission,
    id: str,
):
    return blog.get(id)


@router.get(
    "/customer/fetch/comment",
    tags=["Blog", "Comment", "Customer"],
)
async def get_customer_comment(
    _: Permission,
    id: str,
):
    return blog.get_comment_by_customer(id)


@router.get(
    "/customer/fetch/all",
    tags=["Customer"],
)
async def get_list_customer(
    _: Permission,
):
    return c_ss.get_all_customer()


@router.get(
    "/customer/fetch/id/{id}",
    tags=["Customer"],
)
async def get_customer(
    _: Permission,
    id: str,
):
    return c_ss.get_customer(id)


@router.patch(
    "/customer/edit/status",
    tags=["Customer"],
)
async def change_customer_status(
    _: Permission,
    id: str,
    status: UserAccountStatus,
):
    c_ss.set_account_status(id, status)
