import pytest
import httpx

BASE_URL = "https://culcon-ad-be-30883260979.asia-east1.run.app/api"


@pytest.fixture
def client():
    """Fixture tạo HTTP client cho mỗi test"""
    return httpx.Client(base_url=BASE_URL, timeout=10)


@pytest.fixture
def auth_token(client):
    """Fixture đăng nhập và lấy token"""
    response = client.post(
        "/auth/login", data={"username": "test", "password": "123456"}  
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_login_invalid_credentials(client):
    """Test đăng nhập với tài khoản sai"""
    response = client.post(
        "/auth/login", data={"username": "wrong_user", "password": "wrong_pass"}  
    )
    assert response.status_code == 400


def test_login_valid_credentials(client):
    """Test đăng nhập thành công (Cần user hợp lệ)"""
    valid_credentials = {"username": "test", "password": "123456"}
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


def test_product_fetch_all_success(client, auth_token):
    """Test lấy danh sách sản phẩm với token hợp lệ"""
    response = client.get(
        "/general/product/fetch_all",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200

def test_product_fetch_success(client, auth_token):
    response = client.get(
        f"{BASE_URL}/general/product/fetch",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        },
        params={"prod_id": "VEG_Apple"},
    )
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
    assert response.status_code == 200

def test_product_fetch_ProductNotExist(client, auth_token):
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