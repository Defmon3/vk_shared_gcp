from concurrent.futures import TimeoutError as FuturesTimeoutError

import pytest
from google.api_core.exceptions import Conflict
from google.api_core.retry import Retry
from google.cloud import bigquery

from vk_shared_gcp.bigquery.query_runner import BigQueryQueryError, BigQueryQueryRunner, BigQueryQueryTimeoutError


class FakeJob:
    def __init__(self, *, affected_rows: int | None = None, error_result: dict[str, object] | None = None, timeout: bool = False) -> None:
        self.state = "DONE"
        self.error_result = error_result
        self.num_dml_affected_rows = affected_rows
        self.timeout = timeout
        self.result_timeouts: list[int | float | None] = []

    def result(self, *, timeout: int | float | None = None) -> object:
        self.result_timeouts.append(timeout)
        if self.timeout:
            raise FuturesTimeoutError
        return object()


class FakeClient:
    def __init__(self, *, query_job: FakeJob | None = None, existing_job: FakeJob | None = None, conflict: bool = False) -> None:
        self.query_job = query_job
        self.existing_job = existing_job
        self.conflict = conflict
        self.query_calls: list[tuple[str, str, str, Retry, bigquery.QueryJobConfig]] = []
        self.get_job_calls: list[tuple[str, str]] = []

    def query(self, query: str, *, job_config: bigquery.QueryJobConfig, job_id: str, location: str, retry: Retry) -> FakeJob:
        self.query_calls.append((query, job_id, location, retry, job_config))
        if self.conflict:
            raise Conflict("already exists")
        if self.query_job is None:
            raise AssertionError("query_job is required")
        return self.query_job

    def get_job(self, job_id: str, *, location: str) -> FakeJob:
        self.get_job_calls.append((job_id, location))
        if self.existing_job is None:
            raise AssertionError("existing_job is required")
        return self.existing_job


def test_run_query_returns_affected_rows() -> None:
    job = FakeJob(affected_rows=7)
    client = FakeClient(query_job=job)
    runner = BigQueryQueryRunner(client)

    result = runner.run_query(
        sql="select 1",
        job_id="job.1",
        labels={"Service": "Owner Worker"},
        query_parameters=[],
        location="EU",
        maximum_bytes_billed=10,
        timeout_seconds=4,
    )

    assert result.job_id.startswith("job_1_")
    assert result.skipped_existing_job is False
    assert result.affected_rows == 7
    assert job.result_timeouts == [4]
    assert client.query_calls[0][1] == result.job_id
    assert client.query_calls[0][4].labels == {"Service": "owner_worker"}
    assert client.query_calls[0][4].maximum_bytes_billed == 10


def test_run_query_resumes_conflicting_job_without_concrete_query_job() -> None:
    existing_job = FakeJob(affected_rows=3)
    client = FakeClient(existing_job=existing_job, conflict=True)
    runner = BigQueryQueryRunner(client)

    result = runner.run_query(
        sql="select 1",
        job_id="job-1",
        labels={},
        query_parameters=None,
        location="EU",
        maximum_bytes_billed=None,
        timeout_seconds=5,
    )

    assert result.skipped_existing_job is True
    assert result.affected_rows == 3
    assert len(client.get_job_calls) == 1
    assert client.get_job_calls[0][0].startswith("job-1_")
    assert client.get_job_calls[0][1] == "EU"


def test_run_query_raises_on_job_error() -> None:
    job = FakeJob(error_result={"reason": "invalid"})
    client = FakeClient(query_job=job)
    runner = BigQueryQueryRunner(client)

    with pytest.raises(BigQueryQueryError) as exc_info:
        runner.run_query(sql="bad", job_id="bad", labels={}, query_parameters=None, location="EU", maximum_bytes_billed=None, timeout_seconds=1)

    assert exc_info.value.job_id.startswith("bad_")


def test_run_query_raises_timeout_with_job_id() -> None:
    job = FakeJob(timeout=True)
    client = FakeClient(query_job=job)
    runner = BigQueryQueryRunner(client)

    with pytest.raises(BigQueryQueryTimeoutError) as exc_info:
        runner.run_query(sql="select 1", job_id="slow", labels={}, query_parameters=None, location="EU", maximum_bytes_billed=None, timeout_seconds=1)

    assert exc_info.value.job_id.startswith("slow_")


def test_run_query_job_id_changes_when_sql_changes() -> None:
    first = BigQueryQueryRunner.content_bound_job_id("job", "select 1", {}, None, None)
    second = BigQueryQueryRunner.content_bound_job_id("job", "select 2", {}, None, None)

    assert first != second
    assert first.startswith("job_")
    assert second.startswith("job_")
