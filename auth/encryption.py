from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(input: str) -> str:
    return pwd_context.hash(input)


def verify(secret: str, hash: str):
    return pwd_context.verify(
        secret=secret,
        hash=hash
    )
