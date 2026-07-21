"""B2 upload core.

Wraps the Backblaze b2sdk so the rest of the app can store a file with one call
and get back the stored file's id, name, and public download URL. The `Uploader`
takes an already-built b2sdk bucket, which is the seam that lets tests inject a
RawSimulator-backed bucket and run fully offline.
"""

import os
from dataclasses import dataclass

from b2sdk.v2 import B2Api, InMemoryAccountInfo


@dataclass
class UploadResult:
    """The outcome of a successful upload.

    Change this when callers (the HTTP layer, a future frontend) need more fields
    from B2 about the stored file, e.g. size or content-type.
    """

    file_id: str
    file_name: str
    url: str


class Uploader:
    """Stores bytes in one B2 bucket.

    Change this when the upload behavior itself must change (naming rules,
    per-upload metadata, large-file handling). It deliberately knows nothing about
    HTTP or env vars so it stays unit-testable against the b2sdk simulator.
    """

    def __init__(self, bucket):
        # Hold the b2sdk bucket the uploads target. Injected so production passes a
        # real bucket and tests pass a simulated one.
        self._bucket = bucket

    def upload(self, file_name, data, content_type="b2/x-auto"):
        """Upload `data` under `file_name` and return an UploadResult.

        Change this when validation rules or the returned fields change. Empty name
        or empty data raise ValueError here (policy in code) rather than letting B2
        reject them with an opaque error later.
        """
        if not file_name:
            raise ValueError("file_name must not be empty")
        if not data:
            raise ValueError("data must not be empty")
        file_version = self._bucket.upload_bytes(
            data, file_name, content_type=content_type
        )
        url = self._bucket.get_download_url(file_name)
        return UploadResult(
            file_id=file_version.id_,
            file_name=file_version.file_name,
            url=url,
        )


def build_uploader():
    """Build the production Uploader from environment credentials.

    Reads B2_KEY_ID, B2_APPLICATION_KEY, and B2_BUCKET_NAME, authorizes against B2,
    and binds an Uploader to the named bucket. Change this when the credential
    source or the B2 realm changes. A missing env var fails fast with a clear
    ValueError instead of surfacing as an auth error mid-request.
    """
    key_id = os.environ.get("B2_KEY_ID")
    application_key = os.environ.get("B2_APPLICATION_KEY")
    bucket_name = os.environ.get("B2_BUCKET_NAME")
    missing = [
        name
        for name, value in (
            ("B2_KEY_ID", key_id),
            ("B2_APPLICATION_KEY", application_key),
            ("B2_BUCKET_NAME", bucket_name),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    b2_api = B2Api(InMemoryAccountInfo())
    b2_api.authorize_account("production", key_id, application_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)
    return Uploader(bucket)
