import pytest

from vk_shared_gcp.bigquery.identifiers import label_value, make_query_job_id, validate_sql_identifier


def test_validate_sql_identifier_accepts_expected_values() -> None:
    validate_sql_identifier("table", "owner_candidate_queue")
    validate_sql_identifier("project", "vk8-prod")


def test_validate_sql_identifier_rejects_dotted_values() -> None:
    with pytest.raises(ValueError):
        validate_sql_identifier("table", "dataset.table")


def test_make_query_job_id_truncates_with_hash_suffix() -> None:
    first = make_query_job_id("a" * 1100)
    second = make_query_job_id(("a" * 1099) + "b")

    assert len(first) <= 1024
    assert len(second) <= 1024
    assert first != second
    assert first[-17] == "_"


def test_make_query_job_id_sanitizes_empty_value() -> None:
    assert make_query_job_id("...") == "___"
    assert make_query_job_id("") == "query"


def test_label_value_sanitizes_and_caps_values() -> None:
    assert label_value("VK Step 1") == "vk_step_1"
    assert label_value("!!!") == "unknown"
    assert len(label_value("a" * 100)) == 63
