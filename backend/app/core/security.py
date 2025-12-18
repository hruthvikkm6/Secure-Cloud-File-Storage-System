from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.schemas.user import TokenData



password_hasher = PasswordHasher()

def get_password_hash(password: str) -> str:
    """
    Hash a plain password using Argon2.
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except Exception:
        return False




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")




def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    """
    if not isinstance(settings.SECRET_KEY, str) or not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not properly set")

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt



def decode_access_token(token: str) -> TokenData:
    """
    Decode JWT token and extract user data.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(email=email)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """
    Dependency to get current authenticated user.
    """
    return decode_access_token(token)
