from db.postgresql.models.product import (
    MealkitIngredients,
    Product,
    ProductPriceHistory,
    ProductStatus,
)
from db.postgresql.models.transaction import PaymentTransaction
from db.postgresql.paging import Page, display_page, paging
from db.postgresql.models.order_history import (
    Coupon,
    OrderHistory,
    OrderHistoryItems,
    OrderProcess,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)

from datetime import datetime
from uuid import uuid4

import db.postgresql.models.product

def preb_order_history_1() -> OrderHistory:
    return OrderHistory(
        id="Order_001",
        user_id="User_001",  # You can change this if your tests expect a valid user
        order_date=datetime.now(),
        delivery_address="123 Main Street",
        note="Leave at the door",
        total_price=100.0,
        receiver="John Doe",
        phonenumber="1234567890",
        coupon=None,  # Or set an ID if testing coupon linkage
        payment_method=PaymentMethod.COD,
        payment_status=PaymentStatus.PENDING,
        order_status=OrderStatus.ON_CONFIRM,  # or any other starting status
    )

def preb_order_history_item_1(product_price_history: ProductPriceHistory) -> OrderHistoryItems:
 
    # Create the order history item and associate it with the order and product price history
    return OrderHistoryItems(
        order_history_id="Order_001",  # 
        product_id=product_price_history.product_id,  # Foreign key to ProductPriceHistory
        date=product_price_history.date,  # Date from ProductPriceHistory
        quantity=2  # Example quantity
    )