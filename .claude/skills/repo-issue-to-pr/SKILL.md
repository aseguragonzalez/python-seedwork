---
name: repo-issue-to-pr
description: Run this repo's maintenance workflow end to end — analyze a problem, open a GitHub issue with the right template and labels, branch, implement, and open a PR linked to the issue. Use whenever asked to fix, add, or change something in this repository (not for questions about how the library works).
---

# repo-issue-to-pr

Maintenance workflow for `python-seedwork`, matching the policy in `CLAUDE.md`'s "Maintenance workflow" section.

## Steps

1. **Analyze** — read the relevant code/docs before writing anything. Confirm the scope: what's broken or missing, and what "done" looks like.
2. **Open an issue** using the user's personal `gh` session (do **not** export `GH_TOKEN` to the bot token — the bot App installation only has Pull requests permission, not Issues):
   - Pick the matching template under `.github/ISSUE_TEMPLATE/` (bug report, feature request, question).
   - Apply labels from the existing set (`gh label list`) — don't invent new ones.
   - Write the issue body in English.
3. **Branch from `main`** with a descriptive name (e.g. `fix/...`, `feat/...`, `docs/...`, `chore/...`).
4. **Implement**, staying scoped to the issue. Verify with `make check` (inside the devcontainer) before committing.
5. **Commit and push using the bot identity** (`myclaudecodeagent[bot]`), per the global git/GitHub conventions — mint a token via `gh-app-token.mjs`, commit with the bot's `user.name`/`user.email`, push, then reverify via `gh-app-reverify-commit.mjs` so the commit shows as Verified.
6. **Open a PR against `main`** that links the issue (`Closes #N`), with the What/Why/How/How to test structure, in English, using a Conventional Commits title prefix chosen for whether it should trigger a release (see `CLAUDE.md`'s PR title / release policy — this repo only squash-merges, so the PR title is the commit message on `main`).
7. Apply matching labels to the PR (same label set as issues).
8. Do not merge — a human approves and merges once CI is green. The bot identity exists specifically so the user's own GitHub account can leave that approval.
