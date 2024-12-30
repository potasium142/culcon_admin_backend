from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from auth import jwt_token
from db.postgresql.repos import account_repo
from db.postgresql.models.staff_account import AccountType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

CREDENTIAL_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def permission(token: str, type: AccountType) -> bool:
    try:
        payload = jwt_token.decode(token)

        if payload.get("id") is None:
            raise CREDENTIAL_EXCEPTION

        account = account_repo.find_by_token(token)

        if account is None:
            raise CREDENTIAL_EXCEPTION

        if account.type not in type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient permission",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except InvalidTokenError:
        raise CREDENTIAL_EXCEPTION

    return True


def manager_permission(token: str = Depends(oauth2_scheme)) -> bool:
    return permission(token, True)


def staff_permission(token: str = Depends(oauth2_scheme)) -> bool:
    return permission(token)
