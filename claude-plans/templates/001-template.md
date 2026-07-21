# Plan 001 — <slice name>

## Context

<Where the repo stands now (what files exist), and what CLAUDE.md says this
project is. Note which CLAUDE.md sections this plan will settle — e.g. Stack and
Commands were left blank and this plan fills them for the first slice.>

**Decisions (confirmed with the user):**

- Language / stack: <chosen, with the reason tied to a constitution rule>
- Scope of slice 001: <the smallest testable slice — what's IN>
- <Any policy/default the model chose on your behalf — state it and flag it so it can be revisited>

## Dependencies

<External libraries this slice uses, each with the WHY and version. "None
(stdlib only)" is a valid, expected entry — do not invent dependencies to fill
this section. Every added library is surface area, so name why it earns its place.>

- <library==version> — <why it's needed>

## Goal of this slice

<One or two sentences: what this slice produces and, just as important, what it
deliberately does NOT do (no I/O, no CLI, no runnable app yet, etc.).>

## Design

### <file> (location)

<The public surface — key function/signature(s), what it exposes.>

- <Design decision, with the WHY (which rule / constraint drives it)>
- <Design decision, with the WHY>
- <Validation / error behavior — what raises, when, and why it's policy in code>

<Note any per-function purpose comments or conventions required by House rules.>

### <test file>

<Test framework choice + why. Then the cases:>

- <case>
- <case>
- <edge / error case>

## Files

- <file> — new, <what it holds>.
- <test file> — new, the cases above.

## Out of scope (parked)

### Planned — intended for this version

- <feature> — later plan (00N)

### Possible — noted, not committed

- <idea that may never be built>

## Follow-ups after implementation (not code changes in this slice)

- Fill CLAUDE.md Stack section: "<...>".
- Fill CLAUDE.md Commands section: "<only commands that work AFTER this slice>".
  (CLAUDE.md is a protected file — propose the exact edit for approval rather
  than editing it silently.)

## Verification

### Outcome — what this slice now does

<One or two plain-language sentences: what the app / code can now do that it
couldn't before this slice, stated so a non-coder could confirm it. E.g.
"There's now a tested function that returns a random quote from the catalog."
For a logic-only slice, say what capability exists in the core, even if there's
no UI yet.>

### Steps — confirm it by hand

Step-by-step (copy-pasteable, in order). Each step lists the command AND its
expected output, so correctness is confirmed by eye.

1. <setup command, e.g. npm install / activate venv> — expected: <installs, no errors>
2. <test command, e.g. npm test / python -m pytest> — expected: <e.g. "6 passed", exit 0>
3. <smoke check — a by-hand confirmation of the happy path> — expected: <printed value>

ONLY list commands that actually work after THIS slice. If the app is not yet
runnable (logic-only slice, no UI/entry point yet), say so explicitly — do NOT
list a dev-server / launch command that has nothing to run. The launch command
arrives with the interface slice that creates the entry point.

For interface slices, the smoke check is a LAUNCH command + expected VISIBLE
result (e.g. "page loads, click shows a quote"), not a printed value.
