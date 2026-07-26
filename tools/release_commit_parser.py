"""Custom python-semantic-release commit parser.

Mirrors the convention already used across this org's other *-seedwork
repositories (see e.g. ts-seedwork's .releaserc.json releaseRules): automated
dependency bump commits scoped to `deps`/`deps-dev` must never trigger a
release on their own, even when tagged `fix`/`perf`, since they carry no
functional change to the library itself. Everything else falls back to the
stock Conventional Commits behavior.

Referenced from pyproject.toml as a file path so it does not need to be
installed as part of the `seedwork` package:

    [tool.semantic_release]
    commit_parser = "tools/release_commit_parser.py:DepsScopedCommitParser"
"""

from __future__ import annotations

from re import Match

from semantic_release.commit_parser.conventional import ConventionalCommitParser
from semantic_release.commit_parser.token import ParsedMessageResult
from semantic_release.enums import LevelBump

_MUTED_TYPES = ("fix", "perf")
_MUTED_SCOPES = ("deps", "deps-dev")


class DepsScopedCommitParser(ConventionalCommitParser):
    def create_parsed_message_result(self, match: Match[str]) -> ParsedMessageResult:
        result = super().create_parsed_message_result(match)
        if (
            result.bump is not LevelBump.MAJOR
            and result.type in _MUTED_TYPES
            and result.scope in _MUTED_SCOPES
        ):
            return result._replace(bump=LevelBump.NO_RELEASE)
        return result
