#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: secrets.py

Secret Manager resolution primitives.
"""

from typing import Protocol, cast

from google.cloud.secretmanager import SecretManagerServiceClient


class SecretResolutionError(ValueError):
    """Raised when a Secret Manager version has no usable payload."""


class SecretPayload(Protocol):
    """Protocol for a Secret Manager response payload."""

    data: bytes


def resolve_secret(client: SecretManagerServiceClient, *, project: str, secret_name: str, version: str = "latest", timeout_seconds: float) -> str:
    """Resolve a Secret Manager version to a non-empty UTF-8 string."""
    path = f"projects/{project}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": path}, timeout=timeout_seconds)
    payload = cast(SecretPayload | None, getattr(response, "payload", None))
    if payload is None or not payload.data:
        raise SecretResolutionError(f"Secret {path} has no payload")

    value = payload.data.decode("utf-8").strip()
    if not value:
        raise SecretResolutionError(f"Secret {path} is empty")
    return value
