#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: identifiers.py

BigQuery identifier and label helpers.
"""

import hashlib
import re

SQL_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
QUERY_JOB_ID_LIMIT = 1024
QUERY_JOB_HASH_LENGTH = 16
LABEL_VALUE_LIMIT = 63


def validate_sql_identifier(field: str, value: str) -> None:
    """Validate a BigQuery project, dataset, table, or field identifier component."""
    if not SQL_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must match {SQL_IDENTIFIER_PATTERN.pattern}: {value!r}")


def make_query_job_id(raw_job_id: str) -> str:
    """Build a BigQuery-safe job id preserving injectivity when truncated."""
    safe_job_id = re.sub(r"[^A-Za-z0-9_-]", "_", raw_job_id)
    if not safe_job_id:
        safe_job_id = "query"
    if len(safe_job_id) <= QUERY_JOB_ID_LIMIT:
        return safe_job_id

    digest = hashlib.sha256(raw_job_id.encode("utf-8")).hexdigest()[:QUERY_JOB_HASH_LENGTH]
    prefix_limit = QUERY_JOB_ID_LIMIT - QUERY_JOB_HASH_LENGTH - 1
    return f"{safe_job_id[:prefix_limit]}_{digest}"


def label_value(value: str) -> str:
    """Build a BigQuery label value."""
    cleaned = re.sub(r"[^a-z0-9_-]", "_", value.lower()).strip("_")
    if not cleaned:
        return "unknown"
    return cleaned[:LABEL_VALUE_LIMIT]
