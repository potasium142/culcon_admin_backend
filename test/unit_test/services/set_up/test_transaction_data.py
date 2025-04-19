from db.postgresql.models.transaction import PaymentTransaction
from db.postgresql.models.order_history import PaymentStatus, OrderHistory
from datetime import datetime

def preb_payment_transaction_table_1():
    return PaymentTransaction(
        order_id="Order_001",  # Must match the OrderHistory test object
        create_time=datetime.utcnow(),
        payment_id="PAYPAL_PAYMENT_123456",
        refund_id=None,
        url="https://paypal.com/payment/PAYPAL_PAYMENT_123456",
        transaction_id="TX1234567890",
        status=PaymentStatus.PENDING,
        amount=99.99,
    )