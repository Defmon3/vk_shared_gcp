#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: storage.py

Google Cloud Storage client and byte helpers.
"""

from typing import cast

from google.api_core.retry import Retry
from google.cloud import storage  # type: ignore[attr-defined]

from vk_shared_gcp.gcs.uri import parse_gcs_uri


def build_storage_client(project: str) -> storage.Client:
    """Build a Google Cloud Storage client."""
    return cast(storage.Client, storage.Client(project=project))


def download_bytes(client: storage.Client, uri: str, *, timeout_seconds: float) -> bytes:
    """Download bytes from a GCS URI."""
    parsed = parse_gcs_uri(uri)
    return cast(bytes, client.bucket(parsed.bucket).blob(parsed.name).download_as_bytes(timeout=timeout_seconds))


def upload_bytes(client: storage.Client, uri: str, data: bytes, *, content_type: str, timeout_seconds: float, retry: Retry | None = None) -> int | None:
    """Upload bytes to a GCS URI and return the object generation."""
    parsed = parse_gcs_uri(uri)
    blob = client.bucket(parsed.bucket).blob(parsed.name)
    blob.upload_from_string(data, content_type=content_type, timeout=timeout_seconds, retry=retry)
    generation = blob.generation
    if generation is None:
        return None
    return int(generation)
