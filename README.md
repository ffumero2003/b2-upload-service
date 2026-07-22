# B2 File Uploader

A minimal Flask web app that uploads a file to a Backblaze B2 bucket and returns
the stored file's download URL.

## Features

- Browser upload page at `GET /`: pick a file, click Upload, get a clickable B2
  download link (or the error message if it fails).
- JSON API at `POST /upload`: multipart upload, responds with
  `{fileName, fileId, url}`.
- Upload core is unit-tested fully offline against the b2sdk simulator, so the
  test suite needs no network and no real credentials.

## Requirements

- Python 3
- A Backblaze B2 account
- An existing B2 bucket
- A B2 application key with write access to that bucket

## Backblaze setup

If you do not already have a bucket and key:

1. In the Backblaze B2 console, go to **Buckets** and create a bucket. Note its
   name; that is your `B2_BUCKET_NAME`.
2. Go to **Application Keys** and create a new key, scoped to that bucket, with
   read and write access.
3. The console shows the key's `keyID` and `applicationKey` **once**. Copy both
   before closing the dialog.

Map the console values to the app's environment variables:

| Console field    | Environment variable   |
| ---------------- | ---------------------- |
| `keyID`          | `B2_KEY_ID`            |
| `applicationKey` | `B2_APPLICATION_KEY`   |
| bucket name      | `B2_BUCKET_NAME`       |

The console also shows a `keyName`. It is a human-readable label only and is not
used by this app.

## Setup

From the repo root:

```
python3 -m venv .venv && source .venv/bin/activate
```

Expected: the prompt shows `(.venv)`, and `which python` points inside `.venv`.

```
pip install -r requirements.txt
```

Expected: installs `b2sdk`, `Flask`, `pytest`, and `python-dotenv` with no errors.

## Configuration

The app reads three environment variables. All three are required; if any is
missing, startup fails immediately with a `ValueError` naming the missing ones
rather than failing later as an opaque auth error.

| Variable               | Meaning                                  | Example                            |
| ---------------------- | ---------------------------------------- | ---------------------------------- |
| `B2_KEY_ID`            | The application key's `keyID`            | `0011223344556677889aabb`          |
| `B2_APPLICATION_KEY`   | The application key secret               | `K001xxxxxxxxxxxxxxxxxxxxxxxxxxx`  |
| `B2_BUCKET_NAME`       | Target bucket for uploads                | `my-uploads-bucket`                |

Create a `.env` file in the repo root:

```
B2_KEY_ID=your-key-id
B2_APPLICATION_KEY=your-application-key
B2_BUCKET_NAME=your-bucket-name
```

`.env` is gitignored and holds credentials only. Policy such as size limits or
scope rules belongs in code, not in `.env` — a limit is not a secret.

## Running

```
flask --app app.wsgi run
```

Expected: `Running on http://127.0.0.1:5000`.

Open <http://127.0.0.1:5000/> in a browser to use the upload page.

## API

### `GET /`

Serves the single-page uploader UI (`app/static/index.html`). No credentials are
touched by this route.

### `POST /upload`

Multipart form upload. The file must be sent under the field name `file`.

Success — `200`:

```json
{
  "fileName": "smoke.txt",
  "fileId": "4_z27c88f1d182b150e9860_f1004ba650fe24e6b_d20260722_m000000_c000_v0001_t0000",
  "url": "https://f000.backblazeb2.com/file/my-uploads-bucket/smoke.txt"
}
```

Errors:

| Status | When                                              | Body                                                  |
| ------ | ------------------------------------------------- | ----------------------------------------------------- |
| `400`  | No `file` field, or an empty filename             | `{"error": "No file provided under field 'file'"}`    |
| `400`  | Core validation failed (empty name or empty data) | `{"error": "<message>"}`                              |
| `500`  | The upload itself failed                          | `{"error": "Upload failed"}`                          |

The `500` response never leaks a stack trace to the client.

If the browser sends no content type for the file, the app falls back to B2's
`b2/x-auto`, letting B2 infer the type.

Example:

```
printf 'hello b2' > smoke.txt && curl -s -F file=@smoke.txt http://127.0.0.1:5000/upload
```

Expected: the JSON success body above, with `smoke.txt` now visible in the bucket
and downloadable at `url`.

## Project structure

```
app/
  __init__.py        package marker
  b2_client.py       upload core: Uploader, UploadResult, build_uploader()
  server.py          create_app(uploader) factory: GET / and POST /upload
  wsgi.py            production entry point: loads .env, wires the real uploader
  static/
    index.html       the upload page (inline CSS and JS, no build step)
tests/
  test_b2_client.py  offline core tests against the b2sdk simulator
  test_server.py     endpoint tests with an injected fake uploader
conftest.py          puts the repo root on sys.path for pytest
claude-plans/        numbered implementation plans, written before the code
claude-logs/         iteration logs
requirements.txt     pinned dependencies
```

## Design notes

- **Injection seam.** `create_app(uploader)` in `app/server.py` takes its uploader
  as an argument, so tests inject a fake or a simulator-backed uploader and the
  test path never touches the network or needs credentials.
- **Credential wiring is isolated.** The real, `.env`-backed wiring lives in
  `app/wsgi.py`, not `app/server.py`. Both `flask --app app.server` and pytest's
  `import app.server` set `__name__ == "app.server"`, so an import-time guard
  inside `server.py` could not tell them apart, and test collection would demand
  real B2 keys. Keeping the wiring in a separate entry module avoids that.
- **The core is transport-agnostic.** `app/b2_client.py` knows nothing about HTTP
  or environment variables. `Uploader` receives an already-built b2sdk bucket,
  which is the seam that lets tests hand it a `RawSimulator`-backed bucket.
- **The page adds no logic.** `app/static/index.html` posts to `/upload` and
  renders the response; all validation and storage stay on the server.

## Testing

```
python -m pytest -q
```

Expected: `10 passed`, exit 0.

The suite runs fully offline — no network, no credentials — and covers the happy
path, the core's validation errors, and the endpoint's error status codes.

## Smoke check

A quick by-hand confirmation of the happy path (the test command above is the
full check).

1. Ensure `.env` has `B2_KEY_ID`, `B2_APPLICATION_KEY`, and `B2_BUCKET_NAME` set
   to real values, then start the server:
   `flask --app app.wsgi run` — expected: `Running on http://127.0.0.1:5000`.
2. Browser path — open <http://127.0.0.1:5000/>.
   - INPUT: click the file picker, choose a small local file (e.g. `smoke.txt`),
     click **Upload**.
   - OUTPUT: the page shows `Uploaded smoke.txt` and a clickable download URL
     ending in that file name. Clicking the link downloads the file from B2, and
     the file appears in the bucket.
3. API path — in another terminal:
   `printf 'hello b2' > smoke.txt && curl -s -F file=@smoke.txt http://127.0.0.1:5000/upload`
   - OUTPUT: JSON with `fileName`, a non-empty `fileId`, and a `url` ending in
     `smoke.txt`.

Both paths surface exactly what the tested core guarantees; neither adds logic of
its own.

## Development workflow

Every substantial feature gets a numbered plan in `claude-plans/`, written before
any code for it:

- `001-upload-core-and-endpoint.md` — the B2 upload core and `POST /upload`.
- `002-frontend-upload-page.md` — the upload page and `GET /`.

Bugs that survive three attempts get an iteration log in `claude-logs/`.

## Possible next steps

Not implemented, and not committed to:

- File listing and delete endpoints, plus a UI for them.
- Large-file multipart uploads with a progress bar.
- Drag-and-drop dropzone and multiple-file upload.
- Client-side size and type validation; a "copy link" button.
- Auth and per-user scoping; time-limited (presigned) download links.
