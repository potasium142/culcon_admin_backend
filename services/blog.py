from uuid import uuid4
from db.postgresql.models.blog import Blog
from db.postgresql.models.user_account import PostComment
from dtos.request.blog import BlogCreation
from etc import cloudinary
from db.postgresql.db_session import db_session
from etc.local_error import HandledError


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


def get_comment(post_id: str):
    return (
        db_session.session.query(PostComment)
        .filter_by(
            post_id=post_id,
            comment_type="POST",
        )
        .all()
    )


def get_blog_list() -> list[dict[str, str]]:
    blogs = db_session.session.query(Blog).all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "description": b.description,
        }
        for b in blogs
    ]


def get_comment_by_customer(user_id: str):
    return (
        db_session.session.query(PostComment)
        .filter_by(
            account_id=user_id,
        )
        .all()
    )
