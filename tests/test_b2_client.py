"""Offline tests for the upload core.

Runs against b2sdk's RawSimulator so no network and no real credentials are used.
The simulator behaves like B2 for create-bucket / upload / download, which lets us
assert the real Uploader code path end to end.
"""

import io

import pytest
from b2sdk.v2 import B2Api, B2HttpApiConfig, InMemoryAccountInfo, RawSimulator

from app.b2_client import Uploader, build_uploader


@pytest.fixture
def uploader():
    """Yield an Uploader bound to a simulated B2 bucket.

    Change this when the b2sdk simulator setup changes. Creating a fresh simulated
    account + public bucket per test keeps cases isolated.
    """
    account_info = InMemoryAccountInfo()
    b2_api = B2Api(
        account_info, api_config=B2HttpApiConfig(_raw_api_class=RawSimulator)
    )
    raw_simulator = b2_api.session.raw_api
    application_key_id, master_key = raw_simulator.create_account()
    b2_api.authorize_account("production", application_key_id, master_key)
    bucket = b2_api.create_bucket("test-bucket", "allPublic")
    return Uploader(bucket)


def test_upload_returns_result_fields(uploader):
    """A successful upload reports the file name, a real id, and a matching URL."""
    result = uploader.upload("hello.txt", b"hello b2", "text/plain")
    assert result.file_name == "hello.txt"
    assert result.file_id
    assert "hello.txt" in result.url


def test_uploaded_bytes_are_stored(uploader):
    """The bytes read back from the simulated bucket match what was uploaded."""
    payload = b"the quick brown fox"
    result = uploader.upload("fox.txt", payload, "text/plain")

    buffer = io.BytesIO()
    uploader._bucket.download_file_by_id(result.file_id).save(buffer)
    assert buffer.getvalue() == payload


def test_empty_file_name_raises(uploader):
    """An empty file name is rejected in code, not deferred to B2."""
    with pytest.raises(ValueError):
        uploader.upload("", b"data", "text/plain")


def test_empty_data_raises(uploader):
    """Empty data is rejected in code, not deferred to B2."""
    with pytest.raises(ValueError):
        uploader.upload("empty.txt", b"", "text/plain")


def test_build_uploader_missing_env_raises(monkeypatch):
    """build_uploader fails fast and clearly when a credential env var is absent."""
    monkeypatch.delenv("B2_KEY_ID", raising=False)
    monkeypatch.delenv("B2_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("B2_BUCKET_NAME", raising=False)
    with pytest.raises(ValueError) as exc_info:
        build_uploader()
    assert "B2_KEY_ID" in str(exc_info.value)
