"""FastAPI dependencies — auth, DB session."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.core.security import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract user_id from Bearer JWT token."""
    payload = decode_access_token(credentials.credentials)
    return payload["sub"]


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract user_id and role from Bearer JWT token."""
    payload = decode_access_token(credentials.credentials)
    return {"user_id": payload["sub"], "role": payload.get("role", "mse")}


# Type aliases
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentUser = Annotated[dict, Depends(get_current_user_role)]
