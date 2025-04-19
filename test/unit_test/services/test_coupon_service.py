import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from services.coupon import *
from db.postgresql.models.order_history import Coupon
from dtos.request.coupon import CouponCreation
from datetime import datetime
import uuid
import sqlalchemy as sqla
from db.postgresql.db_session import db_session
from db.postgresql.paging import Page, display_page, paging, table_size
from dtos.request.coupon import CouponCreation
from etc.local_error import HandledError
from sqlalchemy.exc import SQLAlchemyError

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models import Base

# Test database URL
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_db():
    async with engine.begin() as conn:
        # Enable pgvector extension if not already
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Drop all public tables
        await conn.execute(text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END 
            $$;
        """))

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


#-----------------------------------------------------------
@pytest.mark.asyncio
async def test_create_coupon_success():
    # Arrange
    mock_ss = AsyncMock()
    mock_ss.begin = MagicMock()
    mock_ss.commit = AsyncMock()

    class FakeAsyncBegin:
        async def __aenter__(self): return None
        async def __aexit__(self, exc_type, exc_val, exc_tb): return None

    mock_ss.begin.return_value = FakeAsyncBegin()

    request_data = CouponCreation(
        id=None,  # Should trigger UUID generation
        expire_date=datetime(2025, 12, 31),
        usage_amount=5,
        sale_percent=20,
        minimum_price=100000,
    )

    # Act
    result = await create_coupon(request_data, mock_ss)

    # Assert
    assert result["usage_amount"] == 5
    assert result["sale_percent"] == 20
    assert result["minimum_price"] == 100000
    assert result["expire_time"] == request_data.expire_date
    assert len(result["id"]) == 14  # UUID trimmed to 14 characters

    # Check that coupon was added to session
    assert mock_ss.add.call_count == 1
    added_coupon: Coupon = mock_ss.add.call_args[0][0]
    assert isinstance(added_coupon, Coupon)
    assert added_coupon.usage_left == 5

@pytest.mark.asyncio
async def test_create_coupon_fail_on_add():
    # Arrange
    mock_ss = AsyncMock()
    mock_ss.begin = MagicMock()

    class FakeAsyncBegin:
        async def __aenter__(self): return None
        async def __aexit__(self, exc_type, exc_val, exc_tb): return None

    mock_ss.begin.return_value = FakeAsyncBegin()

    # This should be a regular MagicMock, not AsyncMock
    mock_ss.add = MagicMock(side_effect=SQLAlchemyError("Failed to add coupon"))

    request_data = CouponCreation(
        id=None,
        expire_date=datetime(2025, 12, 31),
        usage_amount=5,
        sale_percent=20,
        minimum_price=100000,
    )

    # Act & Assert
    with pytest.raises(SQLAlchemyError, match="Failed to add coupon"):
        await create_coupon(request_data, mock_ss)

@pytest.mark.asyncio
async def test_get_coupon_success():
    # Arrange
    coupon_id = "abc123"
    fake_coupon = Coupon(
        id=coupon_id,
        usage_left=10,
        expire_time=datetime(2025, 12, 31),
        sale_percent=15,
        minimum_price=50000,
    )

    mock_ss = AsyncMock()
    mock_ss.begin = MagicMock()

    class FakeAsyncBegin:
        async def __aenter__(self): return None
        async def __aexit__(self, exc_type, exc_val, exc_tb): return None

    mock_ss.begin.return_value = FakeAsyncBegin()
    mock_ss.get.return_value = fake_coupon

    # Act
    result = await get_coupon(coupon_id, mock_ss)

    # Assert
    assert result == {
        "id": coupon_id,
        "usage_left": 10,
        "expire_time": datetime(2025, 12, 31),
        "sale_percent": 15,
        "minimum_price": 50000,
    }

@pytest.mark.asyncio
async def test_get_coupon_not_found():
    # Arrange
    mock_ss = AsyncMock()
    mock_ss.begin = MagicMock()

    class FakeAsyncBegin:
        async def __aenter__(self): return None
        async def __aexit__(self, exc_type, exc_val, exc_tb): return None

    mock_ss.begin.return_value = FakeAsyncBegin()
    mock_ss.get.return_value = None

    # Act
    result = await get_coupon("nonexistent_id", mock_ss)

    # Assert
    assert result == {"error": "Coupon not found"}



@pytest.mark.asyncio
async def test_disable_coupon_success():
    # Arrange
    coupon = MagicMock(spec=Coupon)
    coupon.id = "existing-id"
    coupon.usage_left = 5

    mock_session = MagicMock()
    mock_session.get = AsyncMock(return_value=coupon)
    mock_session.commit = AsyncMock()

    # Act
    await disable_coupon("existing-id", mock_session)

    # Assert
    assert coupon.usage_left == -1
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_disable_coupon_not_found():
    # Arrange
    fake_coupon_id = "nonexistent-id"
    
    mock_session = MagicMock()
    mock_session.get = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(HandledError, match="Coupon not found"):
        await disable_coupon(fake_coupon_id, mock_session)