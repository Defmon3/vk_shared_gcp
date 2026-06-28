#!/usr/bin/env python3
"""
SPDX-License-Identifier: LicenseRef-NonCommercial-Only
© 2025 github.com/defmon3 — Non-commercial use only. Commercial use requires permission.
Format docstrings according to PEP 287
File: query_runner.py

BigQuery query runner with conflict resume support.
"""

from collections.abc import Sequence
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Protocol

from google.api_core.exceptions import Conflict
from google.api_core.retry import Retry
from google.cloud import bigquery

from vk_shared_gcp.bigquery.identifiers import label_value, make_query_job_id

BigQueryQueryParameter = bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter | bigquery.StructQueryParameter


class AwaitableJob(Protocol):
    """Protocol for a BigQuery job that can be awaited."""

    def result(self, *, timeout: int | float | None = None) -> object:
        """Wait for the job to complete."""


class BigQueryJob(AwaitableJob, Protocol):
    """Protocol for BigQuery query jobs used by this runner."""

    state: str
    error_result: dict[str, object] | None
    num_dml_affected_rows: int | None


class BigQueryClient(Protocol):
    """Protocol for the subset of BigQuery client behavior used by this runner."""

    def get_job(self, job_id: str, *, location: str) -> BigQueryJob:
        """Get an existing query job."""

    def query(
        self,
        query: str,
        *,
        job_config: bigquery.QueryJobConfig,
        job_id: str,
        location: str,
        retry: Retry,
    ) -> BigQueryJob:
        """Submit a query job."""


@dataclass(frozen=True, slots=True)
class BigQueryQueryResult:
    """Result metadata from a completed query job."""

    job_id: str
    skipped_existing_job: bool
    affected_rows: int | None


class BigQueryQueryError(Exception):
    """Raised when a BigQuery job finishes with an error."""

    def __init__(self, job_id: str, error_result: dict[str, object]) -> None:
        """Initialize the query error."""
        self.job_id = job_id
        self.error_result = error_result
        super().__init__(f"BigQuery job {job_id} failed: {error_result}")


class BigQueryQueryTimeoutError(TimeoutError):
    """Raised when a BigQuery job does not finish before the timeout."""

    def __init__(self, job_id: str, timeout_seconds: int | float | None) -> None:
        """Initialize the query timeout error."""
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"BigQuery job {job_id} did not finish within {timeout_seconds} seconds")


class BigQueryQueryRunner:
    """Run BigQuery jobs with stable ids and conflict resume."""

    def __init__(self, client: BigQueryClient) -> None:
        """Initialize the runner with an injected BigQuery client."""
        self._client = client

    def run_query(
        self,
        *,
        sql: str,
        job_id: str,
        labels: dict[str, str],
        query_parameters: Sequence[BigQueryQueryParameter] | None,
        location: str,
        maximum_bytes_billed: int | None,
        timeout_seconds: int | float | None,
    ) -> BigQueryQueryResult:
        """Run a BigQuery query or resume a conflicting existing job."""
        safe_job_id = make_query_job_id(job_id)
        safe_labels = {key: label_value(value) for key, value in labels.items()}
        job_config = bigquery.QueryJobConfig(query_parameters=list(query_parameters or []), labels=safe_labels, maximum_bytes_billed=maximum_bytes_billed)
        skipped_existing_job = False

        try:
            job = self._client.query(sql, job_config=job_config, job_id=safe_job_id, location=location, retry=Retry())
        except Conflict:
            job = self._client.get_job(safe_job_id, location=location)
            skipped_existing_job = True

        self._await_job(job, safe_job_id, timeout_seconds)
        if job.error_result is not None:
            raise BigQueryQueryError(safe_job_id, job.error_result)

        return BigQueryQueryResult(job_id=safe_job_id, skipped_existing_job=skipped_existing_job, affected_rows=job.num_dml_affected_rows)

    @staticmethod
    def _await_job(job: BigQueryJob, job_id: str, timeout_seconds: int | float | None) -> None:
        try:
            job.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            raise BigQueryQueryTimeoutError(job_id, timeout_seconds) from exc
