from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from auth import jwt_token
from db.repos import account_repo
from db.models.staff_account import AccountType

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

CREDENTIAL_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def permission(
    token: str,
    is_manager: bool = False
) -> bool:
    try:
        payload = jwt_token.decode(token)

        if payload.get("username") is None:
            raise CREDENTIAL_EXCEPTION

        account = account_repo.find_by_token(token)

        if account is None:
            raise CREDENTIAL_EXCEPTION

        is_staff = account.type == AccountType.STAFF

        if not is_manager and is_staff:
            return True

        if account.type != AccountType.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient permission",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except InvalidTokenError:
        raise CREDENTIAL_EXCEPTION

    return True


def manager_permission(
    token: str = Depends(oauth2_scheme)
) -> bool:
    return permission(token, True)


def staff_permission(
    token: str = Depends(oauth2_scheme)
) -> bool:
    return permission(token)
