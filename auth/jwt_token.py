from datetime import datetime, timedelta, timezone
from db.postgresql.models.staff_account import StaffAccount
from config import env
import jwt

SECRET_KEY = env.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = env.TOKEN_EXPIRE_MINUTES


def encode(account: StaffAccount, expires_delta: timedelta | None = None):
    if not expires_delta:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {"id": str(account.id), "exp": expire}

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode(jwt_token: str):
    return jwt.decode(jwt_token, SECRET_KEY, algorithms=ALGORITHM)
