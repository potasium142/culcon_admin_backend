import pytest
import httpx
import json
import os
from .data import mealkit_valid_data, main_image_path_mealkit, additional_image_path_mealkit,mealkit_no_article
from . import data


BASE_URL = "https://culcon-admin-backend-813020060204.asia-northeast3.run.app/api"


@pytest.fixture
def client():
    """Fixture tạo HTTP client cho mỗi test"""
    return httpx.Client(base_url=BASE_URL, timeout=10)


@pytest.fixture
def auth_token(client):
    """Fixture đăng nhập và lấy token"""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "123456"}  
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_login_invalid_credentials(client):
    """Test đăng nhập với tài khoản sai"""
    response = client.post(
        "/auth/login", data={"username": "wrong_user", "password": "wrong_pass"}  
    )
    assert response.status_code == 400

def test_login_blankUsername(client):
    """Test đăng nhập với tài khoản ko có username"""
    response = client.post(
        "/auth/login", data={"username": "", "password": "123456"}  
    )
    assert response.status_code == 400

def test_login_blankPassword(client):
    """Test đăng nhập với tài khoản ko có pasword"""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": ""}  
    )
    assert response.status_code == 400

def test_login_valid_credentials(client):
    """Test đăng nhập thành công (Cần user hợp lệ)"""
    valid_credentials = {"username": "admin", "password": "123456"}
    response = client.post("/auth/login", data=valid_credentials)  # Sửa thành data=
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token is not None

def test_profile_no_token(client):
    """Test lấy profile mà không có token"""
    response = client.get("/auth/profile")
    assert response.status_code == 401  # Unauthorized

def test_permission_test_no_token(client):
    """Test truy cập endpoint yêu cầu quyền mà không có token"""
    response = client.get("/auth/permission_test")
    assert response.status_code == 401

def test_coupon_fetch_all(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/coupon/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        }
    )
    assert response.status_code == 200

def test_coupon_fetch_sucess(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/coupon/fetch",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"id": "CP01"},
    )
    assert response.status_code == 200

def test_coupon_fetch_wrongId(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/coupon/fetch",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"id": "WrongID"},
    )
    assert response.status_code == 200

def test_coupon_create_sucess(client, auth_token):
    response = client.post(
        f"{BASE_URL}/manager/coupon/create",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        json={
  "expire_date": "202-04-10",
  "sale_percent": 10,
  "usage_amount": 5,
  "minimum_price": 100,
  "id": "CPTEST"
},
    )
    assert response.status_code == 200

def test_coupon_create_missing_field(client, auth_token):
    response = client.post(
        f"{BASE_URL}/manager/coupon/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sale_percent": 10,
            "usage_amount": 5,
            
        },
    )
    assert response.status_code == 422  

def test_coupon_create_duplicate_id(client, auth_token):
    response2 = client.post(
        f"{BASE_URL}/manager/coupon/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "expire_date": "2026-04-20T00:00:00",
            "sale_percent": 5,
            "usage_amount": 1,
            "minimum_price": 50,
            "id": "CPTEST"
        },
    )
    assert response2.status_code == 500

def test_coupon_create_no_token(client):
    response = client.post(
        f"{BASE_URL}/manager/coupon/create",
        json={
            "expire_date": "2025-04-10T00:00:00",
            "sale_percent": 10,
            "usage_amount": 5,
            "minimum_price": 100,
            "id": "CPNOTOKEN"
        },
    )
    assert response.status_code == 401  # Unauthorized

def test_coupon_create_invalid_data(client, auth_token):
    response = client.post(
        f"{BASE_URL}/manager/coupon/create",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "expire_date": "2025-04-10T00:00:00",
            "sale_percent": -5,
            "usage_amount": -10,
            "minimum_price": -100,
            "id": "CPINVALID"
        },
    )
    assert response.status_code in [400, 422]

def test_coupon_disable_sucess(client, authtoken):
    test_data = getattr(data, "coupon_disable_sucess")
    response = client.get(
        f"{BASE_URL}/manager/coupon/disable",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=test_data
    )

    assert response.status_code == 200

def test_product_create_success(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cabbage.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cabbage1.jpg"
    product_detail = {
        "product_name": "Dalat Cabbage",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean cabbage",
        "article_md": "Useful information about cabbage",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 200

def test_product_fetch_TakeOneProduct(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ và tham số query"""
    params = {
        "prod_id": "VEG_Potato"         
    }

    response = client.get(
        "/general/product/fetch",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(data, list)  # Tuỳ vào API trả ra kiểu gì
    print("Response:", data)

def test_product_fetch_all_success(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ"""
    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200

def test_product_fetch_all_successwithpagination(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ và tham số query"""
    params = {
        "index": 1,
        "size": 7
    }

    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )
    assert response.status_code == 200

def test_product_fetch_all_success(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ và tham số query"""
    params = {
        "type": "VEG",               
        "index": 0,
        "size": 7
    }

    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(data, list)  
    print("Response:", data)

def test_product_fetch_ProductNotExist(client, auth_token):
    """test ingredient không tồn tại"""
    response = client.get(
        f"{BASE_URL}/general/product/fetch",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"prod_id": "VEG_NotExist"},
    )
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
    assert response.status_code == 500

def test_product_fetch_ingredient(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/product/fetch/ingredients",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"prod_id": "GarlicBeefStirFry"},
    )
    assert response.status_code == 200

def test_product_fetch_ingredient_not_exist(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/product/fetch/ingredients",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"prod_id": "Not Exist"},
    )
    assert response.status_code == 500

def test_product_create_has_existed(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat tomatoes",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean tomatoes",
        "article_md": "Useful information about tomatoes",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 500
    data = response.json()
    assert "message" in data
    assert data["message"] == "Product is already exists"

def test_product_create_invalid_productype(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat milk",
        "product_type": "invalid",
        "day_before_expiry": 5,
        "description": "Organic clean milk",
        "article_md": "Useful information about milk",
        "instructions": [
            "drink",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500ml"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_create_blank_name(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean milk",
        "article_md": "Useful information about milk",
        "instructions": [
            "drink",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500ml"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 500
    data = response.json()
    assert "message" in data
    assert data["message"] == "Product name is not valid"

def test_product_create_dayBeaforeExpiryisNull(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat cabagge",
        "product_type": "VEG",
        "day_before_expiry": "",
        "description": "Organic clean cabagge",
        "article_md": "Useful information about cabagge",
        "instructions": [
            "drink",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500ml"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_create_descriptionIsNull(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat cabagge 0",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "",
        "article_md": "Useful information about cabagge",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }
    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422
    
def test_product_create_article_mdIsNull(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat cabagge 1",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean cabagge",
        "article_md": "",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }
    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_create_dayBeaforeExpiryisNull(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat cabagge",
        "product_type": "VEG",
        "day_before_expiry": "",
        "description": "Organic clean milk",
        "article_md": "Useful information about milk",
        "instructions": [
            "drink",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500ml"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_create_dayBeaforeExpiryisNegative(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat cabbage",
        "product_type": "VEG",
        "day_before_expiry": -1,
        "description": "Organic clean milk",
        "article_md": "Useful information about milk",
        "instructions": [
            "drink",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500ml"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 500
    data = response.json()
    assert "message" in data
    assert data["message"] == "day_before_expiry is not valid"

def test_product_create_main_imageIsNotImgFile(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/test img.txt"
    additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


    product_detail = {
        "product_name": "Dalat imageIsNotImgFile",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean tomatoes",
        "article_md": "Useful information about tomatoes",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_create_main_additional_imagesIsNotImgFile(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"
    additional_image_path = "test/IntegartionTest/image_test/test img.txt"


    product_detail = {
        "product_name": "Dalat additional_imageIsNotImgFile",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean tomatoes",
        "article_md": "Useful information about tomatoes",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_product_update_info(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info")
    response = client.post(
            f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_data
        )
    assert response.status_code == 200

def test_product_update_info_BlankExpiredDay(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_blankDayExpiry")
    response = client.post(
            f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "prod_id": (None, json.dumps(test_data), "application/json")
            }
        )
    assert response.status_code == 422
def test_product_update_info_ExpiredDayEualZero(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_ExpiredDayEualZero")
    response = client.post(
            f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "prod_id": (None, json.dumps(test_data), "application/json")
            }
        )
    assert response.status_code == 422

def test_product_update_info_ExpiredDayNegative(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_ExpiredDayNegative")
    response = client.post(
            f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "prod_id": (None, json.dumps(test_data), "application/json")
            }
        )
    assert response.status_code == 422

def test_product_update_info_BlankKeyInfo(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_BlankKeyInfo")
    response = client.post(
            f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "prod_id": (None, json.dumps(test_data), "application/json")
            }
        )
    assert response.status_code == 422

def test_product_update_status_OutOfStock(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "OUT_OF_STOCK"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def test_product_update_status_NoLongerInSale(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "NO_LONGER_IN_SALE"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200


def test_product_update_status_Instock(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "IN_STOCK"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def test_product_update_quantity_success(client, auth_token):
    update_data = getattr(data, "product_update_quantity_valid")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_product_update_quantity_missing_price(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_price")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422

def test_product_update_quantity_missing_prodId(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_prodId")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 500

def test_product_update_quantity_missing_quantity(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_quantity")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422

def test_product_update_quantity_inPriceNegative(client, auth_token):
    update_data = getattr(data, "product_update_quantity_inPriceNegative")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422

def test_product_update_quantity_QuantityNegative(client, auth_token):
    update_data = getattr(data, "product_update_quantity_quantityNegative")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422

def test_product_update_price_valid(client, auth_token):
    update_data = getattr(data, "product_update_price_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def test_product_update_price_Negative_salePercent(client, auth_token):
    update_data = getattr(data, "product_update_price_Negative_salePercent")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 422

def test_product_update_price_blank_productId(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_productId")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 500

def test_product_update_price_blank_price(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_price")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 500

def test_product_update_price_blank_sale_percent(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_sale_percent")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 422

def product_history_stock_valid(client, auth_token):
    update_data = getattr(data, "product_history_stock_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def product_history_stock_prodId_notExist(client, auth_token):
    update_data = getattr(data, "product_history_stock_prodId_notExist")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def product_history_stock_valid(client, auth_token):
    update_data = getattr(data, "product_history_price_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def product_history_stock_prodId_notExist(client, auth_token):
    update_data = getattr(data, "product_history_price_prodId_notExist")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200

def test_mealkit_create_success(client, auth_token):
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(mealkit_valid_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 200

def test_mealkit_create_hadExist(client, auth_token):
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(mealkit_valid_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 500

def test_product_create_main_additional_imagesIsNotImgFile(client, auth_token):
    main_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"
    additional_image_path = "test/IntegartionTest/image_test/test img.txt"


    product_detail = {
        "product_name": "Dalat additional_imageIsNotImgFile",
        "product_type": "VEG",
        "day_before_expiry": 5,
        "description": "Organic clean tomatoes",
        "article_md": "Useful information about tomatoes",
        "instructions": [
            "Wash before use",
            "Store in refrigerator"
        ],
        "infos": {
            "Weight": "500g"
        }
    }

    with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(product_detail), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )

    assert response.status_code == 422

def test_mealkit_create_blankMealkitName(client, auth_token):
    test_data = getattr(data, "mealkit_no_product_name")
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 500

def test_mealkit_create_blankProductType(client, auth_token):
    test_data = getattr(data, "mealkit_no_product_type")
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 422

def test_mealkit_create_blankDescription(client, auth_token):
    test_data = getattr(data, "mealkit_no_desc")
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 500

def test_mealkit_create_blankArticle(client, auth_token):
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(mealkit_no_article), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 500

def test_mealkit_create_blankInfo(client, auth_token):
    test_data = getattr(data, "mealkit_no_infos")
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 500

def test_mealkit_create_blankInfo(client, auth_token):
    test_data = getattr(data, "mealkit_no_ingredients")
    with open(main_image_path_mealkit, "rb") as main_img, open(additional_image_path_mealkit, "rb") as extra_img:
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            }
        )
    assert response.status_code == 422

def test_fetch_ingredients_success(client, auth_token):
#     test_data = getattr(data, "fetch_ingredients_valid_params")
#     response = client.get(
#         f"{BASE_URL}/staff/mealkit/create/fetch/ingredients",
#         headers={"Authorization": f"Bearer {auth_token}"},
#         params=test_data
#     )

#     assert response.status_code == 200
#     json_data = response.json()
#     assert "content" in json_data
#     assert isinstance(json_data["content"], list)






