from datetime import datetime, timedelta
import random
import uuid
import faker

import sqlalchemy as sqla

# Kết nối đến cơ sở dữ liệu
URL_DATABASE = "postgresql+psycopg://culcon:culcon@localhost:5432/culcon_test"
engine = sqla.create_engine(URL_DATABASE)
conn = engine.connect()

fake = faker.Faker()

# Số lượng dữ liệu cần tạo
NUM_PRODUCTS = 50
NUM_USERS = 20
NUM_ORDERS = 100
NUM_BLOGS = 10
NUM_COUPONS = 10

# Các loại sản phẩm
PRODUCT_TYPES = ["VEGETABLE", "MEAT", "SEASON", "MEALKIT"]
PRODUCT_STATUSES = ["IN_STOCK", "OUT_OF_STOCK", "NO_LONGER_IN_SALE"]
PAYMENT_METHODS = ["PAYPAL", "VNPAY", "COD"]
PAYMENT_STATUSES = [
    "PENDING",
    "RECEIVED",
    "REFUNDED",
    "REFUNDING",
    "CREATED",
    "CHANGED",
]
ORDER_STATUSES = ["ON_CONFIRM", "ON_PROCESSING", "ON_SHIPPING", "SHIPPED", "CANCELLED"]

# Thêm sản phẩm
product_ids = [
    "VEG_WholeGarlicBulb",
    "VEG_FreshCarrots",
    "MEAT_BonelessChickenBreast",
    "MEAT_FreshAtlanticSalmon",
    "SS_BlackPepperPowder",
    "MEAT_GarlicButterSalmonwithRoastedCarrots",
    "MK_GarlicPepperChickenStir-Fry",
]

# Thêm lịch sử giá sản phẩm
for product_id in product_ids:
    for i in range(90):  # 90 ngày
        price_history_data = {
            "price": round(random.uniform(10, 100), 2),
            "sale_percent": round(random.uniform(0, 50), 2),
            "date": datetime.now() - timedelta(days=i),
            "product_id": product_id,
        }
        conn.execute(
            sqla.text(
                "INSERT INTO public.product_price_history (price, sale_percent, date, product_id) "
                "VALUES (:price, :sale_percent, :date, :product_id)"
            ),
            price_history_data,
        )

# Thêm lịch sử tồn kho
for product_id in product_ids:
    for i in range(10):  # 10 lần nhập kho
        stock_history_data = {
            "product_id": product_id,
            "date": datetime.now() - timedelta(days=random.randint(1, 90)),
            "in_price": round(random.uniform(5, 50), 2),
            "in_stock": random.randint(10, 50),
        }
        conn.execute(
            sqla.text(
                "INSERT INTO public.product_stock_history (product_id, date, in_price, in_stock) "
                "VALUES (:product_id, :date, :in_price, :in_stock)"
            ),
            stock_history_data,
        )

# Thêm người dùng
user_ids = []
for _ in range(NUM_USERS):
    user_id = str(uuid.uuid4())
    user_ids.append(user_id)
    user_data = {
        "id": user_id,
        "email": fake.email(),
        "username": fake.user_name(),
        "password": fake.password(),
        "status": random.choice(["NON_ACTIVE", "NORMAL", "BANNED", "DEACTIVATE"]),
        "address": fake.address(),
        "phone": fake.phone_number(),
        "profile_pic_uri": fake.image_url(),
        "profile_description": fake.sentence(),
        "token": "",
        "bookmarked_posts": [],
    }
    conn.execute(
        sqla.text(
            "INSERT INTO public.user_account (id, email, username, password, status, address, phone, profile_pic_uri, profile_description, token, bookmarked_posts) "
            "VALUES (:id, :email, :username, :password, :status, :address, :phone, :profile_pic_uri, :profile_description, :token, :bookmarked_posts)"
        ),
        user_data,
    )

# Thêm đơn hàng
for _ in range(NUM_ORDERS):
    order_id = random.randint(1, 10**18)  # Sử dụng BIGINT thay vì UUID
    user_id = random.choice(user_ids)
    order_data = {
        "id": order_id,
        "user_id": user_id,
        "order_date": datetime.now() - timedelta(days=random.randint(1, 90)),
        "delivery_address": fake.address(),
        "note": fake.sentence(),
        "total_price": round(random.uniform(50, 500), 2),
        "receiver": fake.name(),
        "phonenumber": fake.phone_number()[:12],
        "coupon": None,
        "updated_coupon": random.choice([True, False]),
        "updated_payment": random.choice([True, False]),
        "payment_method": random.choice(PAYMENT_METHODS),
        "payment_status": random.choice(PAYMENT_STATUSES),
        "order_status": random.choice(ORDER_STATUSES),
    }
    conn.execute(
        sqla.text(
            "INSERT INTO public.order_history (id, user_id, order_date, delivery_address, note, total_price, receiver, phonenumber, coupon, updated_coupon, updated_payment, payment_method, payment_status, order_status) "
            "VALUES (:id, :user_id, :order_date, :delivery_address, :note, :total_price, :receiver, :phonenumber, :coupon, :updated_coupon, :updated_payment, :payment_method, :payment_status, :order_status)"
        ),
        order_data,
    )


# Thêm phiếu giảm giá
for _ in range(NUM_COUPONS):
    coupon_data = {
        "id": str(uuid.uuid4()),
        "expire_time": datetime.now() + timedelta(days=random.randint(1, 90)),
        "sale_percent": round(random.uniform(5, 50), 2),
        "usage_amount": random.randint(10, 100),
        "usage_left": random.randint(1, 10),
        "minimum_price": round(random.uniform(20, 100), 2),
    }
    conn.execute(
        sqla.text(
            "INSERT INTO public.coupon (id, expire_time, sale_percent, usage_amount, usage_left, minimum_price) "
            "VALUES (:id, :expire_time, :sale_percent, :usage_amount, :usage_left, :minimum_price)"
        ),
        coupon_data,
    )

# Lấy danh sách các đơn hàng từ bảng order_history
order_ids = conn.execute(sqla.text("SELECT id FROM public.order_history")).fetchall()
order_ids = [row[0] for row in order_ids]

product_price_history = conn.execute(
    sqla.text("SELECT product_id, date FROM public.product_price_history")
).fetchall()

for order_id in order_ids:
    num_items = random.randint(1, 5)
    for _ in range(num_items):
        product = random.choice(product_price_history)
        product_id = product[0]
        product_date = product[1]

        order_item_data = {
            "order_history_id": order_id,
            "product_id_product_id": product_id,
            "product_id_date": product_date,
            "quantity": random.randint(1, 10),
        }

        conn.execute(
            sqla.text(
                "INSERT INTO public.order_history_items (order_history_id, product_id_product_id, product_id_date, quantity) "
                "VALUES (:order_history_id, :product_id_product_id, :product_id_date, :quantity)"
            ),
            order_item_data,
        )

# Lấy danh sách các đơn hàng từ bảng order_history
order_data = conn.execute(
    sqla.text("SELECT id, total_price FROM public.order_history")
).fetchall()

# Các trạng thái thanh toán
PAYMENT_STATUSES = [
    "PENDING",
    "RECEIVED",
    "REFUNDED",
    "REFUNDING",
    "CREATED",
    "CHANGED",
]

# Thêm dữ liệu vào bảng payment_transaction
for order in order_data:
    order_id = order[0]
    total_price = order[1]

    # Tạo dữ liệu cho payment_transaction
    payment_data = {
        "order_id": order_id,
        # Thời gian ngẫu nhiên trong 3 tháng qua
        "create_time": datetime.now() - timedelta(days=random.randint(1, 90)),
        "payment_id": str(uuid.uuid4()),  # ID thanh toán ngẫu nhiên
        # 20% giao dịch có refund_id
        "refund_id": None if random.random() > 0.8 else str(uuid.uuid4()),
        "url": fake.url(),
        "transaction_id": str(uuid.uuid4()),  # ID giao dịch ngẫu nhiên
        # Trạng thái thanh toán ngẫu nhiên
        "status": random.choice(PAYMENT_STATUSES),
        "amount": total_price,  # Số tiền thanh toán lấy từ total_price
    }

    # Chèn dữ liệu vào bảng payment_transaction
    conn.execute(
        sqla.text(
            "INSERT INTO public.payment_transaction (order_id, create_time, payment_id, refund_id, url, transaction_id, status, amount) "
            "VALUES (:order_id, :create_time, :payment_id, :refund_id, :url, :transaction_id, :status, :amount)"
        ),
        payment_data,
    )
# Lấy danh sách người dùng từ bảng user_account
user_ids = conn.execute(sqla.text("SELECT id FROM public.user_account")).fetchall()
user_ids = [row[0] for row in user_ids]

# Lấy danh sách sản phẩm từ bảng product
product_ids = conn.execute(sqla.text("SELECT id FROM public.product")).fetchall()
product_ids = [row[0] for row in product_ids]

# Thêm dữ liệu vào bảng cart
for user_id in user_ids:
    # Chọn ngẫu nhiên số lượng sản phẩm trong giỏ hàng (1-5 sản phẩm)
    for _ in range(1):
        # Chọn ngẫu nhiên một sản phẩm
        product_id = random.choice(product_ids)

        # Tạo dữ liệu cho cart
        cart_data = {
            "amount": random.randint(1, 10),  # Số lượng sản phẩm ngẫu nhiên
            "account_id": user_id,
            "product_id": product_id,
        }

        # Chèn dữ liệu vào bảng cart
        conn.execute(
            sqla.text(
                "INSERT INTO public.cart (amount, account_id, product_id) "
                "VALUES (:amount, :account_id, :product_id)"
            ),
            cart_data,
        )

conn.commit()
conn.close()
