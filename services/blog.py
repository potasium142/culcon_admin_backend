from uuid import uuid4
from db.mongodb.models.blog_doc import BlogDoc
from db.postgresql.models.user_account import PostComment
from dtos.request.blog import BlogCreation
from etc import cloudinary
from db.mongodb import db as mongo_session
from db.postgresql.db_session import db_session


def create(
    blog_dto: BlogCreation,
    thumbnail: bytes,
) -> str:
    id = str(uuid4())

    thumbnail_url = cloudinary.upload(thumbnail, "blog", id)

    blog = BlogDoc(
        _id=id,
        title=blog_dto.title,
        description=blog_dto.description,
        markdown_text=blog_dto.markdown_text,
        infos=blog_dto.infos,
        thumbnail_url=thumbnail_url,
    )

    mongo_session["Blog"].insert_one(
        blog.model_dump(
            by_alias=True,
        )
    )
    return id


def edit(
    id: str,
    blog_dto: BlogCreation,
):
    mongo_session["Blog"].update_one(
        {"_id": id},
        {
            "$set": blog_dto.model_dump(
                by_alias=True,
            )
        },
    )


def get(id: str):
    return mongo_session["Blog"].find_one({"_id": id})


def get_comment(post_id: str):
    return db_session.session.query(PostComment).filter_by(post_id=post_id).all()
