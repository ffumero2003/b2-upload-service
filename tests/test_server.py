"""Tests for the POST /upload endpoint.

Injects a fake uploader via create_app so the wiring (request parsing, status
codes, JSON shape) is verified offline, with no B2 dependency.
"""

import io

import pytest

from app.b2_client import UploadResult
from app.server import create_app


class FakeUploader:
    """Records the last upload call and returns a canned result.

    Change this when the Uploader interface changes. `raises` lets a test force the
    failure path without any real backend.
    """

    def __init__(self, raises=None):
        self.calls = []
        self._raises = raises

    def upload(self, file_name, data, content_type):
        """Stand in for Uploader.upload, capturing args or raising on demand."""
        self.calls.append((file_name, data, content_type))
        if self._raises is not None:
            raise self._raises
        return UploadResult(
            file_id="fake-id-123",
            file_name=file_name,
            url=f"https://example.com/file/test-bucket/{file_name}",
        )


def _client(uploader):
    """Build a Flask test client around the given uploader."""
    return create_app(uploader).test_client()


def test_upload_success_returns_json():
    """A posted file returns 200 with the uploader's result and passes bytes through."""
    fake = FakeUploader()
    client = _client(fake)

    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"hello b2"), "hello.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["fileName"] == "hello.txt"
    assert body["fileId"] == "fake-id-123"
    assert body["url"].endswith("/hello.txt")
    assert fake.calls[0][0] == "hello.txt"
    assert fake.calls[0][1] == b"hello b2"


def test_upload_missing_file_returns_400():
    """No file field yields 400 and an error message, without calling the uploader."""
    fake = FakeUploader()
    client = _client(fake)

    response = client.post("/upload", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert fake.calls == []


def test_upload_uploader_failure_returns_500():
    """An unexpected uploader error yields 500 with a generic error, no stack trace."""
    fake = FakeUploader(raises=RuntimeError("b2 exploded"))
    client = _client(fake)

    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"data"), "boom.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    body = response.get_json()
    assert "error" in body
    assert "b2 exploded" not in body["error"]
