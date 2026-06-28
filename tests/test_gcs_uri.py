import pytest

from vk_shared_gcp.gcs.uri import GcsUri, build_gcs_uri, parse_gcs_uri


def test_parse_gcs_uri_returns_bucket_and_name() -> None:
    assert parse_gcs_uri("gs://bucket/a/c.json") == GcsUri(bucket="bucket", name="a/c.json")


@pytest.mark.parametrize("uri", ["http://bucket/a", "gs://", "gs://bucket"])
def test_parse_gcs_uri_rejects_invalid_values(uri: str) -> None:
    with pytest.raises(ValueError):
        parse_gcs_uri(uri)


def test_build_gcs_uri_requires_bucket_and_name() -> None:
    assert build_gcs_uri("bucket", "name") == "gs://bucket/name"

    with pytest.raises(ValueError):
        build_gcs_uri("", "name")
