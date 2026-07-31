---
name: repo-pr-release-readiness
description: Check whether an open PR on python-seedwork is ready for review/merge — correct Conventional Commits title prefix, linked issue, CI status, coverage. Use before requesting review on a PR in this repo, or when asked "is this PR ready" / "will this release correctly".
---

# repo-pr-release-readiness

This repo only squash-merges (`squash_merge_commit_title: PR_TITLE`, `squash_merge_commit_message: BLANK`), so the **PR title** is the only text `python-semantic-release` ever sees. A wrong prefix silently produces the wrong version bump (or no release at all) on merge — verify these before handing a PR to a human reviewer.

## Checks

1. **Title prefix** — `gh pr view <n> --json title`. Must start with one of `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert` (enforced by `.github/workflows/pr-title-lint.yml` and `.pre-commit-config.yaml`'s `conventional-pre-commit` hook). Confirm the prefix matches whether the change should actually trigger a release:
   - `feat`/`fix`/`perf` → bumps the version. Only use these if the change is user-visible in the published package.
   - `docs`/`chore`/`ci`/`build`/`refactor`/`style`/`test`/`revert` → no release. Use for repo-maintenance-only changes (like this one).
   - A breaking change needs a `BREAKING CHANGE:` footer, not just `feat!:` in the title (check the footer is actually present in the PR body if breaking).
2. **Linked issue** — `gh pr view <n> --json body` should contain a `Closes #N` / `Relates to #N` line, not just a prose mention.
3. **Labels** — `gh pr view <n> --json labels` vs `gh label list`; the PR should carry labels matching its content.
4. **CI status** — `gh pr checks <n>`. All required checks green.
5. **Coverage** — if the change touches `src/seedwork/`, confirm the `test` job passed (implies the 90% gate held); don't just check lint/typecheck.
6. **Description structure** — body has What/Why/How/How to test sections, in English, and doesn't narrate the conversation/investigation that produced the change.

Report each check as pass/fail with the specific gh output backing it — don't just say "looks fine".
