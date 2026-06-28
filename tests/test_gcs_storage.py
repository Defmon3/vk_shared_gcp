from google.api_core.retry import Retry

from vk_shared_gcp.gcs.storage import download_bytes, upload_bytes


class FakeBlob:
    def __init__(self, data: bytes = b"payload", generation: int | str | None = 12) -> None:
        self.data = data
        self.generation = generation
        self.upload_calls: list[tuple[bytes, str, float, Retry | None]] = []
        self.download_timeouts: list[float] = []

    def download_as_bytes(self, *, timeout: float) -> bytes:
        self.download_timeouts.append(timeout)
        return self.data

    def upload_from_string(self, data: bytes, *, content_type: str, timeout: float, retry: Retry | None = None) -> None:
        self.upload_calls.append((data, content_type, timeout, retry))


class FakeBucket:
    def __init__(self, blob: FakeBlob) -> None:
        self._blob = blob
        self.names: list[str] = []

    def blob(self, name: str) -> FakeBlob:
        self.names.append(name)
        return self._blob


class FakeStorageClient:
    def __init__(self, blob: FakeBlob) -> None:
        self.bucket_obj = FakeBucket(blob)
        self.buckets: list[str] = []

    def bucket(self, bucket_name: str) -> FakeBucket:
        self.buckets.append(bucket_name)
        return self.bucket_obj


def test_download_bytes_addresses_parsed_blob() -> None:
    blob = FakeBlob(data=b"image")
    client = FakeStorageClient(blob)

    result = download_bytes(client, "gs://bucket/path/image.jpg", timeout_seconds=2.5)

    assert result == b"image"
    assert client.buckets == ["bucket"]
    assert client.bucket_obj.names == ["path/image.jpg"]
    assert blob.download_timeouts == [2.5]


def test_upload_bytes_returns_generation() -> None:
    blob = FakeBlob(generation="15")
    client = FakeStorageClient(blob)
    retry = Retry()

    result = upload_bytes(client, "gs://bucket/path/file.json", b"{}", content_type="application/json", timeout_seconds=3.0, retry=retry)

    assert result == 15
    assert client.buckets == ["bucket"]
    assert client.bucket_obj.names == ["path/file.json"]
    assert blob.upload_calls == [(b"{}", "application/json", 3.0, retry)]


def test_upload_bytes_allows_missing_generation() -> None:
    blob = FakeBlob(generation=None)
    client = FakeStorageClient(blob)

    assert upload_bytes(client, "gs://bucket/path/file.json", b"{}", content_type="application/json", timeout_seconds=3.0) is None
