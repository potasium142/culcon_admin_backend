import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from dtos.request.blog import BlogCreation
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
from services.blog import *
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from sqlalchemy.exc import NoResultFound
from etc.local_error import HandledError
from db.postgresql.paging import Page, display_page, paging, table_size
from datetime import datetime
from enum import Enum
import pytest
import pytest_asyncio
from datetime import date

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

from services.account import create_account
from dtos.request.account import AccountCreateDto, AccountInfoForm
from db.postgresql.models.staff_account import AccountType, AccountStatus, StaffAccount
from db.postgresql.models import Base
from db.postgresql.models.shipper import ShipperAvailbility
from sqlalchemy.exc import IntegrityError
from etc.local_error import HandledError

from .set_up.test_blog_data import *
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

# Test database URL
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        # Enable pgvector extension if not already
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Drop all public tables
        await conn.execute(
            text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END 
            $$;
        """)
        )

        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# Provide DB session for tests
@pytest_asyncio.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


# -----------------------------------------------------------
@pytest.mark.asyncio
async def test_create_blog_success(db_session):
    # 🎯 Arrange test input
    blog_dto = get_sample_blog_dto_1()
    dummy_thumbnail = b"fake_image_bytes"

    # 🤖 Mock clip_model
    mock_clip_model = MagicMock()
    mock_clip_model.encode_text.return_value = [[0.1] * 768]  # Example embedding

    # 🧪 Patch cloudinary.upload to return a mock URL
    with patch(
        "services.blog.cloudinary.upload",
        return_value="http://cloudinary.com/fake_thumb.jpg",
    ):
        # 🛠 Act
        result = await create(blog_dto, mock_clip_model, dummy_thumbnail, db_session)

        # ✅ Assert the result structure
        assert "id" in result
        assert result["title"] == blog_dto.title
        assert result["description"] == blog_dto.description
        assert result["article"] == blog_dto.markdown_text
        assert result["thumbnail"] == "http://cloudinary.com/fake_thumb.jpg"
        assert result["infos"] == blog_dto.infos

        # 🔎 Assert blog and blog_embedding were saved in DB
        uuid_id = UUID(result["id"])  # Will raise ValueError if not valid UUID

        blog = await db_session.get(Blog, str(uuid_id))
        blog_embed = await db_session.get(BlogEmbedding, str(uuid_id))

        assert blog is not None
        assert blog_embed is not None


@pytest.mark.asyncio
async def test_create_fail_title_empty(db_session):
    blog_dto = BlogCreation(
        title="", description="Description", markdown_text="Some text", infos={}
    )

    with pytest.raises(HandledError, match="Title cannot be empty"):
        await create(blog_dto, clip_model=MagicMock(), thumbnail=b"img", ss=db_session)


@pytest.mark.asyncio
async def test_create_fail_description_empty(db_session):
    blog_dto = BlogCreation(
        title="Title", description="", markdown_text="Some text", infos={}
    )

    with pytest.raises(HandledError, match="Description cannot be empty"):
        await create(blog_dto, clip_model=MagicMock(), thumbnail=b"img", ss=db_session)


@pytest.mark.asyncio
async def test_create_fail_markdown_text_empty(db_session):
    blog_dto = BlogCreation(
        title="Title", description="Description", markdown_text="", infos={}
    )

    with pytest.raises(HandledError, match="Content of blog cannot be empty"):
        await create(blog_dto, clip_model=MagicMock(), thumbnail=b"img", ss=db_session)


@pytest.mark.asyncio
async def test_create_fail_title_none_validation():
    with pytest.raises(ValidationError) as exc_info:
        BlogCreation(title=None, description=None, markdown_text=None, infos=None)
    assert "title" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_blog_cloudinary_upload_failure():
    blog_dto = BlogCreation(
        title="Title", description="Desc", markdown_text="Text", infos={"views": "1"}
    )
    thumbnail_bytes = b"img"

    mock_clip_model = MagicMock()
    mock_clip_model.encode_text.return_value = [[0.1, 0.2, 0.3]]

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.get_one = AsyncMock()

    mock_context_manager = AsyncMock()
    mock_session.begin.return_value = mock_context_manager
    mock_context_manager.__aenter__.return_value = None
    mock_context_manager.__aexit__.return_value = None

    with patch("services.blog.cloudinary.upload", side_effect=IOError("Upload failed")):
        with pytest.raises(IOError, match="Upload failed"):
            await create(blog_dto, mock_clip_model, thumbnail_bytes, mock_session)


# -----------------------------------------------------------
@pytest.mark.asyncio
async def test_edit_fail_blog_not_found():
    blog_dto = BlogCreation(
        title="Updated Title",
        description="Updated Description",
        markdown_text="Updated Article",
        infos={"tags": "tech"},
    )

    mock_clip_model = MagicMock()
    mock_clip_model.encode_text.return_value = [[0.1, 0.2, 0.3]]

    class FakeAsyncBegin:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_ss = AsyncMock()
    mock_ss.begin = MagicMock(return_value=FakeAsyncBegin())

    # Simulate `get_one` raising NoResultFound on first call
    mock_ss.get_one = AsyncMock(side_effect=NoResultFound("Blog not found"))

    with pytest.raises(NoResultFound):
        await edit("nonexistent-id", mock_clip_model, blog_dto, mock_ss)


# -----------------------------------------------------------
@pytest.mark.asyncio
async def test_get_blog_success():
    # Mock Blog object
    blog = Blog(
        id="123",
        title="Test Title",
        description="Test Desc",
        article="Test Content",
        infos={"tags": "python"},
        thumbnail="test_thumb.jpg",
    )

    # Mock session
    mock_ss = AsyncMock()

    class FakeAsyncBegin:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_ss.begin = MagicMock(return_value=FakeAsyncBegin())
    mock_ss.get_one = AsyncMock(return_value=blog)

    result = await get("123", mock_ss)

    assert result.id == "123"
    assert result.title == "Test Title"


@pytest.mark.asyncio
async def test_get_blog_not_found():
    mock_ss = AsyncMock()

    class FakeAsyncBegin:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_ss.begin = MagicMock(return_value=FakeAsyncBegin())
    mock_ss.get_one = AsyncMock(side_effect=NoResultFound("Blog not found"))

    with pytest.raises(NoResultFound):
        await get("nonexistent-id", mock_ss)


# -----------------------------------------------------------
@pytest.mark.asyncio
async def test_change_comment_status_success():
    # Create a mock PostComment object
    comment = PostComment(
        id="c1",
        timestamp=datetime.utcnow(),
        post_id="post123",
        account_id="user123",
        parent_comment=None,
        comment="Some comment",
        status=CommentStatus.NORMAL,
        comment_type=None,
    )

    # Mock session
    mock_ss = AsyncMock()

    # Mock context manager for session.begin
    class FakeAsyncBegin:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_ss.begin = MagicMock(return_value=FakeAsyncBegin())

    # First get_one returns the original comment, second after update
    mock_ss.get_one = AsyncMock(side_effect=[comment, comment])
    mock_ss.flush = AsyncMock()

    # Run the function
    result = await change_comment_status("c1", CommentStatus.REPORTED, mock_ss)

    # Check result
    assert result.status == CommentStatus.REPORTED
    mock_ss.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_comment_status_not_found():
    mock_ss = AsyncMock()

    class FakeAsyncBegin:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_ss.begin = MagicMock(return_value=FakeAsyncBegin())
    mock_ss.get_one = AsyncMock(side_effect=NoResultFound)

    with pytest.raises(NoResultFound):
        await change_comment_status("invalid_id", CommentStatus.REPORTED, mock_ss)
