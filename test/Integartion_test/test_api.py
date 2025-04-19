from fastapi.testclient import TestClient
from main import app  # noqa: E402

client = TestClient(app)


def test_permission_test_no_token():
    response = client.get("/api/auth/permission_test")
    assert response.status_code == 401


# def test_permission_test_with_token():
#     response = client.get(
#         "/api/auth/permission_test", headers={"Authorization": "Bearer valid_token"}
#     )
#     assert response.status_code in [200, 401]


# def test_profile_no_token():
#     response = client.get("/api/auth/profile")
#     assert response.status_code == 401


# def test_profile_invalid_token():
#     response = client.get(
#         "/api/auth/profile", headers={"Authorization": "Bearer invalid"}
#     )
#     assert response.status_code in [200, 401]


# def test_login_invalid_credentials():
#     response = client.post(
#         "/api/auth/login", data={"username": "unknown", "password": "wrong"}
#     )
#     assert response.status_code == 400

