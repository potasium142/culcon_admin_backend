from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from ai.clip import OpenCLIP
from db.postgresql.models.blog import Blog, BlogEmbedding
from db.postgresql.models.user_account import (
    CommentStatus,
    CommentType,
    PostComment,
    UserAccount,
)
from dtos.request.blog import BlogCreation
from etc import cloudinary
from etc.local_error import HandledError
import sqlalchemy as sqla


from db.postgresql.paging import Page, display_page, paging, table_size


async def create(
    blog_dto: BlogCreation,
    clip_model: OpenCLIP,
    thumbnail: bytes,
    ss: AsyncSession,
):
    async with ss.begin():
        id = str(uuid4())

        thumbnail_url = cloudinary.upload(thumbnail, "blog", id)

        blog = Blog(
            id=id,
            title=blog_dto.title,
            description=blog_dto.description,
            article=blog_dto.markdown_text,
            infos=blog_dto.infos,
            thumbnail=thumbnail_url,
        )

        embed = clip_model.encode_text(blog_dto.description)[0]

        blog_embed = BlogEmbedding(
            id=id,
            description_embed=embed,
        )

        ss.add(blog)
        ss.add(blog_embed)
        await ss.flush()

        b_rfetch = await ss.get_one(Blog, id)

        return {
            "id": b_rfetch.id,
            "title": b_rfetch.title,
            "description": b_rfetch.description,
            "article": b_rfetch.article,
            "thumbnail": b_rfetch.thumbnail,
            "infos": b_rfetch.infos,
        }


async def edit(
    id: str,
    clip_model: OpenCLIP,
    blog_dto: BlogCreation,
    ss: AsyncSession,
):
    async with ss.begin():
        blog: Blog = await ss.get_one(Blog, id)

        blog.article = blog_dto.markdown_text
        blog.title = blog_dto.title
        blog.description = blog_dto.description
        blog.infos = blog_dto.infos

        blog_embed = await ss.get_one(BlogEmbedding, id)

        embed = clip_model.encode_text(blog_dto.description)[0]

        blog_embed.description_embed = embed

        await ss.flush()

        b_rfetch = await ss.get_one(Blog, id)

        return {
            "id": b_rfetch.id,
            "title": b_rfetch.title,
            "description": b_rfetch.description,
            "article": b_rfetch.article,
            "thumbnail": b_rfetch.thumbnail,
            "infos": b_rfetch.infos,
        }


async def get(id: str, ss: AsyncSession):
    async with ss.begin():
        return await ss.get_one(Blog, id)


async def change_comment_status(
    id: str,
    status: CommentStatus,
    ss: AsyncSession,
):
    async with ss.begin():
        comment = await ss.get_one(PostComment, id)

        comment.status = status

        await ss.flush()

        return await ss.get_one(PostComment, id)


async def get_comment_by_status(
    pg: Page,
    ss: AsyncSession,
    id: str,
    status: CommentStatus | None = None,
    type: CommentType | None = None,
    user_id: str | None = None,
):
    async with ss.begin():
        filters = [PostComment.post_id == id]

        if user_id:
            filters.append(PostComment.account_id == user_id)
        if type:
            filters.append(PostComment.comment_type == type)
        if status:
            filters.append(PostComment.status == status)

        r = await ss.scalars(
            paging(
                sqla.select(PostComment)
                .filter(*filters)
                .order_by(PostComment.timestamp.desc()),
                pg,
            )
        )
        content = r.all()

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(PostComment.id)).filter(*filters)
            )
            or 0
        )
        return display_page(content, count, pg)


async def get_reply(
    pg: Page,
    ss: AsyncSession,
    cmt_id: str,
    blog_id: str,
    status: CommentStatus | None = None,
):
    async with ss.begin():
        filter = [
            PostComment.post_id == blog_id,
            PostComment.parent_comment == cmt_id,
        ]
        if status:
            filter.append(PostComment.status == status)

        replies = await ss.scalars(
            paging(
                sqla.select(PostComment).filter(*filter),
                pg,
            )
        )

        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(PostComment.id)).filter(*filter)
            )
            or 0
        )

        return display_page(replies.all(), count, pg)


async def get_blog_list(page: Page, ss: AsyncSession, title: str = ""):
    async with ss.begin():
        blogs = await ss.scalars(
            paging(
                sqla.select(Blog).filter(Blog.title.ilike(f"%{title}%")),
                page,
            )
        )
        content = [
            {
                "id": b.id,
                "title": b.title,
                "description": b.description,
            }
            for b in blogs
        ]
        count = (
            await ss.scalar(
                sqla.select(sqla.func.count(Blog.id)).filter(
                    Blog.title.ilike(f"%{title}%")
                )
            )
            or 0
        )
        return display_page(content, count, page)
