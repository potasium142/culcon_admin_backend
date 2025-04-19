import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from services.product import *
import sqlalchemy as sqla

from ai.clip import OpenCLIP
from db.postgresql.models.blog import ProductDoc
from datetime import datetime
from db.postgresql.models import product as prod
from db.postgresql.models.product import *
from db.postgresql.models.order_history import OrderHistoryItems
from db.postgresql.models.order_history import OrderHistory
from dtos.request.product import (
    ProductUpdate,
    MealKitUpdate,
)
from etc.local_error import HandledError
from sqlalchemy import func
from db.postgresql.paging import Page, display_page, paging, table_size

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.postgresql.models import Base
from .set_up.test_product_data import *
from sqlalchemy.exc import NoResultFound
from pydantic import ValidationError
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
async def test_update_info_success(db_session):
    # Arrange
    prod_id = "Rice_ID"

    # Insert base product and related models
    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    
    product_doc = preb_product_doc_table_1()
    db_session.add(product_doc)

    product_embed = preb_product_embeded_table_1()
    db_session.add(product_embed)

    await db_session.commit()


    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_product_update_dto_1()


    # Act
    result = await update_info(
        prod_id=prod_id,
        prod_info=update_data,
        clip_model=mock_clip,
        ss=db_session
    )

    # Assert
    assert result["id"] == prod_id
    assert result["description"] == update_data.description
    assert result["infos"] == update_data.infos
    assert result["article_md"] == update_data.article_md
    assert "instructions" not in result  # only included for MealKitUpdate

@pytest.mark.asyncio
async def test_update_info_mealkit_success(db_session):
    # Arrange
    prod_id = "Rice_ID"

    # Insert base product and related models
    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    
    product_doc = preb_product_doc_table_1()
    db_session.add(product_doc)

    product_embed = preb_product_embeded_table_1()
    db_session.add(product_embed)

    await db_session.commit()


    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_mealkit_update_dto_1()


    # Act
    result = await update_info(
        prod_id=prod_id,
        prod_info=update_data,
        clip_model=mock_clip,
        ss=db_session
    )

    # Assert
    assert result["id"] == prod_id
    assert result["description"] == update_data.description
    assert result["infos"] == update_data.infos
    assert result["article_md"] == update_data.article_md
    assert "instructions" in result 

@pytest.mark.asyncio
async def test_update_info_mealkit_fail_no_ingredient(db_session):
    # Arrange
    prod_id = "Rice_ID"

    # Insert base product and related models
    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    
    product_doc = preb_product_doc_table_1()
    db_session.add(product_doc)

    product_embed = preb_product_embeded_table_1()
    db_session.add(product_embed)

    await db_session.commit()


    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_mealkit_update_dto_1_fail_1()
    # Act & Assert
    with pytest.raises(HandledError, match="Product id none is not exist"):
        await update_info(
            prod_id=prod_id,
            prod_info=update_data,
            clip_model=mock_clip,
            ss=db_session
        )


@pytest.mark.asyncio
async def test_update_info_fail_no_product_with_id(db_session):
    # Arrange
    prod_id = "Rice_ID"

    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_product_update_dto_1()

    # Act & Assert
    with pytest.raises(NoResultFound):
        await update_info(
            prod_id=prod_id,
            prod_info=update_data,
            clip_model=mock_clip,
            ss=db_session
        )

@pytest.mark.asyncio
async def test_update_info_fail_invalid_expiry(db_session):
    # Arrange
    prod_id = "Rice_ID"
    # Insert base product and related models
    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    
    product_doc = preb_product_doc_table_1()
    db_session.add(product_doc)

    product_embed = preb_product_embeded_table_1()
    db_session.add(product_embed)

    await db_session.commit()
    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_product_update_dto_1_fail_1()

    # Act & Assert
    with pytest.raises(HandledError, match="Product description cannot be empty"):
        await update_info(
            prod_id=prod_id,
            prod_info=update_data,
            clip_model=mock_clip,
            ss=db_session
        )

@pytest.mark.asyncio
async def test_update_info_fail_invalid_description(db_session):
    # Arrange
    prod_id = "Rice_ID"
    # Insert base product and related models
    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    
    product_doc = preb_product_doc_table_1()
    db_session.add(product_doc)

    product_embed = preb_product_embeded_table_1()
    db_session.add(product_embed)

    await db_session.commit()
    # Create mock clip model
    mock_clip = MagicMock()
    mock_clip.encode_text = MagicMock(return_value=[[0.2] * 768])

    # New product update data
    update_data = ex_product_update_dto_1_fail_2()

    # Act & Assert
    with pytest.raises(HandledError, match="Expired day must be bigger than 0"):
        await update_info(
            prod_id=prod_id,
            prod_info=update_data,
            clip_model=mock_clip,
            ss=db_session
        )

@pytest.mark.asyncio
async def test_product_creation_fail_null():
    with pytest.raises(ValidationError) as exc_info:
        ex_product_update_dto_1_null()
        
    assert "description" in str(exc_info.value)

#-----------------------------------------------------------


@pytest.mark.asyncio
async def test_update_price_success(db_session):
    # Arrange
    prod_id = "Rice_ID"

    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    

    new_price = 79.99
    new_sale = 20.0

    # Act
    result = await update_price(
        prod_id=prod_id,
        price=new_price,
        sale_percent=new_sale,
        ss=db_session
    )

    # Assert: return value
    assert result["id"] == prod_id
    assert result["price"] == new_price
    assert result["sale_percent"] == new_sale
    assert isinstance(result["date"], datetime)

    # Assert: product updated
    updated_product = await db_session.get(Product, prod_id)
    assert updated_product.price == new_price
    assert updated_product.sale_percent == new_sale

    # Assert: price history created
    history = (
        await db_session.execute(
            sqla.select(ProductPriceHistory).where(ProductPriceHistory.product_id == prod_id)
        )
    ).scalars().all()
    assert len(history) == 1
    assert history[0].price == pytest.approx(new_price, rel=1e-6)
    assert history[0].sale_percent == pytest.approx(new_sale, rel=1e-6)


@pytest.mark.asyncio
async def test_update_price_fail_invalid_price(db_session):
    # Arrange
    prod_id = "Rice_ID"

    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    

    new_price = 0
    new_sale = 20.0

    with pytest.raises(HandledError, match="Price is not valid"):
        await update_price(
                    prod_id=prod_id,
                    price=new_price,
                    sale_percent=new_sale,
                    ss=db_session
                )
@pytest.mark.asyncio
async def test_update_price_fail_invalid_sale(db_session):
    # Arrange
    prod_id = "Rice_ID"

    product = preb_product_table_1()
    db_session.add(product)
    await db_session.commit()
    

    new_price = 10.0
    new_sale = -10.0

    with pytest.raises(HandledError, match="Sale percent is not valid"):
        await update_price(
                    prod_id=prod_id,
                    price=new_price,
                    sale_percent=new_sale,
                    ss=db_session
                )

#-----------------------------------------------------------

@pytest.mark.asyncio
async def test_restock_product_success(db_session):
    # Arrange
    prod_id = "Rice_ID"
    product = preb_product_table_1()
    product.available_quantity = 10
    product.product_status = ProductStatus.OUT_OF_STOCK  # Assume this status before restocking

    db_session.add(product)
    await db_session.commit()

    restock_amount = 20
    import_price = 45.5

    # Act
    result = await restock_product(
        prod_id=prod_id,
        amount=restock_amount,
        import_price=import_price,
        ss=db_session,
    )

    # Assert: return value
    assert result["in_stock"] == restock_amount
    assert result["in_price"] == pytest.approx(import_price, rel=1e-6)
    assert isinstance(result["in_date"], datetime)

    # Assert: product updated
    updated_product = await db_session.get(Product, prod_id)
    assert updated_product.available_quantity == 10 + restock_amount
    assert updated_product.product_status == ProductStatus.IN_STOCK

    # Assert: stock history created
    history = (
        await db_session.execute(
            sqla.select(ProductStockHistory).where(ProductStockHistory.product_id == prod_id)
        )
    ).scalars().all()
    assert len(history) == 1
    assert history[0].in_stock == restock_amount
    assert history[0].in_price == pytest.approx(import_price, rel=1e-6)

@pytest.mark.asyncio
async def test_restock_product_fail_invalid_ammount(db_session):
    # Arrange
    prod_id = "Rice_ID"
    product = preb_product_table_1()
    product.available_quantity = 10
    product.product_status = ProductStatus.OUT_OF_STOCK  

    db_session.add(product)
    await db_session.commit()

    restock_amount = 0
    import_price =0

    with pytest.raises(HandledError, match="Amount is not valid"):
        await restock_product(
        prod_id=prod_id,
        amount=restock_amount,
        import_price=import_price,
        ss=db_session,
    )

@pytest.mark.asyncio
async def test_restock_product_fail_invalid_price(db_session):
    # Arrange
    prod_id = "Rice_ID"
    product = preb_product_table_1()
    product.available_quantity = 10
    product.product_status = ProductStatus.OUT_OF_STOCK  

    db_session.add(product)
    await db_session.commit()

    restock_amount = 10
    import_price =0

    with pytest.raises(HandledError, match="Price is not valid"):
        await restock_product(
        prod_id=prod_id,
        amount=restock_amount,
        import_price=import_price,
        ss=db_session,
    )

#-----------------------------------------------------------


@pytest.mark.asyncio
async def test_update_status_success(db_session):
    # Arrange
    prod_id = "Rice_ID"
    product = preb_product_table_1()
    product.available_quantity = 10  # Required for IN_STOCK
    product.product_status = ProductStatus.OUT_OF_STOCK

    db_session.add(product)
    await db_session.commit()

    new_status = ProductStatus.IN_STOCK

    # Act
    result = await update_status(
        prod_id=prod_id,
        status=new_status,
        ss=db_session
    )

    # Assert: return value
    assert result["id"] == prod_id
    assert result["status"] == new_status

    # Assert: database was updated
    updated_product = await db_session.get(Product, prod_id)
    assert updated_product.product_status == new_status


@pytest.mark.asyncio
async def test_update_status_fail_invalid_quantity_for_status(db_session):
    # Arrange
    prod_id = "Rice_ID"
    product = preb_product_table_1()
    product.available_quantity = 0  # Required for IN_STOCK
    product.product_status = ProductStatus.OUT_OF_STOCK

    db_session.add(product)
    await db_session.commit()

    new_status = ProductStatus.IN_STOCK


    with pytest.raises(HandledError, match="Quantity is empty"):
        await update_status(
            prod_id=prod_id,
            status=new_status,
            ss=db_session
        )

#-----------------------------------------------------------
