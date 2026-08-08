"""Read reproducibility metadata (url/ref/commit) from a local git clone."""

from __future__ import annotations

import subprocess
from pathlib import Path

from enade.models.provenance import SourceRepository


class GitMetadataError(RuntimeError):
    """Raised when ``corpus_root`` is not a usable git clone."""


def _git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), check=True, text=True, capture_output=True
        )
    except FileNotFoundError as exc:
        raise GitMetadataError("git executable not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise GitMetadataError(f"git {' '.join(args)} failed: {exc.stderr.strip()}") from exc
    return result.stdout.strip()


def read_source_repository(corpus_root: Path) -> SourceRepository:
    """Inspect a local clone at ``corpus_root`` and return its provenance."""
    if not (corpus_root / ".git").exists():
        raise GitMetadataError(f"{corpus_root} is not a git repository (no .git found)")

    url = _git(["remote", "get-url", "origin"], corpus_root)
    commit_sha = _git(["rev-parse", "HEAD"], corpus_root)
    ref = _git(["rev-parse", "--abbrev-ref", "HEAD"], corpus_root)
    if ref == "HEAD":
        # Detached HEAD: fall back to a symbolic description, else the raw commit.
        try:
            ref = _git(["describe", "--tags", "--always"], corpus_root)
        except GitMetadataError:
            ref = commit_sha

    return SourceRepository(repository_url=url, ref=ref, commit_sha=commit_sha)
