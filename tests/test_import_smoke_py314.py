import importlib
import sys

MODULES = [
    "google.cloud.bigquery",
    "google.cloud.secretmanager",
    "google.cloud.storage",
    "vk_shared_gcp.bigquery.clients",
    "vk_shared_gcp.bigquery.identifiers",
    "vk_shared_gcp.bigquery.query_runner",
    "vk_shared_gcp.bigquery.streaming",
    "vk_shared_gcp.gcs.storage",
    "vk_shared_gcp.gcs.uri",
    "vk_shared_gcp.secrets",
]


def test_google_and_shared_imports_under_python_314() -> None:
    for module in MODULES:
        importlib.import_module(module)

    assert sys.version_info[:2] == (3, 14)
