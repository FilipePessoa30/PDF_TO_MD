#!/usr/bin/env python3
"""Clone or update the raw ENADE source corpus into data/raw/ (gitignored).

This is the *only* sanctioned way to populate data/raw/geacc-enade: it never
writes into the upstream repository, only reads from it (clone/fetch), and
always prints the exact commit SHA that ends up on disk so it can be pasted
into a provenance record.

Usage:
    python scripts/fetch_corpus.py
    python scripts/fetch_corpus.py --ref master --dest data/raw/geacc-enade
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_REPOSITORY_URL = "https://github.com/geacc/enade.git"
DEFAULT_REF = "master"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEST = PROJECT_ROOT / "data" / "raw" / "geacc-enade"


def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)  # type: ignore[arg-type]


def fetch_corpus(repository_url: str, ref: str, dest: Path) -> str:
    if dest.exists():
        if not (dest / ".git").is_dir():
            raise SystemExit(f"refusing to reuse {dest}: it exists but is not a git repository")
        print(f"Updating existing clone at {dest} ...")
        run(["git", "fetch", "origin", ref], cwd=str(dest))
        run(["git", "checkout", ref], cwd=str(dest))
        run(["git", "reset", "--hard", f"origin/{ref}"], cwd=str(dest))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"Cloning {repository_url} ({ref}) into {dest} ...")
        run(["git", "clone", "--branch", ref, repository_url, str(dest)])

    result = run(["git", "rev-parse", "HEAD"], cwd=str(dest))
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_REPOSITORY_URL, help="source repository URL")
    parser.add_argument("--ref", default=DEFAULT_REF, help="branch or tag to fetch")
    parser.add_argument(
        "--dest", type=Path, default=DEFAULT_DEST, help="local destination directory"
    )
    args = parser.parse_args()

    try:
        commit_sha = fetch_corpus(args.url, args.ref, args.dest)
    except subprocess.CalledProcessError as exc:
        print("git command failed:", " ".join(exc.cmd), file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        return 1

    print(f"OK: {args.dest} is at commit {commit_sha} (ref={args.ref!r}, url={args.url!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
