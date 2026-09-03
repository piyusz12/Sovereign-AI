"""
Sovereign AI Workbench — Authentication

JWT-based local authentication. No external auth providers.

Uses bcrypt directly instead of passlib to avoid compatibility issues
with bcrypt >= 4.1 and Python 3.13+.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.settings import settings

logger = logging.getLogger("sovereign.security.auth")

# Config — loaded from settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expiry_minutes


def _hash_password(plain: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    role: str
    department: str
    disabled: bool = False


# Demo users for prototype
DEMO_USERS: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "hashed_password": _hash_password("admin123"),
        "role": "admin",
        "department": "all",
        "disabled": False,
    },
    "engineer": {
        "username": "engineer",
        "hashed_password": _hash_password("eng123"),
        "role": "engineering",
        "department": "engineering",
        "disabled": False,
    },
    "finance_user": {
        "username": "finance_user",
        "hashed_password": _hash_password("fin123"),
        "role": "finance",
        "department": "finance",
        "disabled": False,
    },
    "ops_user": {
        "username": "ops_user",
        "hashed_password": _hash_password("ops123"),
        "role": "operations",
        "department": "operations",
        "disabled": False,
    },
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        return TokenData(username=username, role=role)
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    user_data = DEMO_USERS.get(username)
    if not user_data:
        return None
    if not verify_password(password, user_data["hashed_password"]):
        return None
    return User(
        username=user_data["username"],
        role=user_data["role"],
        department=user_data["department"],
        disabled=user_data["disabled"],
    )
