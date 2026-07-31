---
name: boy-scout
description: Use this skill while analyzing any request or change in python-seedwork, to check whether nearby code could be improved, and whenever the user explicitly asks for a cleanup/refactor pass. Encodes the rule that improvements are either executed inline (if small and contract-safe) or split into a separate issue — never bundled into the requested change — and that refactors must never trigger a release.
metadata:
  version: "1.0.0"
---

# Boy-scout rule for python-seedwork

Leave the code better than you found it, but never at the cost of mixing an unrelated
improvement into the change the requester actually asked for.

## When to apply

- While analyzing any user request (per `CLAUDE.md` — "Workflow"), before implementing:
  look at the code you're about to touch (and its immediate neighbors) for refactoring
  opportunities unrelated to the request itself.
- When the user explicitly asks for a cleanup/refactor pass.

## What counts as a refactoring opportunity

Dead code, duplicated logic, naming drift, mutation of frozen dataclasses, unjustified
`Any`, missing `_co`/`_contra` TypeVar suffixes, or other violations of `CLAUDE.md`'s "Key
design decisions" / "Type-checking constraints" that don't require a bug fix or new
capability — pure cleanup, no behaviour change.

## Decision

- **Small, self-contained, no public API change** → execute directly (spawn the
  `boy-scout` agent, or do it yourself if already in the relevant file) as a `refactor:`
  commit. Confirm it does not trigger a release (see the commit-type table in
  `.claude/skills/gh-workflow/SKILL.md`).
- **Larger, cross-cutting, or touches exported public API** → do not touch it now. Open a
  separate GitHub issue describing the opportunity (requester's own identity, per
  `.claude/skills/gh-workflow/SKILL.md` — "Identity"). Mention it to the requester, then
  continue with the original request unmodified.

Never let a refactor change observable behaviour or a public signature — if it would, it
isn't a refactor; it's a `fix:`/`feat:` change and needs its own issue.
