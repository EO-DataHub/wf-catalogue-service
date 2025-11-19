"""Authentication helpers."""

from __future__ import annotations

from typing import Annotated, Any

import jwt
import jwt.exceptions
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient  # type: ignore[attr-defined]

from wf_catalogue_service.api.auth.schemas import IntrospectResponse
from wf_catalogue_service.core.settings import current_settings

_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

jwt_bearer_scheme = HTTPBearer()
optional_jwt_bearer_scheme = HTTPBearer(auto_error=False)
TIMEOUT = 30


def decode_token(token: str) -> dict[str, Any]:
    """Decodes JWT token."""
    optional_custom_headers = {"User-agent": "custom-user-agent"}
    jwks_client = PyJWKClient(current_settings().eodh.certs_url, headers=optional_custom_headers)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            audience=["oauth2-proxy-workspaces", "oauth2-proxy", "account"],
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
    except jwt.exceptions.PyJWTError as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from ex


def validate_access_token(
    credential: Annotated[HTTPAuthorizationCredentials, Depends(jwt_bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    """Validates JWT token."""
    decode_token(credential.credentials)
    return credential


def validate_access_token_if_provided(
    credential: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_jwt_bearer_scheme)] = None,
) -> HTTPAuthorizationCredentials | None:
    """Validates JWT token if provided."""
    if credential is None:
        return None
    decode_token(credential.credentials)
    return credential


def try_get_workspace_from_token_or_request_body(
    introspected_token: dict[str, Any],
    workspace_from_request_body: str | None = None,
) -> str:
    """Tries to get workspace from token or request body."""
    if workspace_from_request_body is not None:
        return workspace_from_request_body

    parsed_token = IntrospectResponse(**introspected_token)
    if parsed_token.workspaces:
        # Take first workspace from the WS list
        return parsed_token.workspaces[0]
    if parsed_token.preferred_username is not None:
        # As a fallback take preferred username if present
        return parsed_token.preferred_username
    # Raise exception otherwise
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
