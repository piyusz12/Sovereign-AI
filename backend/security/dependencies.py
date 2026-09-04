"""
Sovereign AI Workbench — API Dependencies

Provides FastAPI dependencies for authentication and fine-grained RBAC authorization.
"""

import logging
from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.security.auth import decode_token, DEMO_USERS
from backend.security.rbac import rbac_enforcer
from backend.security.audit import audit_log

logger = logging.getLogger("sovereign.security.dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decode the JWT token and return the active user.
    """
    token_data = decode_token(token)
    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = DEMO_USERS.get(token_data.username)
    if not user_data or user_data.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user_data


def require_permission(permission: str) -> Callable:
    """
    Dependency factory to check if the current user has the specified permission.
    """
    def permission_checker(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role", "")
        if not rbac_enforcer.has_permission(role, permission):
            # Log the denial to audit trail
            audit_log.log_event(
                event_type="authorization_denied",
                user=current_user.get("username", "unknown"),
                result="DENIED",
                details={"required_permission": permission, "role": role},
            )
            logger.warning(
                "Access denied for user '%s' (role: %s). Missing permission: %s",
                current_user.get("username"), role, permission
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires: {permission}",
            )
        return current_user

    return permission_checker
