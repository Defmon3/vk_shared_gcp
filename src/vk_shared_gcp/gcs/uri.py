#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: uri.py

Google Cloud Storage URI helpers.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GcsUri:
    """Parsed Google Cloud Storage URI."""

    bucket: str
    name: str


def parse_gcs_uri(uri: str) -> GcsUri:
    """Parse a gs://bucket/name URI."""
    if not uri.startswith("gs://"):
        raise ValueError(f"GCS URI must start with gs://: {uri!r}")

    without_scheme = uri.removeprefix("gs://")
    bucket, separator, name = without_scheme.partition("/")
    if not bucket or not separator or not name:
        raise ValueError(f"GCS URI must include bucket and object name: {uri!r}")

    return GcsUri(bucket=bucket, name=name)


def build_gcs_uri(bucket: str, name: str) -> str:
    """Build a gs://bucket/name URI."""
    if not bucket or not name:
        raise ValueError("bucket and name are required")
    return f"gs://{bucket}/{name}"
