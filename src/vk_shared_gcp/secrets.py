#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: secrets.py

Secret Manager resolution primitives.
"""

import re
from typing import Protocol, cast

from google.cloud.secretmanager import SecretManagerServiceClient


class SecretResolutionError(ValueError):
    """Raised when a Secret Manager version has no usable payload."""


class SecretPayload(Protocol):
    """Protocol for a Secret Manager response payload."""

    data: bytes


PROJECT_RESOURCE_SEGMENT = re.compile(r"^[A-Za-z0-9_.:-]+$")
SECRET_NAME = re.compile(r"^[A-Za-z0-9_-]{1,255}$")
SECRET_VERSION = re.compile(r"^(latest|[0-9]+)$")


def validate_resource_segment(field: str, value: str, pattern: re.Pattern[str]) -> None:
    """Reject Secret Manager resource path components that could alter the resolved path."""
    if not pattern.fullmatch(value):
        raise ValueError(f"{field} is not a valid Secret Manager resource component: {value!r}")


def resolve_secret(client: SecretManagerServiceClient, *, project: str, secret_name: str, version: str = "latest", timeout_seconds: float) -> str:
    """Resolve a Secret Manager version to a non-empty UTF-8 string."""
    validate_resource_segment("project", project, PROJECT_RESOURCE_SEGMENT)
    validate_resource_segment("secret_name", secret_name, SECRET_NAME)
    validate_resource_segment("version", version, SECRET_VERSION)
    path = f"projects/{project}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": path}, timeout=timeout_seconds)
    payload = cast(SecretPayload | None, getattr(response, "payload", None))
    if payload is None or not payload.data:
        raise SecretResolutionError(f"Secret {path} has no payload")

    value = payload.data.decode("utf-8").strip()
    if not value:
        raise SecretResolutionError(f"Secret {path} is empty")
    return value
