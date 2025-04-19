import pytest
import httpx
import json
from .data import (
    mealkit_valid_data,
    main_image_path_mealkit,
    additional_image_path_mealkit,
    mealkit_no_article,
    main_image_path_blog,
)
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


@pytest.fixture
def auth_token_shipper(client):
    """Fixture đăng nhập và lấy token"""
    response = client.post(
        "/auth/login", data={"username": "hinessarah", "password": "123456"}
    )
    assert response.status_code == 200
    return response.json()["access_token_shipper"]


def test_login_invalid_credentials(client):
    """Test đăng nhập với tài khoản sai"""
    response = client.post(
        "/auth/login", data={"username": "wrong_user", "password": "wrong_pass"}
    )
    assert response.status_code == 400


def test_login_blankUsername(client):
    """Test đăng nhập với tài khoản ko có username"""
    response = client.post("/auth/login", data={"username": "", "password": "123456"})
    assert response.status_code == 400


def test_login_blankPassword(client):
    """Test đăng nhập với tài khoản ko có pasword"""
    response = client.post("/auth/login", data={"username": "admin", "password": ""})
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
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
    )
    assert response.status_code == 200


def test_coupon_fetch_sucess(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/coupon/fetch",
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
        params={"id": "CP01"},
    )
    assert response.status_code == 200


def test_coupon_fetch_wrongId(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/coupon/fetch",
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
        params={"id": "WrongID"},
    )
    assert response.status_code == 200


# def test_coupon_create_sucess(client, auth_token):
#     test_data = data.test_coupon_create_success
#     response = client.post(
#         f"{BASE_URL}/manager/coupon/create",
#         headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
#         json=test_data,
#     )
#     assert response.status_code == 200


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
            "id": "CPTEST",
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
            "id": "CPNOTOKEN",
        },
    )
    assert response.status_code == 401  # Unauthorized


# def test_coupon_create_invalid_data(client, auth_token):
#     response = client.post(
#         f"{BASE_URL}/manager/coupon/create",
#         headers={"Authorization": f"Bearer {auth_token}"},
#         json={
#             "expire_date": "2026-04-10T00:00:00",
#             "sale_percent": -5,
#             "usage_amount": -10,
#             "minimum_price": -100,
#             "id": "CPINVALID_ID"
#         },
#     )
#     assert response.status_code in [400, 422]


def test_coupon_disable_sucess(client, auth_token):
    test_data = getattr(data, "coupon_disable_sucess")
    response = client.delete(
        f"{BASE_URL}/manager/coupon/disable",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=test_data,
    )

    assert response.status_code == 200


# def test_product_create_success(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cabbage.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/cabbage1.jpg"
#     product_detail = {
#         "product_name": "Dalat Spinach",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "Organic clean Spinach",
#         "article_md": "Useful information about Spinach",
#         "instructions": ["Wash before use", "Store in refrigerator"],
#         "infos": {"Weight": "500g"},
#     }

#     with (
#         open(main_image_path, "rb") as main_img,
#         open(additional_image_path, "rb") as extra_img,
#     ):
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (
#                     None,
#                     json.dumps(product_detail),
#                     "application/json",
#                 ),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             },
#         )

#     assert response.status_code == 200


def test_product_fetch_TakeOneProduct(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ và tham số query"""
    params = {"prod_id": "VEG_Potato"}

    response = client.get(
        "/general/product/fetch",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(
        data, list
    )  # Tuỳ vào API trả ra kiểu gì
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
    params = {"index": 1, "size": 7}

    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params,
    )
    assert response.status_code == 200


def test_product_fetch_all_success(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ và tham số query"""
    params = {"type": "VEG", "index": 0, "size": 7}

    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) or isinstance(data, list)
    print("Response:", data)


def test_product_fetch_ProductNotExist(client, auth_token):
    """test ingredient không tồn tại"""
    response = client.get(
        f"{BASE_URL}/general/product/fetch",
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
        params={"prod_id": "VEG_NotExist"},
    )
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
    assert response.status_code == 500


def test_product_fetch_ingredient(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/product/fetch/ingredients",
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
        params={"prod_id": "MK_GarlicBeefStirFry"},
    )
    assert response.status_code == 200


def test_product_fetch_ingredient_not_exist(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/product/fetch/ingredients",
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
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
        "instructions": ["Wash before use", "Store in refrigerator"],
        "infos": {"Weight": "500g"},
    }

    with (
        open(main_image_path, "rb") as main_img,
        open(additional_image_path, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(product_detail),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
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
        "instructions": ["drink", "Store in refrigerator"],
        "infos": {"Weight": "500ml"},
    }

    with (
        open(main_image_path, "rb") as main_img,
        open(additional_image_path, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(product_detail),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
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
        "instructions": ["drink", "Store in refrigerator"],
        "infos": {"Weight": "500ml"},
    }

    with (
        open(main_image_path, "rb") as main_img,
        open(additional_image_path, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(product_detail),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
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
        "instructions": ["drink", "Store in refrigerator"],
        "infos": {"Weight": "500ml"},
    }

    with (
        open(main_image_path, "rb") as main_img,
        open(additional_image_path, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/product/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(product_detail),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )

    assert response.status_code == 422


# def test_product_create_descriptionIsNull(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


#     product_detail = {
#         "product_name": "Dalat cabagge 0",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "",
#         "article_md": "Useful information about cabagge",
#         "instructions": [
#             "Wash before use",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500g"
#         }
#     }
#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422

# def test_product_create_article_mdIsNull(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


#     product_detail = {
#         "product_name": "Dalat cabagge 1",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "Organic clean cabagge",
#         "article_md": "",
#         "instructions": [
#             "Wash before use",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500g"
#         }
#     }
#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422

# def test_product_create_dayBeaforeExpiryisNull(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


#     product_detail = {
#         "product_name": "Dalat cabagge",
#         "product_type": "VEG",
#         "day_before_expiry": "",
#         "description": "Organic clean milk",
#         "article_md": "Useful information about milk",
#         "instructions": [
#             "drink",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500ml"
#         }
#     }

#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422

# def test_product_create_dayBeaforeExpiryisNegative(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


#     product_detail = {
#         "product_name": "Dalat cabbage",
#         "product_type": "VEG",
#         "day_before_expiry": -1,
#         "description": "Organic clean milk",
#         "article_md": "Useful information about milk",
#         "instructions": [
#             "drink",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500ml"
#         }
#     }

#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422

# def test_product_create_main_imageIsNotImgFile(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/test img.txt"
#     additional_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"


#     product_detail = {
#         "product_name": "Dalat imageIsNotImgFile",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "Organic clean tomatoes",
#         "article_md": "Useful information about tomatoes",
#         "instructions": [
#             "Wash before use",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500g"
#         }
#     }

#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422

# def test_product_create_main_additional_imagesIsNotImgFile(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/test img.txt"


#     product_detail = {
#         "product_name": "Dalat additional_imageIsNotImgFile",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "Organic clean tomatoes",
#         "article_md": "Useful information about tomatoes",
#         "instructions": [
#             "Wash before use",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500g"
#         }
#     }

#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422


def test_product_update_info(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info")
    response = client.post(
        f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_data,
    )
    assert response.status_code == 200


def test_product_update_info_BlankExpiredDay(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_blankDayExpiry")
    response = client.post(
        f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"prod_id": (None, json.dumps(test_data), "application/json")},
    )
    assert response.status_code == 422


def test_product_update_info_ExpiredDayEualZero(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_ExpiredDayEualZero")
    response = client.post(
        f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"prod_id": (None, json.dumps(test_data), "application/json")},
    )
    assert response.status_code == 422


# def test_product_update_info_ExpiredDayNegative(client, auth_token):
#     valid_prod_id = "VEG_Potato"
#     test_data = getattr(data, "product_update_info_ExpiredDayNegative")
#     response = client.post(
#             f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "prod_id": (None, json.dumps(test_data), "application/json")
#             }
#         )
#     assert response.status_code == 422


def test_product_update_info_BlankKeyInfo(client, auth_token):
    valid_prod_id = "VEG_Potato"
    test_data = getattr(data, "product_update_info_BlankKeyInfo")
    response = client.post(
        f"{BASE_URL}/staff/product/update/info/prod?prod_id={valid_prod_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"prod_id": (None, json.dumps(test_data), "application/json")},
    )
    assert response.status_code == 422


def test_product_update_status_OutOfStock(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "OUT_OF_STOCK"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def test_product_update_status_NoLongerInSale(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "NO_LONGER_IN_SALE"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def test_product_update_status_Instock(client, auth_token):
    valid_prod_id = "VEG_Potato"
    new_status = "IN_STOCK"

    response = client.patch(
        f"{BASE_URL}/staff/product/update/status?prod_id={valid_prod_id}&status={new_status}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def test_product_update_quantity_success(client, auth_token):
    update_data = getattr(data, "product_update_quantity_valid")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200


def test_product_update_quantity_missing_price(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_price")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 422


def test_product_update_quantity_missing_prodId(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_prodId")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 500


def test_product_update_quantity_missing_quantity(client, auth_token):
    update_data = getattr(data, "product_update_quantity_missing_quantity")

    response = client.patch(
        f"{BASE_URL}/staff/product/update/quantity"
        f"?prod_id={update_data['prod_id']}"
        f"&quantity={update_data['quantity']}"
        f"&in_price={update_data['in_price']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 422


# def test_product_update_quantity_inPriceNegative(client, auth_token):
#     update_data = getattr(data, "product_update_quantity_inPriceNegative")

#     response = client.patch(
#         f"{BASE_URL}/staff/product/update/quantity"
#         f"?prod_id={update_data['prod_id']}"
#         f"&quantity={update_data['quantity']}"
#         f"&in_price={update_data['in_price']}",
#         headers={"Authorization": f"Bearer {auth_token}"}
#     )
#     assert response.status_code == 422

# def test_product_update_quantity_QuantityNegative(client, auth_token):
#     update_data = getattr(data, "product_update_quantity_quantityNegative")

#     response = client.patch(
#         f"{BASE_URL}/staff/product/update/quantity"
#         f"?prod_id={update_data['prod_id']}"
#         f"&quantity={update_data['quantity']}"
#         f"&in_price={update_data['in_price']}",
#         headers={"Authorization": f"Bearer {auth_token}"}
#     )
#     assert response.status_code == 422


def test_product_update_price_valid(client, auth_token):
    update_data = getattr(data, "product_update_price_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


# def test_product_update_price_Negative_salePercent(client, auth_token):
#     update_data = getattr(data, "product_update__price_Negative_salePercent")

#     response = client.put(
#         f"{BASE_URL}/staff/product/update/price"
#         f"?product_id={update_data['product_id']}"
#         f"&price={update_data['price']}"
#         f"&sale_percent={update_data['sale_percent']}",
#         headers={"Authorization": f"Bearer {auth_token}"}
#     )

#     assert response.status_code == 422


def test_product_update_price_blank_productId(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_productId")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 500


def test_product_update_price_blank_price(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_price")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 500


def test_product_update_price_blank_sale_percent(client, auth_token):
    update_data = getattr(data, "product_update_price_blank_sale_percent")

    response = client.put(
        f"{BASE_URL}/staff/product/update/price"
        f"?product_id={update_data['product_id']}"
        f"&price={update_data['price']}"
        f"&sale_percent={update_data['sale_percent']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422


def product_history_stock_valid(client, auth_token):
    update_data = getattr(data, "product_history_stock_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def product_history_stock_prodId_notExist(client, auth_token):
    update_data = getattr(data, "product_history_stock_prodId_notExist")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def product_history_stock_valid(client, auth_token):
    update_data = getattr(data, "product_history_price_valid")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200


def product_history_stock_prodId_notExist(client, auth_token):
    update_data = getattr(data, "product_history_price_prodId_notExist")

    response = client.put(
        f"{BASE_URL}/staff/product/history/stock"
        f"?product_id={update_data['product_id']}"
        f"&index={update_data['index']}"
        f"&size={update_data['size']}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200

    # def test_mealkit_create_success(client, auth_token):
    #     test_data = json.dumps(mealkit_valid_data)  # đảm bảo chuyển đúng sang JSON string

    #     with (
    #         open(main_image_path_mealkit, "rb") as main_img,
    #         open(additional_image_path_mealkit, "rb") as extra_img,
    #     ):
    #         files = [
    #             ("product_detail", (None, test_data, "application/json")),
    #             ("main_image", ("main_image.jpg", main_img, "image/jpeg")),
    #             ("additional_images", ("extra_image.jpg", extra_img, "image/jpeg")),
    #         ]

    #         response = client.post(
    #             f"{BASE_URL}/staff/mealkit/create",
    #             headers={"Authorization": f"Bearer {auth_token}"},
    #             files=files,
    #         )

    print("Response status:", response.status_code)
    print("Response body:", response.text)
    assert response.status_code == 200


def test_mealkit_create_invalid_ingredient(client, auth_token):
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(mealkit_valid_data),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


def test_mealkit_create_hadExist(client, auth_token):
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(mealkit_valid_data),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


# def test_product_create_main_additional_imagesIsNotImgFile(client, auth_token):
#     main_image_path = "test/IntegartionTest/image_test/cachuadalat1.jpg"
#     additional_image_path = "test/IntegartionTest/image_test/test img.txt"


#     product_detail = {
#         "product_name": "ingredient additionalimageIsNotImgFile",
#         "product_type": "VEG",
#         "day_before_expiry": 5,
#         "description": "Organic",
#         "article_md": "Useful",
#         "instructions": [
#             "Wash before use",
#             "Store in refrigerator"
#         ],
#         "infos": {
#             "Weight": "500g"
#         }
#     }

#     with open(main_image_path, "rb") as main_img, open(additional_image_path, "rb") as extra_img:
#         response = client.post(
#             f"{BASE_URL}/staff/product/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "product_detail": (None, json.dumps(product_detail), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
#                 "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
#             }
#         )

#     assert response.status_code == 422


def test_mealkit_create_blankMealkitName(client, auth_token):
    test_data = getattr(data, "mealkit_no_product_name")
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


def test_mealkit_create_blankProductType(client, auth_token):
    test_data = getattr(data, "mealkit_no_product_type")
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 422


def test_mealkit_create_blankDescription(client, auth_token):
    test_data = getattr(data, "mealkit_no_desc")
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


def test_mealkit_create_blankArticle(client, auth_token):
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (
                    None,
                    json.dumps(mealkit_no_article),
                    "application/json",
                ),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


def test_mealkit_create_blankInfo(client, auth_token):
    test_data = getattr(data, "mealkit_no_infos")
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 500


def test_mealkit_create_blankInfo(client, auth_token):
    test_data = getattr(data, "mealkit_no_ingredients")
    with (
        open(main_image_path_mealkit, "rb") as main_img,
        open(additional_image_path_mealkit, "rb") as extra_img,
    ):
        response = client.post(
            f"{BASE_URL}/staff/mealkit/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "product_detail": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
                "additional_images": ("test_image_extra.jpg", extra_img, "image/jpeg"),
            },
        )
    assert response.status_code == 422


def test_fetch_ingredients_success(client, auth_token):
    test_data = getattr(data, "fetch_ingredients_valid_params")
    response = client.get(
        f"{BASE_URL}/staff/mealkit/create/fetch/ingredients",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=test_data,
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "content" in json_data
    assert isinstance(json_data["content"], list)


# def test_create_account_success(client, auth_token):
#     test_data = getattr(data, "create_account_manager_success")
#     response = client.post(
#         f"{BASE_URL}/manager/create/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json",
#         },
#         json=test_data,
#     )

#     assert response.status_code == 200


def test_create_account_success(client, auth_token):
    test_data = getattr(data, "create_account_manager_success")
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json=test_data,
    )

    assert response.status_code == 200


def test_create_account_missing_username(client, auth_token):
    test_data = data.create_account_missing_username
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_data,
    )
    assert response.status_code == 422


def test_create_account_duplicate_username(client, auth_token):
    test_data = data.create_account_manager_success  # dùng lại username đã tồn tại
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_data,
    )
    assert response.status_code in [400, 409, 500]


def test_create_account_invalid_email(client, auth_token):
    test_data = data.create_account_invalid_email
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_data,
    )
    assert response.status_code == 500


def test_create_account_no_token(client):
    test_data = data.create_account_manager_success
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={"Content-Type": "application/json"},
        json=test_data,
    )
    assert response.status_code == 401


# def test_create_account_invalid_ssn(client, auth_token):
#     test_data = getattr(data, "test_create_account_invalid_ssn")
#     response = client.post(
#         f"{BASE_URL}/manager/create/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         json=test_data
#     )

#     assert response.status_code == 500


def test_create_account_duplicate_ssn(client, auth_token):
    test_data = getattr(data, "test_create_account_duplicate_ssn")
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json=test_data,
    )

    assert response.status_code == 500


def test_create_account_invalid_phoneNumber(client, auth_token):
    test_data = getattr(data, "test_create_account_invalid_phoneNumber")
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json=test_data,
    )

    assert response.status_code == 500


def test_create_account_exist_phoneNumber(client, auth_token):
    test_data = getattr(data, "test_create_account_exist_phoneNumber")
    response = client.post(
        f"{BASE_URL}/manager/create/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json=test_data,
    )

    assert response.status_code == 500


# def test_create_accout_underage_dob(client, auth_token):
#     test_data = data.test_create_accout_underage_dob

#     response = client.post(
#         f"{BASE_URL}/manager/create/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         json=test_data
#     )

#     assert response.status_code == 500


def test_staff_fetch_all(client, auth_token):
    test_data = getattr(data, "staff_fetch_all")
    response = client.get(
        f"{BASE_URL}/manager/staff/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "content" in json_data
    assert isinstance(json_data["content"], list)


def test_staff_fetch_all_oneaccount(client, auth_token):
    test_data = getattr(data, "staff_fetch_all")
    response = client.get(
        f"{BASE_URL}/manager/staff/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "content" in json_data
    assert isinstance(json_data["content"], list)


def test_staff_fetch_id_readStaffProfile_IdNotExist(client, auth_token):
    test_data = getattr(data, "staff_fetch_all")
    response = client.get(
        f"{BASE_URL}/manager/staff/fetch/{id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )

    assert response.status_code == 500


# def test_edit_staff_account_valid(client, auth_token):
#     test_data = data.edit_staff_account

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 200

# def test_edit_staff_account_valid_changeOnlyPassword(client, auth_token):
#     test_data = data.edit_staff_account_changeOnlyPassword

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 200

# def test_edit_staff_account_blankUsername(client, auth_token):
#     test_data = data.edit_staff_account_blankUsername

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 422

# def test_edit_staff_account_blankPassword(client, auth_token):
#     test_data = data.edit_staff_account_blankpassword

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 422

# def test_edit_staff_account_wrongId(client, auth_token):
#     test_data = data.edit_staff_account_wrongId

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 500

# def test_edit_staff_account_infos_valid(client, auth_token):
#     test_data = data.edit_staff_account_infos_valid

#     response = client.post(
#         f"{BASE_URL}/api/manager/staff/edit/info",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 200

# def test_edit_staff_account_infos_invalidSsn(client, auth_token):
#     test_data = data.edit_staff_account_infos_invalidSsn

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/info",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 422

# def test_edit_staff_account_infos_invalidEmail(client, auth_token):
#     test_data = data.edit_staff_account_infos_invalidEmail

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/info",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 422

# def test_edit_staff_account_infos_invalidPhone(client, auth_token):
#     test_data = data.edit_staff_account_infos_invalid_phone
#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/info",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )

#     assert response.status_code == 422

# def test_manager_staff_edit_status_disable(client, auth_token):
#     valid_prod_id = "5bd2500d-6ff8-42f0-9299-e0a5088f4bcd" #acc slove
#     new_status = "DISABLE"

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/status?id={valid_prod_id}&status={new_status}",
#         headers={"Authorization": f"Bearer {auth_token}"}
#     )

#     assert response.status_code == 200

# def test_manager_staff_edit_status_active(client, auth_token):
#     valid_prod_id = "5bd2500d-6ff8-42f0-9299-e0a5088f4bcd" #acc slove
#     new_status = "ACTIVE"

#     response = client.post(
#         f"{BASE_URL}/manager/staff/edit/status?id={valid_prod_id}&status={new_status}",
#         headers={"Authorization": f"Bearer {auth_token}"}
#     )

#     assert response.status_code == 200


def test_staff_fetch_id_readStaffProfile(client, auth_token):
    test_data = getattr(data, "staff_fetch_id_readStaffProfile")
    response = client.get(
        f"{BASE_URL}/manager/staff/fetch/{id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )

    assert response.status_code == 500


def test_blog_create_success(client, auth_token):
    test_data = getattr(data, "test_blog_create_success")
    with open(main_image_path_blog, "rb") as main_img:
        response = client.post(
            f"{BASE_URL}/staff/blog/create",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={
                "blog_info": (None, json.dumps(test_data), "application/json"),
                "main_image": ("test_image_main.jpg", main_img, "image/jpeg"),
            },
        )
    assert response.status_code == 200


# def test_blog_create_blank_title(client, auth_token):
#     test_data = getattr(data, "test_blog_create_blank_title")
#     with open(main_image_path_blog, "rb") as main_img:
#         response = client.post(
#             f"{BASE_URL}/staff/blog/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "blog_info": (None, json.dumps(test_data), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg")
#             }
#         )
#     assert response.status_code == 422

# def test_blog_create_blank_descripton(client, auth_token):
#     test_data = getattr(data, "test_blog_create_blank_descripton")
#     with open(main_image_path_blog, "rb") as main_img:
#         response = client.post(
#             f"{BASE_URL}/staff/blog/create",
#             headers={"Authorization": f"Bearer {auth_token}"},
#             files={
#                 "blog_info": (None, json.dumps(test_data), "application/json"),
#                 "main_image": ("test_image_main.jpg", main_img, "image/jpeg")
#             }
#         )
#     assert response.status_code == 422

# def test_edit_blog_success(client, auth_token):
#     test_data = data.edit_blog_success
#     response = client.post(
#         f"{BASE_URL}/staff/blog/edit",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )
#     assert response.status_code == 200

# def test_edit_blog_blank_title(client, auth_token):
#     test_data = data.edit_blog_blank_title
#     response = client.post(
#         f"{BASE_URL}/staff/blog/edit",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )
#     assert response.status_code == 500

# def test_edit_blog_blank_description(client, auth_token):
#     test_data = data.edit_blog_blank_description
#     response = client.post(
#         f"{BASE_URL}/staff/blog/edit",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )
#     assert response.status_code == 500

# def test_edit_blog_blank_markdown_text(client, auth_token):
#     test_data = data.edit_blog_blank_markdown_text
#     response = client.post(
#         f"{BASE_URL}/staff/blog/edit",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )
#     assert response.status_code == 500


def test_comment_fetch_all(client, auth_token):
    test_data = data.test_comment_fetch_all
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_normalStatus(client, auth_token):
    test_data = data.test_comment_fetch_all_normalStatus
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_reportedStatus(client, auth_token):
    test_data = data.test_comment_fetch_all_reportedStatus
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_deletedStatus(client, auth_token):
    test_data = data.test_comment_fetch_all_deletedStatus
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_normalStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_normalStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_reportedStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_reportedStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_deletedStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_deletedStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_normalStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_normalStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_reportedStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_reportedStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_all_deletedStatus_typePost(client, auth_token):
    test_data = data.test_comment_fetch_all_deletedStatus_typePost
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_comment_fetch_oneBlog(client, auth_token):
    test_data = data.test_comment_fetch_oneBlog
    response = client.get(
        f"{BASE_URL}/staff/comment/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_fetch_all(client, auth_token):
    test_data = data.test_customer_fetch_all
    response = client.get(
        f"{BASE_URL}/staff/customer/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_fetch_cart(client, auth_token):
    test_data = data.test_customer_fetch_cart
    customer_id = test_data["id"]
    response = client.get(
        f"{BASE_URL}/staff/customer/fetch/cart/{customer_id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_fetch_infos(client, auth_token):
    test_data = data.test_customer_fetch_infos
    customer_id = test_data["id"]
    response = client.get(
        f"{BASE_URL}/staff/customer/fetch/id/{customer_id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 200


def test_customer_fetch_order(client, auth_token):
    test_data = data.test_customer_fetch_order
    customer_id = test_data["id"]
    response = client.get(
        f"{BASE_URL}/staff/customer/fetch/order/{customer_id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_edit_status_banned(client, auth_token):
    test_data = data.test_customer_edit_status_banned
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_edit_status_normal(client, auth_token):
    test_data = data.test_customer_edit_status_normal
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_customer_edit_account_success(client, auth_token):
    test_data = data.test_customer_edit_account_success
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data["params"],
        json=test_data["payload"],
    )
    assert response.status_code == 200


def test_customer_edit_account_blankUsername(client, auth_token):
    test_data = data.test_customer_edit_account_blankUsername
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/account",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data["params"],
        json=test_data["payload"],
    )
    assert response.status_code == 422


# def test_customer_edit_account_blankPassword(client, auth_token):
#     test_data = data.test_customer_edit_account_blankPassword
#     response = client.patch(
#         f"{BASE_URL}/staff/customer/edit/account",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data["params"],
#         json=test_data["payload"]
#     )
#     assert response.status_code == 422


def test_customer_edit_account_infos_valid(client, auth_token):
    test_data = data.test_customer_edit_account_infos_valid
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/info",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data["params"],
        json=test_data["payload"],
    )
    assert response.status_code == 200


def test_customer_edit_account_infos_invalid_email(client, auth_token):
    test_data = data.test_customer_edit_account_infos_invalid_email
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/info",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data["params"],
        json=test_data["payload"],
    )
    assert response.status_code == 422


def test_customer_edit_account_infos_invalid_phone(client, auth_token):
    test_data = data.test_customer_edit_account_infos_invalid_phone
    response = client.patch(
        f"{BASE_URL}/staff/customer/edit/info",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data["params"],
        json=test_data["payload"],
    )
    assert response.status_code == 422


def test_order_fetch_all(client, auth_token):
    test_data = data.test_order_fetch_all
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_onConfirm(client, auth_token):
    test_data = data.test_order_fetch_all
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_PROCESSING(client, auth_token):
    test_data = data.test_order_fetch_all_ON_PROCESSING
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_ON_SHIPPING(client, auth_token):
    test_data = data.test_order_fetch_all_ON_SHIPPING
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_SHIPPED(client, auth_token):
    test_data = data.test_order_fetch_all_SHIPPED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_DELIVERED(client, auth_token):
    test_data = data.test_order_fetch_all_DELIVERED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_all_CANCELLED(client, auth_token):
    test_data = data.test_order_fetch_all_CANCELLED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_onConfirm(client, auth_token):
    test_data = data.test_order_fetch_status_onConfirm
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_PROCESSING(client, auth_token):
    test_data = data.test_order_fetch_status_ON_PROCESSING
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/all",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_ON_SHIPPING(client, auth_token):
    test_data = data.test_order_fetch_status_ON_SHIPPING
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_SHIPPED(client, auth_token):
    test_data = data.test_order_fetch_status_SHIPPED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_DELIVERED(client, auth_token):
    test_data = data.test_order_fetch_status_DELIVERED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_status_CANCELLED(client, auth_token):
    test_data = data.test_order_fetch_status_CANCELLED
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/status",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_infos(client, auth_token):
    test_data = data.test_order_fetch_infos
    customer_id = test_data["id"]
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/{customer_id}",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


def test_order_fetch_items(client, auth_token):
    test_data = data.test_order_fetch_items
    customer_id = test_data["id"]
    response = client.get(
        f"{BASE_URL}/staff/order/fetch/{customer_id}/items",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        params=test_data,
    )
    assert response.status_code == 200


# def test_order_accept(client, auth_token):
#     test_data = data.test_order_accept
#     customer_id = test_data["id"]
#     response = client.post(
#         f"{BASE_URL}/staff/order/accept/{customer_id}",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data

#     )
#     assert response.status_code == 200

# def test_order_cancel(client, auth_token):
#     test_data = data.test_order_cancel
#     customer_id = test_data["id"]
#     response = client.post(
#         f"{BASE_URL}/staff/order/cancel/{customer_id}",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data

#     )
#     assert response.status_code == 200

# def test_order_shipper_assign(client, auth_token):
#     test_data = data.test_order_shipper_assign
#     response = client.put(
#         f"{BASE_URL}/staff/shipper/assign",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data

#     )
#     assert response.status_code == 200

# def test_order_shipper_assign(client, auth_token):
#     test_data = data.test_order_shipper_assign
#     response = client.put(
#         f"{BASE_URL}/staff/shipper/assign",
#         headers={
#             "Authorization": f"Bearer {auth_token}",
#             "Content-Type": "application/json"
#         },
#         params=test_data

#     )
#     assert response.status_code == 200

# def test_order_shipper_accept(client, auth_token):
#     test_data = data.test_order_shipper_accept
#     id = test_data["id"]
#     response = client.put(
#         f"{BASE_URL}/shipper/order/accept/{id}",
#         headers={
#             "Authorization": f"Bearer {auth_token_shipper}",
#             "Content-Type": "application/json"
#         },
#         params=test_data

#     )
#     assert response.status_code == 200
