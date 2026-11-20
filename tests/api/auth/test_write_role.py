"""Tests for the realm role check on the write endpoints.

The tokens are real RS256 JWTs signed with a key generated here. Only the JWKS fetch is stubbed, so `decode_token` runs
unmocked.

"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWKClient
from jwt.algorithms import RSAAlgorithm
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient, Response

WRITE_ROLE = "catalogue-test-writer"
KEY_ID = "test-signing-key"
DEFAULT_CATALOGUE_ID = "eodh-workflows-notebooks"
SEEDED_COLLECTION_ID = "seeded-collection"
NEW_COLLECTION_ID = "new-collection"
NEW_RECORD_ID = "new-record"

# Realm roles every platform user gets by default.
ORDINARY_USER_ROLES = ["default-roles-eodhp", "offline_access", "hub_user", "uma_authorization"]

_AUTH_ENV = {
    "ENVIRONMENT": "test",
    "EODH__BASE_URL": "https://keycloak.invalid",
    "EODH__REALM": "test-realm",
    "EODH__USERNAME": "unused",
    "EODH__PASSWORD": "unused",
    "EODH__CLIENT_ID": "unused",
    "EODH__STAC_API_ENDPOINT": "https://stac.invalid",
    "EODH__WORKSPACE_SERVICES_ENDPOINT": "https://workspaces.invalid",
    "EODH__TMP_S3_CREDENTIALS_ENDPOINT": "https://s3-creds.invalid",
    "EODH__WRITE_ROLE": WRITE_ROLE,
}


@pytest.fixture(scope="module")
def signing_key() -> rsa.RSAPrivateKey:
    """RSA key the stubbed JWKS endpoint publishes."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def auth_env(monkeypatch: pytest.MonkeyPatch, signing_key: rsa.RSAPrivateKey) -> None:
    """Configure a non-local environment and serve the test key from the JWKS endpoint."""
    for name, value in _AUTH_ENV.items():
        monkeypatch.setenv(name, value)

    jwk = RSAAlgorithm.to_jwk(signing_key.public_key(), as_dict=True)
    jwks = {"keys": [{**jwk, "kid": KEY_ID, "use": "sig", "alg": "RS256"}]}
    monkeypatch.setattr(PyJWKClient, "fetch_data", lambda _self: jwks)


def _token(key: rsa.RSAPrivateKey, **claims: Any) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "azp": "test-client",
        "aud": ["eodh", "account"],
        "iat": now,
        "exp": now + 300,
        **claims,
    }
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": KEY_ID})


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def writer_headers(signing_key: rsa.RSAPrivateKey) -> dict[str, str]:
    """Headers for a token that holds the write role alongside ordinary roles."""
    return _bearer(_token(signing_key, realm_access={"roles": [*ORDINARY_USER_ROLES, WRITE_ROLE]}))


async def _seed(client: AsyncClient, headers: dict[str, str], record: dict[str, Any]) -> None:
    """Create an empty collection and a record for the delete attempts to target."""
    response = await client.post(
        "/collections",
        json={"id": SEEDED_COLLECTION_ID, "title": "Seeded", "description": "Seeded collection"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    response = await client.post("/register", json=record, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED


async def _attempt_writes(client: AsyncClient, headers: dict[str, str], record: dict[str, Any]) -> dict[str, Response]:
    """Call each write endpoint once; deletes target the seeded objects."""
    new_record = {**record, "id": NEW_RECORD_ID}
    return {
        "POST /collections": await client.post(
            "/collections",
            json={"id": NEW_COLLECTION_ID, "title": "New", "description": "New collection"},
            headers=headers,
        ),
        "POST /register": await client.post("/register", json=new_record, headers=headers),
        "DELETE /register/{record_id}": await client.delete(f"/register/{record['id']}", headers=headers),
        "DELETE /collections/{catalogue_id}": await client.delete(
            f"/collections/{SEEDED_COLLECTION_ID}", headers=headers
        ),
    }


async def _assert_catalogue_unchanged(client: AsyncClient, seeded_record_id: str) -> None:
    """The seeded objects still exist and nothing new was created."""
    assert (await client.get(f"/collections/{SEEDED_COLLECTION_ID}")).status_code == status.HTTP_200_OK
    assert (
        await client.get(f"/collections/{DEFAULT_CATALOGUE_ID}/items/{seeded_record_id}")
    ).status_code == status.HTTP_200_OK
    assert (await client.get(f"/collections/{NEW_COLLECTION_ID}")).status_code == status.HTTP_404_NOT_FOUND
    assert (
        await client.get(f"/collections/{DEFAULT_CATALOGUE_ID}/items/{NEW_RECORD_ID}")
    ).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.usefixtures("auth_env")
@pytest.mark.parametrize(
    "claims",
    [
        pytest.param({"realm_access": {"roles": ORDINARY_USER_ROLES}}, id="ordinary-user-roles"),
        pytest.param({}, id="no-realm-access-claim"),
        pytest.param({"realm_access": {"roles": WRITE_ROLE}}, id="roles-claim-is-a-string"),
        pytest.param({"realm_access": [WRITE_ROLE]}, id="realm-access-is-a-list"),
        pytest.param(
            {
                "realm_access": {"roles": ORDINARY_USER_ROLES},
                "resource_access": {"eodh": {"roles": [WRITE_ROLE]}},
            },
            id="role-only-as-client-role",
        ),
    ],
)
async def test_valid_token_without_write_role_gets_403(
    client: AsyncClient,
    signing_key: rsa.RSAPrivateKey,
    writer_headers: dict[str, str],
    workflow_json: dict[str, Any],
    claims: dict[str, Any],
) -> None:
    """A valid token without the write role gets 403 on every write endpoint and changes nothing."""
    await _seed(client, writer_headers, workflow_json)

    responses = await _attempt_writes(client, _bearer(_token(signing_key, **claims)), workflow_json)

    assert {route: r.status_code for route, r in responses.items()} == dict.fromkeys(
        responses, status.HTTP_403_FORBIDDEN
    )
    assert all(r.json() == {"detail": "Insufficient permissions"} for r in responses.values())
    await _assert_catalogue_unchanged(client, workflow_json["id"])


@pytest.mark.asyncio
@pytest.mark.usefixtures("auth_env")
async def test_token_with_write_role_can_write(
    client: AsyncClient,
    writer_headers: dict[str, str],
    workflow_json: dict[str, Any],
) -> None:
    """A token with the write role can create and delete collections and records."""
    await _seed(client, writer_headers, workflow_json)

    responses = await _attempt_writes(client, writer_headers, workflow_json)

    assert {route: r.status_code for route, r in responses.items()} == {
        "POST /collections": status.HTTP_201_CREATED,
        "POST /register": status.HTTP_201_CREATED,
        "DELETE /register/{record_id}": status.HTTP_204_NO_CONTENT,
        "DELETE /collections/{catalogue_id}": status.HTTP_204_NO_CONTENT,
    }
    assert (await client.get(f"/collections/{NEW_COLLECTION_ID}")).status_code == status.HTTP_200_OK
    assert (
        await client.get(f"/collections/{DEFAULT_CATALOGUE_ID}/items/{NEW_RECORD_ID}")
    ).status_code == status.HTTP_200_OK
    assert (
        await client.get(f"/collections/{DEFAULT_CATALOGUE_ID}/items/{workflow_json['id']}")
    ).status_code == status.HTTP_404_NOT_FOUND
    assert (await client.get(f"/collections/{SEEDED_COLLECTION_ID}")).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.usefixtures("auth_env")
@pytest.mark.parametrize(
    "make_headers",
    [
        pytest.param(lambda _key: {}, id="no-authorization-header"),
        pytest.param(
            lambda _key: _bearer(
                _token(
                    rsa.generate_private_key(public_exponent=65537, key_size=2048),
                    realm_access={"roles": [WRITE_ROLE]},
                )
            ),
            id="signed-by-another-key",
        ),
        pytest.param(
            lambda key: _bearer(
                _token(
                    key, realm_access={"roles": [WRITE_ROLE]}, iat=int(time.time()) - 600, exp=int(time.time()) - 300
                )
            ),
            id="expired",
        ),
        pytest.param(
            lambda key: _bearer(_token(key, realm_access={"roles": [WRITE_ROLE]}, aud=["eodh"])),
            id="audience-not-accepted",
        ),
    ],
)
async def test_invalid_token_with_write_role_gets_401(
    client: AsyncClient,
    signing_key: rsa.RSAPrivateKey,
    writer_headers: dict[str, str],
    workflow_json: dict[str, Any],
    make_headers: Any,
) -> None:
    """An invalid token gets 401 even if it claims the write role."""
    await _seed(client, writer_headers, workflow_json)

    responses = await _attempt_writes(client, make_headers(signing_key), workflow_json)

    assert {route: r.status_code for route, r in responses.items()} == dict.fromkeys(
        responses, status.HTTP_401_UNAUTHORIZED
    )
    await _assert_catalogue_unchanged(client, workflow_json["id"])


@pytest.mark.asyncio
@pytest.mark.usefixtures("auth_env")
@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/collections",
        f"/collections/{DEFAULT_CATALOGUE_ID}",
        f"/collections/{DEFAULT_CATALOGUE_ID}/items",
    ],
)
async def test_read_endpoints_need_no_token(client: AsyncClient, path: str) -> None:
    """Read endpoints need no token."""
    response = await client.get(path)

    assert response.status_code == status.HTTP_200_OK
