# Plan 002 — Frontend upload page (GET / serves it)

## Context

Plan 001 built the backend: `app/b2_client.py` (the `Uploader` core +
`build_uploader()`), `app/server.py` (`create_app(uploader)` factory exposing
`POST /upload`), and `app/wsgi.py` (the real, `.env`-backed entry point). Tests
run fully offline (8 passing) against a `FakeUploader` and the b2sdk simulator.

Right now the app has **no frontend and no `GET /`** — a browser hitting `/`
404s; you can only use it via `curl`. Plan 001 parked exactly this slice as
Planned out-of-scope: "Frontend upload page (HTML + JS that POSTs to /upload,
shows the result URL)" and "Serve the frontend from the Flask app (GET /)".
This plan delivers both.

This plan does NOT recreate the skeleton. It reuses `create_app(uploader)` as-is
(the injection seam stays intact), leaves `POST /upload`, `b2_client.py`, and
`wsgi.py` untouched, and hangs one new route + one static file off the existing
factory.

**Decisions (confirmed with the user):**

- Scope: **Minimal** upload page — a single file picker + an Upload button. On
  success it shows the stored filename and a clickable download URL; on error it
  shows the endpoint's error message. Plain HTML/CSS/JS, no build step, no new
  deps. Drag-and-drop, multi-file, copy-link, and progress bars stay parked as
  Possible (from 001).
- The page is **served same-origin by Flask** (`GET /`), so no CORS is needed —
  the JS posts to the same host that served it. (Flagged: chosen to avoid adding
  CORS surface; a separately-hosted frontend would need it.)
- HTML is served as a **static asset**, not a Jinja template. There is no
  server-side dynamic data on the page, so a static file is the honest, simplest
  choice and avoids Jinja `{{ }}`/`{% %}` colliding with JS. (Flagged: pick a
  template engine later only if the page needs server-rendered data.)

## Dependencies

None — reuses the existing Flask + b2sdk stack. Flask serves the static file and
the JS uses the browser-native `fetch` + `FormData`.

## Goal of this feature

Add a browser page at `GET /` that lets a person pick one file, click Upload, and
see the resulting B2 download URL (or an error) — wiring the existing `POST
/upload` endpoint to a UI. It adds no new upload logic; it only makes the core's
existing `UploadResult` visible in a browser.

## Design

### `app/static/index.html` (new)

A single self-contained page (inline `<style>` + inline `<script>`, no external
assets, no build step):

- A `<form>` with `<input type="file" name="file" id="file">` and a submit
  button, plus an empty `<div id="result">` for output.
- On submit: `preventDefault`, build `FormData` from the file input, `fetch('/upload', { method: 'POST', body: form })`.
- Parse the JSON response and branch on `response.ok`:
  - success -> render the returned `fileName` and an `<a href="url">url</a>`
    clickable link (keys `fileName` / `fileId` / `url`, matching the endpoint
    exactly).
  - non-2xx -> render the response's `error` string.
  - network/throw -> render a generic "Upload failed" message.
- Guard: if no file is selected, show a "choose a file" message and skip the
  fetch (mirrors the endpoint's own 400 so the user gets instant feedback).
- The JS deliberately avoids Jinja delimiters (`${...}` template literals only),
  so serving it as a raw static file is safe.

Why static/inline: no dynamic server data, no dependency, trivially testable, and
the whole UI ships in one file the smoke check can open directly.

### `app/server.py` (modified — one route added inside `create_app`)

Add a root route to the **existing** factory; do not change its signature or the
`/upload` route:

```python
@app.get("/")
def index():
    """Serve the single-page uploader UI.

    Change this when the frontend entry point moves or needs server-rendered
    data. Serves the static page so a browser has something to POST /upload from.
    """
    return app.send_static_file("index.html")
```

- `Flask(__name__)` (with `__name__ == "app.server"`) already resolves its static
  folder to `app/static/`, so `send_static_file("index.html")` finds the new file
  with the correct `text/html` mimetype — no extra config.
- `create_app(uploader)` still takes the injected uploader; the new route needs no
  uploader, so the test path stays credential-free and offline. `wsgi.py` and
  `b2_client.py` are untouched.

### `tests/test_server.py` (modified — 2 tests added)

Reuse the existing `FakeUploader` + `_client(uploader)` helper (no new fixtures):

- `test_index_served_as_html` — `GET /` returns 200 and a `text/html` content
  type, and the uploader is never called (`fake.calls == []`).
- `test_index_wires_upload_endpoint` — the page body contains the markers the
  frontend depends on: a file input (`type="file"`), the `/upload` target, and a
  reference to the `url` result key — so a regression that breaks the wiring fails
  a test, not just the smoke check.

These stay offline (Flask test client, injected fake), consistent with 001.

## Files

- `app/static/index.html` — new, the minimal upload page (inline CSS + JS).
- `app/server.py` — modified, add the `GET /` route inside `create_app`; no other
  changes.
- `tests/test_server.py` — modified, add the 2 `GET /` tests above.

## Out of scope (parked)

### Planned — intended for this version

- None. With this slice, 001's Planned out-of-scope list (frontend page + `GET /`)
  is emptied. Per claude.md, "Done" = the Planned list is empty across all plans.

### Possible — noted, not committed

- Drag-and-drop dropzone; multiple-file / batch upload.
- "Copy link" button and an upload-in-progress state (disabled button, spinner).
- Client-side size/type validation and a progress bar for large files.
- File listing / delete UI; time-limited (presigned) links.

## Follow-ups after implementation (not code changes in this slice)

- **claude.md Commands** (protected file — propose the exact edit for approval):
  the Test line's expected output changes from `# expected: 8 passed` to
  `# expected: 10 passed` once the 2 new tests land.
- No new run command: `flask --app app.wsgi run` already serves the page; only the
  reachable surface grows (now also `GET /`).

## Verification

### Outcome — what this feature now does

Before this slice, opening the app in a browser gave a 404 — uploads were
`curl`-only. Now visiting `http://127.0.0.1:5000/` shows an upload page: pick a
file, click Upload, and the page displays the stored file's name and a clickable
Backblaze download link (or the error message if it fails).

### Steps — confirm it by hand

1. `python -m pytest -q` — expected: `10 passed`, exit 0. (Full offline check: the
   b2sdk-simulator core tests, the `POST /upload` wiring tests, and the 2 new
   `GET /` page tests. No network, no credentials.)
2. Ensure `.env` has `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`, then
   start the server: `flask --app app.wsgi run` — expected:
   "Running on http://127.0.0.1:5000".
3. Smoke check (GUI, happy path) — open `http://127.0.0.1:5000/` in a browser.
   - INPUT: click the file picker, choose a small local file (e.g. `smoke.txt`),
     click **Upload**.
   - OUTPUT (expected): the page shows the stored file name and a clickable
     download URL ending in that file name; clicking the link downloads the file
     from B2, and the file appears in the bucket.
   This matches what the tested `POST /upload` core already guarantees — the page
   adds no new logic, it just makes the endpoint's `{fileName, fileId, url}`
   response visible in the browser.
