"""Application settings.

Examples:
    ```python
    import logging

    from core.settings import current_settings


    # log current environment
    logging.info(current_settings.env)  # INFO:dev
    ```

"""

from __future__ import annotations

from urllib.parse import urljoin

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from wf_catalogue_service import consts


class OAuth2Settings(BaseModel):
    """OAuth2 settings."""

    base_url: str
    realm: str
    username: str
    password: str
    client_id: str

    @property
    def oid_url(self) -> str:
        """Returns the OpenID URL."""
        return urljoin(self.base_url, f"/keycloak/realms/{self.realm}/protocol/openid-connect")

    @property
    def token_url(self) -> str:
        """Returns the token URL."""
        return self.oid_url + "/token"

    @property
    def auth_url(self) -> str:
        """Returns the auth URL."""
        return self.oid_url + "/auth"

    @property
    def introspect_url(self) -> str:
        """Returns the introspect URL."""
        return self.token_url + "/introspect"

    @property
    def certs_url(self) -> str:
        """Returns the certs URL."""
        return self.oid_url + "/certs"


class EODHSettings(OAuth2Settings):
    """EO Data Hub settings."""

    stac_api_endpoint: str
    workspace_services_endpoint: str
    tmp_s3_credentials_endpoint: str

    @property
    def workspace_tokens_url(self) -> str:
        """Returns the URL for retrieving workspace tokens."""
        return f"{self.workspace_services_endpoint}/{self.username}/me/tokens"

    @property
    def workspace_session_tokens_url(self) -> str:
        """Returns the URL for retrieving workspace session tokens."""
        return f"{self.workspace_services_endpoint}/{self.username}/me/sessions"


class Settings(BaseSettings):
    """Represents Application Settings with nested configuration sections."""

    environment: str = "local"
    eodh: EODHSettings
    model_config = SettingsConfigDict(
        env_file=consts.directories.ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


def current_settings() -> Settings:
    """Instantiate current application settings.

    Returns:
        Current application settings.

    """
    return Settings()
