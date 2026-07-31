---
name: bug-triage
description: Use this skill when the user reports unexpected behavior or a suspected defect in python-seedwork, before writing any fix. Encodes the analyze-propose-confirm-then-issue flow so a bug report turns into a well-formed GitHub issue instead of an immediate, unreviewed code change.
metadata:
  version: "1.0.0"
---

# Bug triage for python-seedwork

A bug report is not an implicit go-ahead to change code. Analyze first, propose a
solution, get it confirmed, only then create the issue (and only after that, implement,
following the normal `CLAUDE.md` workflow: issue → plan → parallel implementation → PR).

## Flow

1. **Analyze** — spawn the `bug-analyst` agent (or do the analysis inline if trivial):
   confirm the reported behavior is actually a defect, find the root cause with
   `file:line` precision, and propose a solution including whether it would be a breaking
   change.
2. **Confirm with the requester** — present the analysis and proposed solution; do not
   proceed until they confirm it's correct and worth fixing.
3. **Create the issue** — under the requester's own `gh` identity (no `GH_TOKEN`; see
   `.claude/skills/gh-workflow/SKILL.md` — "Identity"), with clear acceptance criteria
   derived from the confirmed analysis. Label `bug`.
4. **Hand off to implementation** — from here on, follow the normal workflow in
   `CLAUDE.md` (plan → parallel code/test/docs implementation → PR referencing the issue).

Never skip step 2: an unconfirmed analysis becoming an issue (or worse, a PR) risks
"fixing" something that was actually intended behavior or a misunderstanding.
