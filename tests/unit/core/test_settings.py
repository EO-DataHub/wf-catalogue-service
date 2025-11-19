from __future__ import annotations

from unittest.mock import patch

from wf_catalogue_service.core.settings import Settings, current_settings

_TEST_ENV_VARS = {
    "ENVIRONMENT": "production",
    "EODH__USERNAME": "test_username",
    "EODH__PASSWORD": "test_password",
    "EODH__BASE_URL": "https://eodh.test.com/",
    "EODH__CLIENT_ID": "test_client_id",
    "EODH__REALM": "test_realm",
    "EODH__STAC_API_ENDPOINT": "https://eodh.test.com/stac",
    "EODH__WORKSPACE_SERVICES_ENDPOINT": "https://eodh.test.com/workspaces",
    "EODH__TMP_S3_CREDENTIALS_ENDPOINT": "https://eodh.test.com/s3-creds",
}


@patch.dict(
    "os.environ",
    _TEST_ENV_VARS,
)
def test_settings() -> None:
    assert current_settings() is not None


@patch.dict(
    "os.environ",
    _TEST_ENV_VARS,
)
def test_environment_variable_override() -> None:
    settings = Settings()
    assert settings.environment == "production"
