"""
Sovereign AI Workbench — Authentication

JWT-based local authentication. No external auth providers.

Uses bcrypt directly instead of passlib to avoid compatibility issues
with bcrypt >= 4.1 and Python 3.13+.

User data is persisted in a JSON file (data/users.json) instead of
hard-coded demo users.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


# ── Persistent User Store ──────────────────────────────────────────────────────

USERS_FILE = Path(settings.data_dir) / "users.json"

# Default users seeded on first boot
_SEED_USERS: list[dict] = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "department": "all",
    },
]


class UserStore:
    """
    JSON-file-backed user store.

    On first run, seeds default admin credentials.
    Thread-safety: writes are serialized through _save(), which is acceptable
    for a single-process API server.  For multi-process deployments, swap
    this for a proper DB.
    """

    def __init__(self, path: Path = USERS_FILE):
        self._path = path
        self._users: dict[str, dict] = {}
        self._load()

    # ── Private ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load users from disk, seeding defaults if the file doesn't exist."""
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._users = {u["username"]: u for u in data}
                logger.info("Loaded %d users from %s", len(self._users), self._path)
                return
            except Exception as exc:
                logger.warning("Failed to load users file: %s — reseeding", exc)

        # First run — seed
        self._path.parent.mkdir(parents=True, exist_ok=True)
        for seed in _SEED_USERS:
            self._users[seed["username"]] = {
                "username": seed["username"],
                "hashed_password": _hash_password(seed["password"]),
                "role": seed["role"],
                "department": seed["department"],
                "disabled": False,
            }
        self._save()
        logger.info("Seeded %d default users to %s", len(self._users), self._path)

    def _save(self) -> None:
        """Persist current users to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(list(self._users.values()), indent=2),
            encoding="utf-8",
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def get_user(self, username: str) -> Optional[dict]:
        """Return user dict or None."""
        return self._users.get(username)

    def create_user(
        self,
        username: str,
        password: str,
        role: str,
        department: str,
    ) -> dict:
        """Create a new user. Raises ValueError if username exists."""
        if username in self._users:
            raise ValueError(f"User '{username}' already exists")

        user_data = {
            "username": username,
            "hashed_password": _hash_password(password),
            "role": role,
            "department": department,
            "disabled": False,
        }
        self._users[username] = user_data
        self._save()
        logger.info("Created user '%s' with role '%s'", username, role)
        return user_data

    def delete_user(self, username: str) -> bool:
        """Delete a user. Returns True if deleted, False if not found."""
        if username not in self._users:
            return False
        del self._users[username]
        self._save()
        logger.info("Deleted user '%s'", username)
        return True

    def list_users(self) -> list[dict]:
        """Return all users (without hashed passwords)."""
        return [
            {
                "username": u["username"],
                "role": u["role"],
                "department": u["department"],
                "disabled": u.get("disabled", False),
            }
            for u in self._users.values()
        ]


# Global singleton
user_store = UserStore()


# ── Token helpers ──────────────────────────────────────────────────────────────


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
    """Authenticate against the persistent user store."""
    user_data = user_store.get_user(username)
    if not user_data:
        return None
    if user_data.get("disabled", False):
        return None
    if not verify_password(password, user_data["hashed_password"]):
        return None
    return User(
        username=user_data["username"],
        role=user_data["role"],
        department=user_data["department"],
        disabled=user_data.get("disabled", False),
    )
