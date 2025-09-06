"""Authentication utilities."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ryagent.config.settings import settings

security = HTTPBearer(auto_error=False)


async def verify_token(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
) -> bool:
    """Verify the authorization token."""

    # For development, allow requests from localhost without token
    if (
        settings.debug
        and request.client
        and request.client.host in ["127.0.0.1", "::1"]
    ):
        return True

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.auth_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


# Dependency for protected routes
AuthRequired = Annotated[bool, Depends(verify_token)]
