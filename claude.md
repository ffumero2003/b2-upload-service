# CLAUDE.md

## Overview

Build a simple file uploader web app backed by Backblaze B2. require a small backend and front end. I will give you the application keys(keyId, keyName, applicationKey)

## Stack

- Python 3 + Flask (HTTP) + b2sdk 2.x (Backblaze B2). pytest for tests; python-dotenv loads .env.
- Deps pinned in requirements.txt. No lint tool yet (add when a slice earns one).

## Commands

- Setup:  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
- Test:   python -m pytest -q          # expected: 8 passed
- Run:    flask --app app.wsgi run     # needs B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME in .env
- Lint:   none configured yet.

## Verification

- End every slice with the exact commands to reproduce it myself:
  1. the test command, and
  2. a manual smoke-check command I can run by hand.
- Both must be copy-pasteable and runnable as-is from the repo root.
- Each command is shown with its EXPECTED output, so I can confirm correctness by eye,
  not just that the command ran (e.g. "12 passed", "prints 2").
- Every numbered plan's Verification section carries these same two commands.
- The smoke check is a spot-check, not full coverage. The test command must be the one
  that exercises everything (all options and error cases); the manual smoke-check is only
  a quick by-hand confirmation of the happy path.
- For interface slices without command-line output (e.g. a GUI), the smoke check is
  a launch command plus the expected visible result (e.g. "window opens, shows a
  streak of 2"), instead of a printed value.
- For any interface slice (CLI or GUI), the smoke check states the intended INPUT
  (the action taken) and the intended OUTPUT (what should result), so I can confirm
  the interface wires to the core correctly:
  - CLI example — input: `habit done read` after marking Jul 19-20; output: prints
    "streak: 2".
  - GUI example — input: click "read", then "Mark done" on Jul 20 (Jul 19 already
    marked); output: the streak label updates to "2".
- The intended output must match what the tested core already guarantees — the
  interface adds no new logic, so its expected result is just the core's result made
  visible.

## Rules

- Injection seam: the Flask factory create_app(uploader) takes its uploader as an
  argument. The real, credential-backed wiring lives in app/wsgi.py, built from .env.
  This keeps the test path offline and credential-free (tests inject a fake or a
  b2sdk RawSimulator-backed uploader).
- B2 core logic (app/b2_client.py) knows nothing about HTTP or env vars, so it stays
  unit-testable against the b2sdk simulator without a network or real keys.

## What NOT to do

- Do NOT build the credential-requiring app at module-import time in a module that
  tests import (e.g. app/server.py). Both `flask --app app.server` and pytest's
  `import app.server` set __name__ == "app.server", so an import-time guard can't
  tell them apart, and test collection would demand real B2 keys. Keep env-backed
  wiring in a separate entry module (app/wsgi.py). Cost paid once during slice 001.

## Protected files

- CLAUDE.md

## House rules

- No emojis in code, comments, or docs.
- Secrets live in .env (credentials only). Never hardcoded, never in a plan file, never committed.
- Policy (limits, scope rules) lives in code, not .env — a limit is not a secret.
- Run tests before calling anything done.

## Git

- Never run git add, commit, push, rebase, or gh pr create unless explicitly asked this turn.
- Edit files freely; suggest commands I can run.
- Commit messages naming a plan use the format `Plan 00N: <description>` so history maps to the numbered plans.

## Project setup

- At project start, create a .gitignore covering OS and language junk plus secrets:
  .DS_Store, **pycache**/, \*.pyc, .env
- Never create a .env unless the project has real secrets. If it does, it must be
  gitignored and hold credentials only (policy lives in code, not .env).

## Environment

- Never install packages outside the activated venv. Verify with `which python` before pip install.

## Docs

- Do not create documentation files unless asked.

## Workflow conventions

- Every substantial feature gets its own numbered plan in claude-plans/ as 00N-name.md, written before any code.
- Iteration logs go in claude-logs/, one per bug that survives 3 attempts.
- Out of scope splits into Planned (committed for this version) and Possible (noted, not committed).
- "Done" = the Planned out-of-scope list is empty across all plans. Possible items never block done.
- NO EXCEPTIONS: every plan must be written to claude-plans/00N-name.md as a real
  committed file in the repo BEFORE any code for that plan is written. The internal
  plan-mode preview is not sufficient — if the numbered file is not on disk in
  claude-plans/, the plan does not exist and implementation must not begin.
- Before implementing any plan, confirm the claude-plans/00N-\*.md file exists. If it
  does not, stop and create it first.
