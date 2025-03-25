from uuid import uuid4

from db.postgresql.models.blog import Blog
from db.postgresql.models.user_account import CommentType, PostComment
from dtos.request.blog import BlogCreation
from etc import cloudinary
from db.postgresql.db_session import db_session
from etc.local_error import HandledError
import sqlalchemy as sqla


from db.postgresql.paging import Page, display_page, paging, table_size


def create(
    blog_dto: BlogCreation,
    thumbnail: bytes,
) -> str:
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

    db_session.session.add(blog)
    db_session.commit()

    return id


def edit(
    id: str,
    blog_dto: BlogCreation,
):
    blog: Blog = db_session.session.get(Blog, id)

    if not blog:
        raise HandledError("Blog not found")

    blog.article = blog_dto.markdown_text
    blog.title = blog_dto.title
    blog.description = blog_dto.description
    blog.infos = blog_dto.infos

    db_session.commit()


def get(id: str):
    return db_session.session.get(Blog, id)


def delete_comment(
    id: str,
):
    comment = db_session.session.get(PostComment, id)

    if not comment:
        raise HandledError("Comment not found")

    comment.deleted = True
    comment.account_id = None

    db_session.commit()

    return db_session.session.get(PostComment, id)


def get_comment(post_id: str, pg: Page):
    with db_session.session as ss:
        content = ss.scalars(
            paging(
                sqla.select(PostComment).filter(
                    PostComment.post_id == post_id,
                    PostComment.comment_type == CommentType.POST,
                ),
                pg,
            )
        ).all()

        count = (
            ss.scalar(
                sqla.select(sqla.func.count(PostComment.id)).filter(
                    PostComment.post_id == post_id,
                    PostComment.comment_type == CommentType.POST,
                )
            )
            or 0
        )
        return display_page(content, count, pg)


def get_blog_list(page: Page):
    with db_session.session as ss:
        blogs = ss.scalars(
            paging(
                sqla.select(Blog),
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
        count = table_size(Blog.id)
        return display_page(content, count, page)


def get_comment_by_customer(user_id: str, page: Page):
    with db_session.session as ss:
        content = ss.scalars(
            paging(
                sqla.select(PostComment).filter(
                    PostComment.account_id == user_id,
                ),
                page,
            )
        ).all()

        count = (
            ss.scalar(
                sqla.select(sqla.func.count(PostComment.id)).filter(
                    PostComment.account_id == user_id,
                )
            )
            or 0
        )
        return display_page(content, count, page)
