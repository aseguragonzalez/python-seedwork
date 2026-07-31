---
name: gh-workflow
description: Use this skill whenever working on python-seedwork and about to open a GitHub issue or pull request, decide a commit message/PR title, or plan how to implement an issue. Encodes this repo's issue-first workflow, identity rules, label taxonomy, and the commit/PR conventions that keep semantic-release from shipping an unintended version bump.
metadata:
  version: "1.0.0"
---

# python-seedwork GitHub workflow

This repo requires every change to start from an issue and follows strict Conventional
Commit rules because `python-semantic-release` reads the **PR title** literally (this repo
only squash-merges) to decide whether — and what kind of — a release ships. See
`CLAUDE.md` for the policy statement this skill implements.

## Flow

1. **Analyze and open the issue.** Understand the request, confirm the understanding with
   the requester, then create (or confirm) an issue with clear, testable acceptance
   criteria. Skip creation only if an issue for this exact change already exists.
2. **Plan.** Re-read the issue and draft an implementation plan that separates code,
   tests, and documentation as independent tracks against contracts (Protocols/signatures)
   agreed up front.
3. **Implement in parallel** using the code/test/docs agents under `.claude/agents/`
   (`python-implementer`, `python-test-writer`, `docs-aligner`) against those contracts.
4. **Open a PR that references the issue** — use a closing keyword (`Closes #N`) in the
   PR body, never just a prose mention.

Never open a PR without a linked issue. While analyzing any request, also check whether
nearby code could be improved — if so, open a **separate** issue for it (see the
`boy-scout` skill) rather than folding it into this change.

## Identity

- **Issues** are created under the requester's own `gh` session (the default — do **not**
  export `GH_TOKEN`). Issues represent the requester's decisions/requests. The bot App
  installation on this repo only has Pull requests permission, not Issues — bot-token
  issue calls fail with `403`.
- **Commits and PRs** use the bot App identity (`myclaudecodeagent[bot]`) — see the global
  `~/.claude/CLAUDE.md` instructions for minting `GH_TOKEN` and commit authorship, plus the
  reverify-commit step for the Verified badge. This is what lets the requester leave a
  genuine "Approve" review, since GitHub blocks a PR author from approving their own PR.
- Mint the token and run the `gh`/`git push` command that needs it **in the same Bash
  call** — `GH_TOKEN` does not persist across separate tool invocations, and a dropped
  token silently falls back to the requester's personal session for that one call.
- Never mix the two: don't create an issue with the bot token, and don't commit/push with
  the requester's personal session when the bot identity is available.

## Reviewers

Every PR should get an explicit review request to the repo owner (`@aseguragonzalez`,
per `.github/CODEOWNERS`) — `gh pr create --reviewer aseguragonzalez` or
`gh pr edit <n> --add-reviewer aseguragonzalez` — even though CODEOWNERS may also trigger
an automatic request; make it explicit rather than relying on that silently.

## Labels

Use the repo's existing label set (`gh label list`) — don't invent new ones:

`bug`, `enhancement`, `documentation`, `question`, `good first issue`, `help wanted`,
`invalid`, `duplicate`, `wontfix`, `dependencies`, `python:uv`, `github_actions`.

## Commit type → release impact

The commit type is read by `python-semantic-release`'s default Angular preset (no custom
`releaseRules` in `pyproject.toml`). Pick it by **which layer actually changed**, not by
habit — and remember only the **PR title** matters here, since the repo squash-merges:

| Change scope | Type | Triggers release? |
|---|---|---|
| `src/seedwork/` behaviour (bug fix) | `fix:` | patch |
| `src/seedwork/` behaviour (new capability) | `feat:` | minor |
| `src/seedwork/` breaking change (renamed public class, required param added, return type changed, etc.) | `fix!:` / `feat!:` + `BREAKING CHANGE:` footer | major |
| `docs/`, `docs/examples/`, README, `CLAUDE.md` only | `docs:` | none |
| `.github/workflows/`, CI/pipeline files | `ci:` | none |
| `Makefile`, `pyproject.toml` build config, `.claude/` tooling | `chore:` / `build:` | none |
| Refactor with no behaviour change | `refactor:` | none |
| Test-only changes | `test:` | none |

A mismatched type either ships a spurious release or silently swallows one that should
have shipped — both are defects. This applies even when the underlying commit type is
technically valid Conventional Commits; e.g. `.claude/skills/` changes are `chore:`/`docs:`,
never `feat:`, because nothing shipped to PyPI changed.

## Issue and PR content

- Body: exactly **What / Why / How** + **How to test**, in English.
- **No conversation narrative or reasoning trail** — state the outcome directly.
- Always link the issue via a closing keyword.
- Apply matching labels from the taxonomy above.
- Request review from the repo owner explicitly (see Reviewers above).

## PR release-readiness check

Before requesting review, verify:

1. `gh pr view <n> --json title` — prefix matches the change per the table above.
2. `gh pr view <n> --json body` — contains `Closes #N` and the What/Why/How/How to test
   sections.
3. `gh pr view <n> --json labels` vs `gh label list` — labels applied.
4. `gh pr checks <n>` — all required checks green.
5. If the change touches `src/seedwork/`, confirm the `test` job passed (implies the 90%
   coverage gate held), not just lint/typecheck.

## Replying to PR review comments

Answer review comments — from a human or a bot reviewer — in English, as a **reply in the
same review-comment thread**, never as a new top-level PR comment:

```bash
gh api repos/aseguragonzalez/python-seedwork/pulls/<pr-number>/comments \
  -f body="<answer in English>" \
  -F in_reply_to=<review_comment_id>
```

Get `<review_comment_id>` from `gh api repos/aseguragonzalez/python-seedwork/pulls/<pr-number>/comments`
(the `id` field of the comment being answered).
