#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: clients.py

BigQuery client builders.
"""

from google.cloud import bigquery


def build_bigquery_client(project: str, location: str) -> bigquery.Client:
    """Build a BigQuery client with a default job location."""
    return bigquery.Client(project=project, location=location)
