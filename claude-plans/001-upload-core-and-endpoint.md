# Plan 001 — B2 upload core + POST /upload endpoint

## Context

This repo is a greenfield "simple file uploader web app backed by Backblaze B2"
(per `claude.md`). At the start of this plan the repo holds only governance files
(the `claude.md` constitution, plan templates, log convention) and a `.env` with
real B2 credentials (`keyID`, `keyName = ai-interview-felipe-fumero`,
`applicationKey`). There is no source code, no `.gitignore`, no chosen stack, and
no numbered plan.

`claude.md` leaves **Stack** and **Commands** blank on purpose — the first slice
settles them. This plan does that: it picks the stack and delivers the first
testable, runnable piece of the app.

**Decisions (confirmed with the user):**

- Language / stack: **Python + `b2sdk`** (official Backblaze SDK). Chosen because
  the constitution's mandated `.gitignore` (`__pycache__/`, `*.pyc`) points at
  Python, and because `b2sdk` ships a `RawSimulator` that lets the upload core be
  unit-tested **fully offline** — no network and no real keys in the test path,
  which satisfies the "run tests before done" rule cheaply.
- Scope of slice 001: the **upload core** (authorize with B2, upload bytes, return
  file id / name / download URL) **plus a `POST /upload` HTTP endpoint** that wraps
  it. No frontend yet.
- Web framework: **Flask** (model's choice, flagged for revisit). Simplest thing
  that serves one multipart endpoint and has a first-class test client. FastAPI is
  the obvious alternative if async / OpenAPI is wanted later.
- **Bucket name is required config** and is NOT currently in `.env` (only the key
  triplet is). The code will read `B2_BUCKET_NAME` from the environment; the user
  must supply the target bucket name (see Follow-ups). Treated as deployment config
  via env var, not hardcoded (account-specific) and not a secret.

## Dependencies

- `b2sdk` (latest 2.x) — B2 authorize + upload; also provides `RawSimulator` /
  `InMemoryAccountInfo` for offline tests. Earns its place as the official,
  supported B2 client (vs. hand-rolling the B2 native API).
- `Flask` (latest 3.x) — the `POST /upload` endpoint and its `app.test_client()`
  for endpoint tests.
- `pytest` (latest) — test runner.
- `python-dotenv` (latest) — load `.env` credentials for the real run / smoke check
  only (flagged: convenience; could be replaced by manual `export`).

## Goal of this slice

Produce a tested upload core and a running server that accepts one file over
`POST /upload` (multipart) and returns JSON `{fileName, fileId, url}` after storing
it in the B2 bucket. It deliberately does NOT include any frontend/HTML, no file
listing, no delete, no auth, no progress/large-file multipart handling.

## Design

Key idea for testability: **dependency injection** at two seams so nothing in the
test path touches the network.

### `app/b2_client.py` (new)

Public surface:

- `build_uploader() -> Uploader` — reads `B2_KEY_ID`, `B2_APPLICATION_KEY`,
  `B2_BUCKET_NAME` from env, authorizes a real `B2Api`, returns an `Uploader` bound
  to that bucket. This is the production wiring.
- `class Uploader` — wraps a `b2sdk` bucket. Method:
  `upload(file_name: str, data: bytes, content_type: str) -> UploadResult`.
- `class UploadResult` (dataclass) — `file_id`, `file_name`, `url` (public download
  URL via `b2_api.get_download_url_for_file_name`).

Design decisions + why:

- `Uploader` takes an already-built `b2sdk` bucket, so tests can hand it a
  `RawSimulator`-backed bucket and production hands it a real one. This is the seam
  that keeps tests offline (constitution: tests must run before done, cheaply).
- Credentials come only from env vars (House rule: secrets in `.env`, never
  hardcoded). Missing credential -> raise a clear `ValueError` at `build_uploader()`
  time (policy in code, fail fast).
- Empty `file_name` or empty `data` -> raise `ValueError` (validation is policy in
  code, not left to B2 to reject obscurely).

Every function/method gets a purpose comment (what + when-you'd-change-it), per
House rules.

### `app/server.py` (new)

- `create_app(uploader) -> Flask` — app factory taking an `Uploader` (or any object
  with `.upload(...)`), so tests inject a fake/simulator-backed uploader and no
  network is hit.
- Module-level `app = create_app(build_uploader())` — the runnable entry point so
  `flask --app app.server run` works for the smoke check.
- Route `POST /upload`:
  - Reads the multipart file field `file`. Missing/empty -> `400` JSON `{error}`.
  - Calls `uploader.upload(filename, bytes, content_type)`.
  - Success -> `200` JSON `{fileName, fileId, url}`.
  - Uploader raises -> `500` JSON `{error}` (no stack trace leaked).

### `tests/test_b2_client.py` (new) — pytest

Uses `b2sdk` `InMemoryAccountInfo` + `RawSimulator` (offline). A fixture creates a
simulated account + bucket and yields an `Uploader`.

- uploads bytes -> `UploadResult` has the given `file_name`, a non-empty `file_id`,
  and a `url` containing the file name.
- re-download / verify the stored bytes match what was uploaded (via simulator).
- empty file name raises `ValueError`.
- empty data raises `ValueError`.
- `build_uploader()` with a missing env var raises `ValueError` (monkeypatched env).

### `tests/test_server.py` (new) — pytest + Flask test client

Injects a fake uploader (records calls, returns a canned `UploadResult`) via
`create_app`, so it's offline and asserts wiring only.

- `POST /upload` with a file -> `200`, JSON `{fileName, fileId, url}` matching the
  fake's result; fake received the right filename + bytes.
- `POST /upload` with no file field -> `400` JSON with `error`.
- `POST /upload` where the uploader raises -> `500` JSON with `error`.

## Files

- `app/__init__.py` — new, empty package marker.
- `app/b2_client.py` — new, the `Uploader` core + `build_uploader()`.
- `app/server.py` — new, Flask app factory + `POST /upload` + runnable `app`.
- `tests/test_b2_client.py` — new, offline simulator tests above.
- `tests/test_server.py` — new, test-client tests above.
- `requirements.txt` — new, the four dependencies.
- `.gitignore` — new (constitution mandate): `.DS_Store`, `__pycache__/`, `*.pyc`, `.env`.

## Out of scope (parked)

### Planned — intended for this version

- Frontend upload page (HTML + JS that POSTs to `/upload`, shows the result URL) — plan 002.
- Serve the frontend from the Flask app (`GET /`) — plan 002.

### Possible — noted, not committed

- File listing / delete endpoints.
- Large-file / multipart-chunk uploads + progress.
- Multiple-file and drag-and-drop upload.
- Auth / per-user scoping; time-limited (presigned) download links.

## Follow-ups after implementation (not code changes in this slice)

- **Bucket name**: add `B2_BUCKET_NAME=<bucket>` to `.env` (the user provides the
  target bucket). `.env` is a secret file — propose the exact line for approval
  rather than editing it silently. Also normalize the existing `.env` keys to the
  names the code reads: `B2_KEY_ID`, `B2_APPLICATION_KEY` (currently `keyID` /
  `applicationKey`); `keyName` is unused by the code.
- Fill `claude.md` **Stack**: "Python 3.x, Flask, b2sdk; pytest for tests."
- Fill `claude.md` **Commands**: `python -m venv .venv && source .venv/bin/activate`,
  `pip install -r requirements.txt`, `python -m pytest -q`, `flask --app app.wsgi run`.
  (`claude.md`/CLAUDE.md is protected — propose the exact edit for approval.)

## Verification

### Outcome — what this slice now does

There is now a running web server with a `POST /upload` endpoint: send it a file
and it stores that file in the Backblaze B2 bucket and returns JSON with the stored
file's name, id, and a download URL. The upload logic is covered by offline tests.

### Steps — confirm it by hand

1. `python -m venv .venv && source .venv/bin/activate` — expected: venv activates,
   prompt shows `(.venv)`; `which python` points inside `.venv`.
2. `pip install -r requirements.txt` — expected: installs b2sdk, Flask, pytest,
   python-dotenv with no errors.
3. `python -m pytest -q` — expected: all tests pass, e.g. `8 passed`, exit 0.
   (This is the full check — happy path, validation errors, and endpoint error
   codes — and it runs offline against the b2sdk simulator + Flask test client.)
4. Ensure `.env` has `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME` set
   (real creds + a real bucket). Then start the server:
   `flask --app app.wsgi run` — expected: "Running on http://127.0.0.1:5000".
5. Smoke check (happy path) — in another terminal:
   `printf 'hello b2' > smoke.txt && curl -s -F file=@smoke.txt http://127.0.0.1:5000/upload`
   - INPUT: POST the file `smoke.txt`.
   - OUTPUT (expected): JSON like
     `{"fileName":"smoke.txt","fileId":"<non-empty id>","url":"https://.../smoke.txt"}`,
     and `smoke.txt` is now visible in the B2 bucket (and downloadable at `url`).
   This matches what the tested core guarantees — the endpoint adds no new logic,
   just makes the core's `UploadResult` visible over HTTP.
