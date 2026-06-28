import pytest

from vk_shared_gcp.bigquery.streaming import (
    STREAMING_INSERT_CHUNK_SIZE,
    BigQueryInsertError,
    chunk_rows,
)


def test_chunk_rows_splits_rows_and_ids() -> None:
    rows = [{"id": str(index)} for index in range(STREAMING_INSERT_CHUNK_SIZE + 1)]
    row_ids = [f"row-{index}" for index in range(STREAMING_INSERT_CHUNK_SIZE + 1)]

    chunks = list(chunk_rows(rows, row_ids))

    assert [len(chunk) for chunk, _ in chunks] == [500, 1]
    assert chunks[0][1] == row_ids[:500]
    assert chunks[1][1] == row_ids[500:]


def test_chunk_rows_accepts_missing_row_ids() -> None:
    rows = [{"id": "1"}]

    assert list(chunk_rows(rows, None)) == [(rows, None)]


def test_chunk_rows_rejects_mismatched_row_ids() -> None:
    with pytest.raises(ValueError):
        list(chunk_rows([{"id": "1"}], []))


def test_bigquery_insert_error_carries_destination_and_errors() -> None:
    errors = [{"index": 1}]

    exc = BigQueryInsertError("dataset.table", errors)

    assert exc.destination == "dataset.table"
    assert exc.errors == errors
