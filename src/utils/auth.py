import logging
from typing import Optional, Callable
from fastapi import Header, HTTPException
from src.config import settings
from src.utils.security import check_permission, PERMISSIONS

logger = logging.getLogger(__name__)

def _extract_admin_key(x_admin_key: Optional[str], authorization: Optional[str]) -> Optional[str]:
    if x_admin_key:
        return x_admin_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None

def require_permission(action: str):
    """
    Enforces admin authentication + RBAC permission check.
    Admin key can be provided via `X-Admin-Key` or `Authorization: Bearer <key>`.
    Role can be provided via `X-Role` (defaults to 'admin').
    """
    async def _dependency(
        x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
        authorization: Optional[str] = Header(None, alias="Authorization"),
        x_role: Optional[str] = Header("admin", alias="X-Role")
    ):
        # Enforce admin key presence in prod
        if settings.ENV.lower() in {"prod", "production"}:
            if not settings.ADMIN_API_KEY or settings.ADMIN_API_KEY == "dev_admin_key_CHANGE_IN_PROD":
                raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured.")
        else:
            if settings.ADMIN_API_KEY == "dev_admin_key_CHANGE_IN_PROD":
                logger.warning("⚠️ Using default ADMIN_API_KEY (dev). Set ADMIN_API_KEY in .env for safety.")

        admin_key = _extract_admin_key(x_admin_key, authorization)
        if not admin_key or admin_key != settings.ADMIN_API_KEY:
            raise HTTPException(status_code=401, detail="Admin authorization required.")

        # Role validation
        role = (x_role or "admin").strip().lower()
        if role not in PERMISSIONS:
            raise HTTPException(status_code=403, detail="Invalid role.")

        if not check_permission(role, action):
            raise HTTPException(status_code=403, detail="Insufficient permissions.")

        return role

    return _dependency
