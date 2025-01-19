from datetime import date, datetime
import faker
from passlib.context import CryptContext
import sqlalchemy as sqla
import uuid
import random
from tqdm.auto import tqdm
import json

# ========================================================
URL_DATABASE = "postgresql+psycopg://culcon:culcon@localhost:5432/culcon"

USER_AMOUNT = 0
STAFF_AMOUNT = 0
VARIANCE_OF_PRICE = 7
# ========================================================

fake = faker.Faker()
engine = sqla.create_engine(URL_DATABASE)
conn = engine.connect()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USER_STATEMENT = sqla.text(
    "INSERT INTO "
    + "user_account(id,email,username,password,status,address,phone,profile_pic_uri,profile_description,token,bookmarked_posts) "
    + "VALUES(:id,:email,:username,:password,:status,:address,:phone,:profile_pic_uri,:profile_description,:token,:bookmarked_posts)"
)

STAFF_STATMENT = sqla.text(
    "INSERT INTO"
    + " staff_account(id,username,password,type,status,token) VALUES"
    + " (:id,:username,:password,:type,:status,:token)"
)

EMPLOYEE_INFO_STATEMENT = sqla.text(
    "INSERT INTO"
    + " employee_info(account_id,ssn,phonenumber,realname,email,dob) VALUES"
    + " (:account_id,:ssn,:phonenumber,:realname,:email,:dob)",
)

PRODUCT_STATEMENT = sqla.text(
    "INSERT INTO "
    + "product(id,product_name,available_quantity,product_types,product_status,image_url,price,sale_percent) "
    + "VALUES (:id,:product_name,:available_quantity,:product_types,:product_status,:image_url,:price,:sale_percent)"
)

PRODUCT_PRICE_HISTORY_STATEMENT = sqla.text(
    "INSERT INTO product_price_history(price, sale_percent, date, product_id) "
    + "VALUES (:price, :sale_percent, :date, :product_id)"
)

PRODUCT_DOC_STATEMENT = sqla.text(
    "INSERT INTO product_doc(id, description, images_url, infos, ingredients, instructions, article_md, day_before_expiry) "
    + "VALUES (:id, :description, :images_url, :infos, :ingredients, :instructions, :article_md, :day_before_expiry)"
)

PRODUCT_IMAGES = [
    "https://minecraft.wiki/images/Potato_JE2.png",
    "https://minecraft.wiki/images/Melon_Slice_JE2_BE2.png",
    "https://minecraft.wiki/images/Carrot_JE3_BE2.png",
    "https://minecraft.wiki/images/Golden_Carrot_JE4_BE2.png",
    "https://minecraft.wiki/images/Sweet_Berries_JE1_BE1.png",
    "https://minecraft.wiki/images/Glow_Berries_JE1_BE1.png",
    "https://minecraft.wiki/images/Golden_Apple_JE2_BE2.png",
    "https://minecraft.wiki/images/Apple_JE3_BE3.png",
]

PROFILE_URI = "https://media1.tenor.com/m/kXJajV6M8jEAAAAd/iron-man-jarvis.gif"

USER_STATUS = [
    "NON_ACTIVE",
    "NORMAL",
    "NORMAL",
    "NORMAL",
    "BANNED",
    "DEACTIVATE",
]

PRODUCT_TYPE = [
    "VEGETABLE",
    "MEAT",
    "SEASON",
    "MEAKIT",
]

PRODUCT_STATUS = [
    "IN_STOCK",
    "IN_STOCK",
    "IN_STOCK",
    "OUT_OF_STOCK",
    "NO_LONGER_IN_SALE",
]

PRODUCT_TYPE_FOOD_NAMES = {
    "VEGETABLE": [
        "carrot",
        "broccoli",
        "spinach",
        "potato",
        "tomato",
        "cucumber",
        "lettuce",
        "pepper",
        "onion",
        "garlic",
        "peas",
        "corn",
        "cabbage",
        "zucchini",
    ],
    "MEAT": [
        "chicken",
        "beef",
        "pork",
        "lamb",
        "turkey",
        "duck",
        "bacon",
        "sausage",
        "ham",
        "salami",
        "venison",
        "rabbit",
        "goose",
        "quail",
    ],
    "SEASON": [
        "salt",
        "pepper",
        "paprika",
        "cumin",
        "oregano",
        "basil",
        "thyme",
        "rosemary",
        "cinnamon",
        "nutmeg",
        "clove",
        "coriander",
        "turmeric",
        "ginger",
    ],
    "MEALKIT": [
        "spaghetti_bolognese",
        "chicken_curry",
        "taco",
        "sushi",
        "pizza",
        "burger",
        "salad",
        "bbq",
        "pasta",
        "soup",
        "stir_fry",
        "wrap",
        "sandwich",
        "breakfast",
    ],
}

created_user_id = []
created_staff_id = []

for _ in tqdm(range(USER_AMOUNT)):
    username = fake.user_name()
    id = str(uuid.uuid4())
    created_user_id.append(id)
    data = {
        "id": id,
        "email": fake.email(),
        "username": username,
        "password": pwd_context.hash(username),
        "status": random.choice(USER_STATUS),
        "address": fake.address(),
        "profile_pic_uri": PROFILE_URI,
        "profile_description": fake.sentence(),
        "phone": fake.phone_number(),
        "token": "",
        "bookmarked_posts": [],
    }
    conn.execute(
        USER_STATEMENT,
        data,
    )

for _ in tqdm(range(STAFF_AMOUNT)):
    username = fake.user_name()
    id = str(uuid.uuid4())
    created_staff_id.append(id)

    account_data = {
        "id": id,
        "username": username,
        "password": pwd_context.hash(username),
        "type": random.choice(["MANAGER", "STAFF"]),
        "status": random.choice(["ACTIVE", "DISABLE"]),
        "token": "",
    }

    info_data = {
        "account_id": id,
        "ssn": fake.ssn(),
        "phonenumber": fake.phone_number(),
        "realname": fake.name(),
        "email": fake.email(),
        "dob": fake.date_of_birth(),
    }

    conn.execute(STAFF_STATMENT, account_data)
    conn.execute(EMPLOYEE_INFO_STATEMENT, info_data)


for i, (cate, foods) in enumerate(PRODUCT_TYPE_FOOD_NAMES.items()):
    for food in foods:
        product_id = f"{cate}_{food}"

        current_price = round(random.uniform(14.2, 142.0), 2)
        current_sale = round(random.uniform(0.0, 50.0), 2)

        product_data = {
            "id": product_id,
            "product_name": food,
            "available_quantity": random.randint(14, 142),
            "product_types": cate,
            "product_status": random.choice(PRODUCT_STATUS),
            "image_url": fake.image_url(),
            "price": current_price,
            "sale_percent": current_sale,
        }

        conn.execute(
            PRODUCT_STATEMENT,
            product_data,
        )

        num_price_entries = random.randint(
            1,
            VARIANCE_OF_PRICE,
        )

        price_history_data = {
            "price": current_price,
            "sale_percent": current_sale,
            "date": datetime.now(),
            "product_id": product_id,
        }
        conn.execute(
            PRODUCT_PRICE_HISTORY_STATEMENT,
            price_history_data,
        )
        for _ in range(num_price_entries):
            price_history_data = {
                "price": round(random.uniform(14.2, 142.0), 2),
                "sale_percent": round(random.uniform(0.0, 50.0), 2),
                "date": fake.date_time_between(
                    start_date="-2y",
                    end_date="now",
                ),
                "product_id": product_id,
            }
            conn.execute(
                PRODUCT_PRICE_HISTORY_STATEMENT,
                price_history_data,
            )

        product_doc_data = {
            "id": product_id,
            "description": fake.text(),
            "images_url": random.choices(PRODUCT_IMAGES, k=3),
            "infos": json.dumps({fake.word(): fake.word() for _ in range(5)}),
            "ingredients": [fake.word() for _ in range(5)],
            "instructions": [fake.sentence() for _ in range(3)],
            "article_md": fake.text(),
            "day_before_expiry": random.randint(142, 365),
        }

        conn.execute(
            PRODUCT_DOC_STATEMENT,
            product_doc_data,
        )


conn.commit()
conn.close()
