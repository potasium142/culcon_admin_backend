# test_data.py
from datetime import date
from datetime import datetime
from dtos.request.product import *
import db.postgresql.models.product as prod
from db.postgresql.models.blog import ProductDoc
def ex_product_creation_dto_1():
    return ProductCreation(
        product_name="Test Product",
        product_type=prod.ProductType.VEGETABLE,
        description="A very tasty snack",
        infos={"detail": "Some basic info"}, 
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],  
        day_before_expiry=3
    )

def ex_product_creation_dto_1_fail_1():
    return ProductCreation(
        product_name="Test Product#",
        product_type=prod.ProductType.VEGETABLE,
        description="A very tasty snack",
        infos={"detail": "Some basic info"}, 
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],  
        day_before_expiry=3
    )

def ex_product_creation_dto_1_fail_2():
    return ProductCreation(
        product_name="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        product_type=prod.ProductType.VEGETABLE,
        description="A very tasty snack",
        infos={"detail": "Some basic info"}, 
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],  
        day_before_expiry=3
    )

def ex_product_creation_dto_1_fail_3():
    return ProductCreation(
        product_name="Test Product",
        product_type=prod.ProductType.VEGETABLE,
        description="",
        infos={"detail": "Some basic info"}, 
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],  
        day_before_expiry=3
    )

def ex_product_creation_dto_1_fail_4():
    return ProductCreation(
        product_name="Test Product",
        product_type=prod.ProductType.VEGETABLE,
        description="A very tasty snack",
        infos={"detail": "Some basic info"}, 
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],  
        day_before_expiry=0
    )

def ex_product_creation_dto_1_null():
    return ProductCreation(
        product_name=None,
        product_type=None,
        description=None,
        infos=None, 
        article_md=None,
        instructions=None,  
        day_before_expiry=None
    )

def ex_mealkit_creation_dto_1():
    return MealKitCreation(
        product_name="Test MealKit",
        product_type=prod.ProductType.MEALKIT,  # Explicitly specify the product type
        day_before_expiry=3,
        description="A very tasty snack",
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],
        infos={"detail": "Some basic info"},
        ingredients={
            "Rice_ID": 200,
            "Tofu_ID": 100
        }
    )

    

def ex_mealkit_creation_dto_empty_1():
    return MealKitCreation(
        product_name="Test MealKit",
        product_type=prod.ProductType.MEALKIT,  
        day_before_expiry=3,
        description="A very tasty snack",
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],
        infos={"detail": "Some basic info"},
        ingredients={
        
        }
    )


def ex_mealkit_creation_dto_2():
    return MealKitCreation(
        product_name="Test MealKit",
        product_type=prod.ProductType.MEALKIT,  
        day_before_expiry=3,
        description="A very tasty snack",
        article_md="Some markdown",
        instructions=["Cook for 5 mins"],
        infos={"detail": "Some basic info"},
        ingredients={
            "Rice_ID": 200
        }
    )


def preb_product_table_1():
    return prod.Product(
        id="Rice_ID", 
        product_name="Rice",
        available_quantity=1000,
        product_types=prod.ProductType.VEGETABLE,  # Assuming the correct type
        product_status=prod.ProductStatus.IN_STOCK,  # Assuming the correct status
        image_url="url_to_image",
        price=5.0
    )

# Function to create a product price history instance
def preb_product_price_history_table_1():
    return prod.ProductPriceHistory(
        price=5.0,  
        sale_percent=0.0,
        date=datetime.now(),  
        product_id="Rice_ID" 
    )

def preb_product_doc_table_1():
    return ProductDoc(
        id="Rice_ID",
        description="Old description",
        instructions="Old instructions",
        infos=["old", "info"],
        article_md="old article",
        day_before_expiry=5,
        images_url=[]
    )


def preb_product_embeded_table_1():
    return prod.ProductEmbedding(
        id="Rice_ID",
        description_embed=[0.1] * 768,  
        images_embed_yolo=[0.1] * 512,
        images_embed_clip=[0.1] * 768,
    )

def ex_product_update_dto_1():
    return ProductUpdate(
        description="Updated description",
        instructions=["Step 1", "Step 2"],  # now a list of strings
        infos={"note": "updated", "detail": "info"},  # now a dict
        article_md="updated article",
        day_before_expiry=10,
    )

def ex_product_update_dto_1_fail_1():
    return ProductUpdate(
        description="",
        instructions=["Step 1", "Step 2"],  # now a list of strings
        infos={"note": "updated", "detail": "info"},  # now a dict
        article_md="updated article",
        day_before_expiry=10,
    )

def ex_product_update_dto_1_fail_2():
    return ProductUpdate(
        description="Updated description",
        instructions=["Step 1", "Step 2"],  # now a list of strings
        infos={"note": "updated", "detail": "info"},  # now a dict
        article_md="updated article",
        day_before_expiry=0,
    )

def ex_product_update_dto_1_null():
    return ProductUpdate(
        description=None,
        instructions=None,  # now a list of strings
        infos=None,  # now a dict
        article_md=None,
        day_before_expiry=None,
    )

def ex_mealkit_update_dto_1():
    return  MealKitUpdate(
        description="Fresh meal description",
        day_before_expiry=5,
        instructions=["Cook for 5 mins"],
        article_md="Updated article",
        infos={"nutrition": "high"},
        ingredients={"Rice_ID": 2}
    )

def ex_mealkit_update_dto_1_fail_1():
    return  MealKitUpdate(
        description="Fresh meal description",
        day_before_expiry=5,
        instructions=["Cook for 5 mins"],
        article_md="Updated article",
        infos={"nutrition": "high"},
        ingredients={"none": 2}
    )
