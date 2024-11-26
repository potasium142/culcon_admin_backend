from datetime import datetime, timedelta, timezone
from db.models.account import Account
import jwt

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def encode(account: Account,
           expires_delta: timedelta | None = None):

    if not expires_delta:
        expires_delta = timedelta(hours=1)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "username": account.username,
        "type": account.type.name,
        "exp": expire
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode(jwt_token: str) -> dict:
    return jwt.decode(jwt_token, SECRET_KEY, algorithms=ALGORITHM)
