#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: streaming.py

BigQuery streaming insert chunking primitives.
"""

from collections.abc import Iterator, Mapping, Sequence

STREAMING_INSERT_CHUNK_SIZE = 500
BIGQUERY_TIMEOUT_SECONDS = 300


class BigQueryInsertError(Exception):
    """Raised when BigQuery streaming insert returns row errors."""

    def __init__(self, destination: str, errors: list[dict[str, object]]) -> None:
        """Initialize the insert error."""
        self.destination = destination
        self.errors = errors
        super().__init__(f"BigQuery insert into {destination} failed for {len(errors)} rows")


def chunk_rows(rows: Sequence[Mapping[str, object]], row_ids: Sequence[str] | None) -> Iterator[tuple[list[Mapping[str, object]], list[str] | None]]:
    """Yield aligned 500-row BigQuery insert chunks."""
    if row_ids is not None and len(row_ids) != len(rows):
        raise ValueError("row_ids length must match rows length")

    for start in range(0, len(rows), STREAMING_INSERT_CHUNK_SIZE):
        end = start + STREAMING_INSERT_CHUNK_SIZE
        chunk = list(rows[start:end])
        chunk_ids = list(row_ids[start:end]) if row_ids is not None else None
        yield chunk, chunk_ids
