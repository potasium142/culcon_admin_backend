import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from services.product_ import *
from io import BytesIO
from PIL import Image, ImageFile
from fastapi import BackgroundTasks
from ai import clip, yolo
from db.postgresql.models.blog import ProductDoc
import db.postgresql.models.product as prod
import sqlalchemy as sqla
from db.postgresql.models.product import Product  # Replace with the actual module path

from db.postgresql.paging import Page, display_page, paging
from dtos.request.product import MealKitCreation, ProductCreation
from etc import cloudinary
from etc.local_error import HandledError
from pydantic import ValidationError

from unittest.mock import AsyncMock, MagicMock


import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select  
from sqlalchemy.exc import IntegrityError
from db.postgresql.models import Base
from .set_up.test_product_data import *
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
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_success(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    result = await product_creation(
        prod_info=product_info,
        additional_images=additional_images,
        main_image=main_image_bytes,
        yolo_model=fake_yolo,
        clip_model=fake_clip,
        ss=db_session,
        bg_task=bg_tasks
    )

    # Assertions
    assert result["id"].startswith("VEG_TestProduct")
    assert result["name"] == "Test Product"

    # Check database entry exists
    product_in_db = await db_session.get(prod.Product, result["id"])
    assert product_in_db is not None
    assert product_in_db.product_name == "Test Product"

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_fail_invalid_name(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1_fail_1()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    with pytest.raises(HandledError, match="Product name is not valid"):
        await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_fail_invalid_name_too_long(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1_fail_2()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    with pytest.raises(HandledError, match="Product id is longer than 255, please trim down product name"):
        await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_fail_invalid_description(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1_fail_3()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    with pytest.raises(HandledError, match="Product description cannot be empty"):
        await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_fail_invalid_expired(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1_fail_4()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    with pytest.raises(HandledError, match="Expired day must be bigger than 0"):
        await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_product_creation_fail_product_exist(mock_upload, db_session):
    # Mock main and additional image bytes
    fake_image = BytesIO()
    Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
    main_image_bytes = fake_image.getvalue()
    additional_images = [main_image_bytes]

    product_info = ex_product_creation_dto_1()
    # Mock the ML models
    fake_clip = MagicMock()
    fake_clip.encode_text.return_value = [[0.1] * 512]
    fake_clip.encode_image.return_value = [[0.2] * 512]

    fake_yolo = MagicMock()
    fake_yolo.embed.return_value = [[0.3] * 512]

    # Background tasks
    bg_tasks = BackgroundTasks()

    # Call the function
    await product_creation(
        prod_info=product_info,
        additional_images=additional_images,
        main_image=main_image_bytes,
        yolo_model=fake_yolo,
        clip_model=fake_clip,
        ss=db_session,
        bg_task=bg_tasks
    )

    with pytest.raises(HandledError, match="Product is already exists"):
        await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

#@-----------------------------------------------------------
@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_mealkit_creation_success(mock_upload, db_session):
    # Start a transaction block to ensure rollback happens after the test
    
        # Create fake image bytes
        fake_image = BytesIO()
        Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
        main_image_bytes = fake_image.getvalue()
        additional_images = [main_image_bytes]

        # Use MealKit DTO
        product_info = ex_mealkit_creation_dto_1()  

        # Mock ML models
        fake_clip = MagicMock()
        fake_clip.encode_text.return_value = [[0.1] * 512]
        fake_clip.encode_image.return_value = [[0.2] * 512]

        fake_yolo = MagicMock()
        fake_yolo.embed.return_value = [[0.3] * 512]

        bg_tasks = BackgroundTasks()

        # Create the required products first
        product_rice = prod.Product(
            id="Rice_ID", 
            product_name="Rice",
            available_quantity=1000,
            product_types=prod.ProductType.VEGETABLE,  # Assuming the correct type
            product_status=prod.ProductStatus.IN_STOCK,  # Assuming the correct status
            image_url="url_to_image",
            price=5.0
        )
        product_tofu = prod.Product(
            id="Tofu_ID", 
            product_name="Tofu",
            available_quantity=1000,
            product_types=prod.ProductType.VEGETABLE,  # Assuming the correct type
            product_status=prod.ProductStatus.IN_STOCK,  # Assuming the correct status
            image_url="url_to_image",
            price=6.0
        )

        # Add the products to the session
        db_session.add(product_rice)
        db_session.add(product_tofu)
        await db_session.commit()  # Commit the product inserts

        # Now call service to create meal kit
        result = await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

        # Assertions
        assert result["id"].startswith("MK_TestMealKit")  # Assuming "MEALKIT_" prefix
        assert result["name"] == "Test MealKit"

        # Check product in DB
        product_in_db = await db_session.get(prod.Product, result["id"])
        assert product_in_db is not None
        assert product_in_db.product_name == "Test MealKit"

        # Check ingredients were saved
        result_ingredients = (
            await db_session.execute(
                select(prod.MealkitIngredients).where(prod.MealkitIngredients.mealkit_id == result["id"])
            )
        ).scalars().all()

        assert len(result_ingredients) == 2  # Assuming 2 ingredients (Rice, Tofu)
        ingredient_names = {ing.ingredient for ing in result_ingredients}
        assert "Rice_ID" in ingredient_names
        assert "Tofu_ID" in ingredient_names

        # Check that the foreign key relationships are respected
        rice_product = await db_session.execute(select(prod.Product).where(prod.Product.product_name == "Rice"))
        tofu_product = await db_session.execute(select(prod.Product).where(prod.Product.product_name == "Tofu"))
        assert rice_product.scalar() is not None
        assert tofu_product.scalar() is not None

@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_mealkit_creation_success_with_no_ingredient(mock_upload, db_session):
    # Start a transaction block to ensure rollback happens after the test
    
        # Create fake image bytes
        fake_image = BytesIO()
        Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
        main_image_bytes = fake_image.getvalue()
        additional_images = [main_image_bytes]

        # Use MealKit DTO
        product_info = ex_mealkit_creation_dto_empty_1()  

        # Mock ML models
        fake_clip = MagicMock()
        fake_clip.encode_text.return_value = [[0.1] * 512]
        fake_clip.encode_image.return_value = [[0.2] * 512]

        fake_yolo = MagicMock()
        fake_yolo.embed.return_value = [[0.3] * 512]

        bg_tasks = BackgroundTasks()

        
        # Now call service to create meal kit
        result = await product_creation(
            prod_info=product_info,
            additional_images=additional_images,
            main_image=main_image_bytes,
            yolo_model=fake_yolo,
            clip_model=fake_clip,
            ss=db_session,
            bg_task=bg_tasks
        )

        # Assertions
        assert result["id"].startswith("MK_TestMealKit")  # Assuming "MEALKIT_" prefix
        assert result["name"] == "Test MealKit"

        # Check product in DB
        product_in_db = await db_session.get(prod.Product, result["id"])
        assert product_in_db is not None
        assert product_in_db.product_name == "Test MealKit"

        # Check ingredients were saved
        result_ingredients = (
            await db_session.execute(
                select(prod.MealkitIngredients).where(prod.MealkitIngredients.mealkit_id == result["id"])
            )
        ).scalars().all()

        assert len(result_ingredients) == 0  
   


@pytest.mark.asyncio
@patch("services.product_.cloudinary.upload", return_value="http://fakeurl.com/image.jpg")
async def test_mealkit_creation_fail_no_ingredent_product_in_database(mock_upload, db_session):
    # Start a transaction block to ensure rollback happens after the test
    
        # Create fake image bytes
        fake_image = BytesIO()
        Image.new("RGB", (100, 100)).save(fake_image, format="PNG")
        main_image_bytes = fake_image.getvalue()
        additional_images = [main_image_bytes]

        # Use MealKit DTO
        product_info = ex_mealkit_creation_dto_2()  

        # Mock ML models
        fake_clip = MagicMock()
        fake_clip.encode_text.return_value = [[0.1] * 512]
        fake_clip.encode_image.return_value = [[0.2] * 512]

        fake_yolo = MagicMock()
        fake_yolo.embed.return_value = [[0.3] * 512]

        bg_tasks = BackgroundTasks()


        with pytest.raises(IntegrityError, match="violates foreign key constraint"):
            await product_creation(
                prod_info=product_info,
                additional_images=additional_images,
                main_image=main_image_bytes,
                yolo_model=fake_yolo,
                clip_model=fake_clip,
                ss=db_session,
                bg_task=bg_tasks
            )


@pytest.mark.asyncio
async def test_product_creation_fail_null():
    with pytest.raises(ValidationError) as exc_info:
        ex_product_creation_dto_1_null()
        
    assert "product_name" in str(exc_info.value)
