import pytest
from unittest.mock import  AsyncMock, MagicMock, patch, Mock
from services.order import *
from db.postgresql.models.product import (
    MealkitIngredients,
    Product,
    ProductPriceHistory,
    ProductStatus,
    ProductType,
)
from db.postgresql.paging import Page, display_page, paging, table_size
from db.postgresql.models.order_history import (
    Coupon,
    OrderHistory,
    OrderHistoryItems,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    DeliveryStatus,
)
from etc.local_error import HandledError

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from db.postgresql.models import Base
from .set_up.test_order_data import *
from .set_up.test_product_data import *
from .set_up.test_user_account_data import *
from .set_up.test_account_data import *
from .set_up.test_transaction_data import *
from uuid import UUID
from sqlalchemy.exc import NoResultFound 
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
async def test_change_order_status_success(db_session):
    # Arrange
    order_id = "Order_001"
    initial_status = OrderStatus.ON_CONFIRM
    new_status = OrderStatus.ON_PROCESSING


    user_account = preb_user_account_1()  
    db_session.add(user_account)
    await db_session.commit()


    order = preb_order_history_1() 
    db_session.add(order)
    await db_session.commit()

    # Act
    result = await change_order_status(
        id=order_id,
        ss=db_session,
        prev_status=initial_status,
        status=new_status
    )

    # Assert: result is True (status was changed)
    assert result is True

    # Assert: order's new status in DB
    updated_order = await db_session.get(OrderHistory, order_id)
    assert updated_order.order_status == new_status

@pytest.mark.asyncio
async def test_change_order_status_fail_previous_status(db_session):
    order_id = "Order_001"
  

    user_account = preb_user_account_1()  
    db_session.add(user_account)
    await db_session.commit()

    order = preb_order_history_1()
    order.order_status = OrderStatus.DELIVERED  # Incorrect previous status

    db_session.add(order)
    await db_session.commit()

    with pytest.raises(HandledError, match="Status of order must be ON_CONFIRM"):
        await change_order_status(
            id=order_id,
            ss=db_session,
            prev_status=OrderStatus.ON_CONFIRM,  # Expecting PLACED, but it's SHIPPED
            status=OrderStatus.DELIVERED
        )

#-----------------------------------------------------------
@pytest.mark.asyncio
async def test_accept_order_success(db_session):
    # Arrange
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    staff_account = preb_staff_account_1()  
    db_session.add(staff_account)
    await db_session.commit()

    user_account = preb_user_account_1()  
    db_session.add(user_account)
    await db_session.commit()

    # Create mock order
    mock_order = preb_order_history_1()
    db_session.add(mock_order)
    await db_session.commit()

    # Create mock order history items
    mock_product = preb_product_table_1()
    db_session.add(mock_product)
    await db_session.commit()

    mock_product_price_history = preb_product_price_history_table_1()
    db_session.add(mock_product_price_history)
    await db_session.commit()

    mock_order_history_item = preb_order_history_item_1(mock_product_price_history)
    db_session.add(mock_order_history_item)
    await db_session.commit()

    # Act: Call the accept_order function
    result = await accept_order(order_id, db_session, staff_id)

    # Assert: The result should be True (status change successful)
    assert result is True

    # Assert: The order's status should now be ON_PROCESSING
    updated_order = await db_session.get(OrderHistory, order_id)
    assert updated_order.order_status == OrderStatus.ON_PROCESSING

    order_process_get = await db_session.execute(
        select(OrderProcess).filter(OrderProcess.order_id == order_id)
    )
    order_process = order_process_get.scalars().first()  # Get the first OrderProcess row

    assert order_process is not None
    assert order_process.delivery_status == DeliveryStatus.AWAIT
    assert order_process.process_by == UUID(staff_id)


@pytest.mark.asyncio
async def test_accept_order_fail_insufficient_stock(db_session):
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    db_session.add(preb_user_account_1())
    db_session.add(preb_order_history_1())
    
    mock_product = preb_product_table_1()
    db_session.add(mock_product)

    price = preb_product_price_history_table_1()
    db_session.add(price)

    order_item = preb_order_history_item_1(price)
    order_item.quantity = 10000
    db_session.add(order_item)

    await db_session.commit()

    with pytest.raises(HandledError, match="does not have enough stock"):
        await accept_order(order_id, db_session, staff_id)


@pytest.mark.asyncio
async def test_accept_order_invalid_status(db_session):
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    db_session.add(preb_user_account_1())
    order = preb_order_history_1()
    order.order_status = OrderStatus.CANCELLED
    db_session.add(order)
    
    mock_product = preb_product_table_1()
    db_session.add(mock_product)

    price = preb_product_price_history_table_1()
    db_session.add(price)

    order_item = preb_order_history_item_1(price)
    db_session.add(order_item)

    await db_session.commit()

    with pytest.raises(HandledError, match="Status of order must be ON_CONFIRM"):
        await accept_order(order_id, db_session, staff_id)


@pytest.mark.asyncio
async def test_accept_order_invalid_cod_payment_status(db_session):
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    db_session.add(preb_user_account_1())

    order = preb_order_history_1()
    order.payment_method=PaymentMethod.COD
    order.payment_status=PaymentStatus.RECEIVED
    
    db_session.add(order)

    mock_product = preb_product_table_1()
    db_session.add(mock_product)

    price = preb_product_price_history_table_1()
    db_session.add(price)

    db_session.add(preb_order_history_item_1(price))
    await db_session.commit()

    with pytest.raises(HandledError, match="Illegal payment status"):
        await accept_order(order_id, db_session, staff_id)


@pytest.mark.asyncio
async def test_accept_order_not_paid_non_cod(db_session):
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    db_session.add(preb_user_account_1())

    order = preb_order_history_1()
    order.payment_method=PaymentMethod.PAYPAL
    order.payment_status=PaymentStatus.PENDING
    
    db_session.add(order)

    mock_product = preb_product_table_1()
    db_session.add(mock_product)

    price = preb_product_price_history_table_1()
    db_session.add(price)

    db_session.add(preb_order_history_item_1(price))
    await db_session.commit()

    with pytest.raises(HandledError, match="Order has not paid"):
        await accept_order(order_id, db_session, staff_id)


@pytest.mark.asyncio
async def test_accept_order_sets_out_of_stock(db_session):
    order_id = "Order_001"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    db_session.add(preb_user_account_1())
    db_session.add(preb_order_history_1())
    
    mock_product = preb_product_table_1()
    mock_product.available_quantity = 0
    db_session.add(mock_product)

    price = preb_product_price_history_table_1()
    db_session.add(price)

    order_item = preb_order_history_item_1(price)
    order_item.quantity = 1000
    db_session.add(order_item)

    await db_session.commit()

    result = await accept_order(order_id, db_session, staff_id)

    updated_product = await db_session.get(type(mock_product), mock_product.id)
    assert result is True
    assert updated_product.product_status == ProductStatus.OUT_OF_STOCK


@pytest.mark.asyncio
async def test_accept_order_invalid_order_id(db_session):
    order_id = "NonExistentID"
    staff_id = "12345678-9012-3456-7890-123456789012"

    db_session.add(preb_staff_account_1())
    await db_session.commit()

    with pytest.raises(NoResultFound):  # Replace with NoResultFound if not caught
        await accept_order(order_id, db_session, staff_id)
#-----------------------------------------------------------



@pytest.mark.asyncio
@patch("culcon_admin_backend.services.order.payment_controller.refund_captured_payment")
async def test_cancel_order_success(mock_refund, db_session):
    # Setup fake refund response
    mock_refund.return_value = MagicMock(body=MagicMock(id="REFUND_123"))
    # Arrange
    order_id = "Order_001"

    user_account = preb_user_account_1()
    db_session.add(user_account)
    await db_session.commit()

    # Add product
    product = preb_product_table_1()
    original_quantity = product.available_quantity 
    db_session.add(product)
    await db_session.commit()


    # Add product price history
    price_history = preb_product_price_history_table_1()
    db_session.add(price_history)
    await db_session.commit()



    # Create order
    order = preb_order_history_1()
    order.order_status = OrderStatus.ON_CONFIRM  # Should be cancelable
    order.payment_method = PaymentMethod.PAYPAL
    db_session.add(order)
    await db_session.commit()

    # Create order item
    order_item = preb_order_history_item_1(price_history)
    order_item.order_history_id = order_id
    order_item.quantity = 2
    db_session.add(order_item)
    await db_session.commit()

    # Create PAYPAL payment transaction
    payment_transaction = preb_payment_transaction_table_1()
    db_session.add(payment_transaction)
    await db_session.commit()

    # Act
    result = await cancel_order(order_id, db_session)

    # Assert
    assert result is True

    updated_order = await db_session.get(OrderHistory, order_id)
    assert updated_order.order_status == OrderStatus.CANCELLED

    payment = await db_session.get(PaymentTransaction, order_id)
    assert payment.status == PaymentStatus.REFUNDED
    assert payment.refund_id is not None

    # Check if inventory was restocked
    updated_product = await db_session.get(Product, product.id)
    assert updated_product.available_quantity == original_quantity + 2  

@pytest.mark.asyncio
@patch("culcon_admin_backend.services.order.payment_controller.refund_captured_payment")
async def test_cancel_order_fail_on_shipping(mock_refund, db_session):
    # Setup fake refund response
    mock_refund.return_value = MagicMock(body=MagicMock(id="REFUND_123"))
    # Arrange
    order_id = "Order_001"

    user_account = preb_user_account_1()
    db_session.add(user_account)
    await db_session.commit()

    # Add product
    product = preb_product_table_1()
    original_quantity = product.available_quantity 
    db_session.add(product)
    await db_session.commit()


    # Add product price history
    price_history = preb_product_price_history_table_1()
    db_session.add(price_history)
    await db_session.commit()

    # Create order
    order = preb_order_history_1()
    order.order_status = OrderStatus.ON_SHIPPING 
    order.payment_method = PaymentMethod.PAYPAL
    db_session.add(order)
    await db_session.commit()

    # Create order item
    order_item = preb_order_history_item_1(price_history)
    order_item.order_history_id = order_id
    order_item.quantity = 2
    db_session.add(order_item)
    await db_session.commit()

    # Create PAYPAL payment transaction
    payment_transaction = preb_payment_transaction_table_1()
    db_session.add(payment_transaction)
    await db_session.commit()

    # Act
    with pytest.raises(HandledError, match="Order already in delivering"):
        await cancel_order(order_id, db_session)

@pytest.mark.asyncio
@patch("culcon_admin_backend.services.order.payment_controller.refund_captured_payment")
async def test_cancel_order_fail_delivered(mock_refund, db_session):
    # Setup fake refund response
    mock_refund.return_value = MagicMock(body=MagicMock(id="REFUND_123"))
    # Arrange
    order_id = "Order_001"

    user_account = preb_user_account_1()
    db_session.add(user_account)
    await db_session.commit()

    # Add product
    product = preb_product_table_1()
    original_quantity = product.available_quantity 
    db_session.add(product)
    await db_session.commit()


    # Add product price history
    price_history = preb_product_price_history_table_1()
    db_session.add(price_history)
    await db_session.commit()

    # Create order
    order = preb_order_history_1()
    order.order_status = OrderStatus.SHIPPED 
    order.payment_method = PaymentMethod.PAYPAL
    db_session.add(order)
    await db_session.commit()

    # Create order item
    order_item = preb_order_history_item_1(price_history)
    order_item.order_history_id = order_id
    order_item.quantity = 2
    db_session.add(order_item)
    await db_session.commit()

    # Create PAYPAL payment transaction
    payment_transaction = preb_payment_transaction_table_1()
    db_session.add(payment_transaction)
    await db_session.commit()

    # Act
    with pytest.raises(HandledError, match="Order already  delivered"):
        await cancel_order(order_id, db_session)

@pytest.mark.asyncio
@patch("culcon_admin_backend.services.order.payment_controller.refund_captured_payment")
async def test_cancel_order_fail_cancel(mock_refund, db_session):
    # Setup fake refund response
    mock_refund.return_value = MagicMock(body=MagicMock(id="REFUND_123"))
    # Arrange
    order_id = "Order_001"

    user_account = preb_user_account_1()
    db_session.add(user_account)
    await db_session.commit()

    # Add product
    product = preb_product_table_1()
    original_quantity = product.available_quantity 
    db_session.add(product)
    await db_session.commit()


    # Add product price history
    price_history = preb_product_price_history_table_1()
    db_session.add(price_history)
    await db_session.commit()

    # Create order
    order = preb_order_history_1()
    order.order_status = OrderStatus.CANCELLED 
    order.payment_method = PaymentMethod.PAYPAL
    db_session.add(order)
    await db_session.commit()

    # Create order item
    order_item = preb_order_history_item_1(price_history)
    order_item.order_history_id = order_id
    order_item.quantity = 2
    db_session.add(order_item)
    await db_session.commit()

    # Create PAYPAL payment transaction
    payment_transaction = preb_payment_transaction_table_1()
    db_session.add(payment_transaction)
    await db_session.commit()

    # Act
    with pytest.raises(HandledError, match="Order already cancelled"):
        await cancel_order(order_id, db_session)