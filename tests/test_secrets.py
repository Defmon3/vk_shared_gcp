from dataclasses import dataclass

import pytest
from google.api_core.exceptions import PermissionDenied

from vk_shared_gcp.secrets import SecretResolutionError, resolve_secret


@dataclass(frozen=True, slots=True)
class FakePayload:
    data: bytes


@dataclass(frozen=True, slots=True)
class FakeResponse:
    payload: FakePayload | None


class FakeSecretClient:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.requests: list[dict[str, str]] = []
        self.timeouts: list[float] = []

    def access_secret_version(self, *, request: dict[str, str], timeout: float) -> FakeResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise AssertionError("response is required")
        return self.response


def test_resolve_secret_decodes_trimmed_payload() -> None:
    client = FakeSecretClient(FakeResponse(FakePayload(b" token \n")))

    result = resolve_secret(client, project="vk8", secret_name="vk-token", timeout_seconds=3.5)

    assert result == "token"
    assert client.requests == [{"name": "projects/vk8/secrets/vk-token/versions/latest"}]
    assert client.timeouts == [3.5]


@pytest.mark.parametrize("response", [FakeResponse(None), FakeResponse(FakePayload(b"")), FakeResponse(FakePayload(b"   \n"))])
def test_resolve_secret_rejects_missing_or_empty_payload(response: FakeResponse) -> None:
    client = FakeSecretClient(response)

    with pytest.raises(SecretResolutionError):
        resolve_secret(client, project="vk8", secret_name="vk-token", timeout_seconds=2.0)


def test_resolve_secret_propagates_google_errors() -> None:
    client = FakeSecretClient(error=PermissionDenied("denied"))

    with pytest.raises(PermissionDenied):
        resolve_secret(client, project="vk8", secret_name="vk-token", timeout_seconds=2.0)


@pytest.mark.parametrize(
    ("project", "secret_name", "version"),
    [
        pytest.param("vk8/bad", "vk-token", "latest", id="project_slash"),
        pytest.param("vk8", "vk/token", "latest", id="secret_slash"),
        pytest.param("vk8", "vk-token", "1/2", id="version_slash"),
        pytest.param("vk8", "vk-token", "latest/extra", id="version_resource_suffix"),
    ],
)
def test_resolve_secret_rejects_path_altering_resource_components(project: str, secret_name: str, version: str) -> None:
    client = FakeSecretClient(FakeResponse(FakePayload(b"token")))

    with pytest.raises(ValueError):
        resolve_secret(client, project=project, secret_name=secret_name, version=version, timeout_seconds=2.0)
    assert client.requests == []
