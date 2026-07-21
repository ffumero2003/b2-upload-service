# Plan 00N — <feature name>

## Context

<Where the repo stands now — what earlier plans (001, 002...) already built that
this one depends on. What in CLAUDE.md this feature touches. The base skeleton
already exists, so this plan does NOT recreate it.>

**Decisions (confirmed with the user):**

- Scope of this feature: <what's IN>
- <Any policy/default chosen on your behalf — state and flag it>

## Dependencies

<New external libraries this feature adds, each with the WHY and version. "None —
reuses existing stack" is a valid, expected entry. Do not invent dependencies to
fill this section; every added library is surface area.>

- <library==version> — <why it's needed>

## Goal of this feature

<One or two sentences: what this feature adds and what it deliberately does not do.>

## Design

### <file> (location)

<Key surface / signatures for the new code, what it exposes.>

- <Design decision, with the WHY>
- <How it connects to what earlier plans built>
- <Validation / error behavior>

### <test file>

<Cases for the new behavior:>

- <case>
- <edge / error case>

## Files

- <file> — new or modified, <what changes>.
- <test file> — new, the cases above.

## Out of scope (parked)

### Planned — intended for this version

- <feature> — later plan (00N)

### Possible — noted, not committed

- <idea that may never be built>

## Follow-ups after implementation (not code changes in this slice)

- <Any CLAUDE.md harvest this feature triggers — new command, new rule, new
  protected file. Propose the exact edit for approval; CLAUDE.md is protected.>

## Verification

### Outcome — what this feature now does

<One or two plain-language sentences: the new user-visible or behavioral change
this slice adds, stated so a non-coder could confirm it. E.g. "Quotes now never
repeat twice in a row." State what's DIFFERENT from before this slice.>

### Steps — confirm it by hand

Step-by-step (copy-pasteable, in order). Each step lists the command AND its
expected output.

1. <setup command, if any new deps> — expected: <installs, no errors>
2. <full test command — runs THIS slice's tests + all earlier slices> — expected: <e.g. "all pass">
3. <smoke check for the new behavior> — expected: <printed value, OR for an interface slice: launch command + expected VISIBLE result>

ONLY list commands that actually work after THIS slice. If this feature is the
one that first makes the app runnable (the interface/entry-point slice), THIS is
where the launch command (e.g. npm run dev) belongs — and its expected result is
the visible app, not a printed value. If the app still isn't runnable after this
slice, do not list a launch command.
