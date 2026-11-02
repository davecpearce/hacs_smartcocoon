#!/usr/bin/env python3
"""Fail when a tool pinned in two places disagrees with itself.

`pylint`, `ruff` and `mypy` are pinned both in `requirements_test.txt` and
as a `rev` in `.pre-commit-config.yaml`. **pre-commit is what gates CI**, so
when the two drift the linter judging a pull request is not the one anyone
runs before opening it.

Dependabot can only ever see the `requirements_test.txt` half, and these
updates auto-merge unattended, so it walks into this on its own and nothing
reports it. It has happened four times (ruff, pylint twice, mypy). Each
time it was found by hand, long afterwards.

Rather than hold a list of known pairs -- which would miss the next tool to
become dual-pinned -- this derives a package name from each hook repo URL
and checks whether `requirements_test.txt` also pins it. Anything pinned in
only one place is not this script's business and is ignored.

Run locally with:

    python scripts/check_tool_pins.py
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"
REQUIREMENTS = REPO_ROOT / "requirements_test.txt"

#: Hook repos whose name differs from the package they install.
#: Derivation handles the common `mirrors-x` / `x-pre-commit` spellings, so
#: this is only for genuine exceptions.
NAME_OVERRIDES: dict[str, str] = {
    "pre-commit-hooks": "",  # a hook bundle, not a pinned package
    "prettier": "",  # npm, never in requirements_test.txt
}

_REQ_PIN = re.compile(r"^([A-Za-z0-9._-]+)==([A-Za-z0-9._-]+)\s*$")


def package_for(repo_url: str) -> str:
    """Return the PyPI package a hook repo installs, or "" if not one."""
    slug = repo_url.rstrip("/").rsplit("/", 1)[-1].lower()
    # github.com/pre-commit/mirrors-mypy  -> mypy
    # github.com/astral-sh/ruff-pre-commit -> ruff
    slug = re.sub(r"^mirrors-", "", slug)
    slug = re.sub(r"-pre-commit$", "", slug)
    return NAME_OVERRIDES.get(slug, slug)


def precommit_pins() -> dict[str, str]:
    """Return {package: version} for every revisioned hook repo."""
    config = yaml.safe_load(PRE_COMMIT.read_text())
    pins: dict[str, str] = {}
    for repo in config.get("repos", []):
        url, rev = repo.get("repo"), repo.get("rev")
        # `repo: local` hooks carry no rev and pin nothing.
        if not url or url == "local" or not rev:
            continue
        package = package_for(str(url))
        if package:
            pins[package] = str(rev).lstrip("vV")
    return pins


def requirement_pins() -> dict[str, str]:
    """Return {package: version} for every `==` pin in requirements_test."""
    pins: dict[str, str] = {}
    for line in REQUIREMENTS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-r", "-c")):
            continue
        match = _REQ_PIN.match(line)
        if match:
            pins[match.group(1).lower()] = match.group(2)
    return pins


def main() -> int:
    """Compare the two sources and explain the fix on any mismatch."""
    for path in (PRE_COMMIT, REQUIREMENTS):
        if not path.is_file():
            print(f"::error::{path} not found")
            return 1

    hooks = precommit_pins()
    reqs = requirement_pins()

    shared = sorted(set(hooks) & set(reqs))
    if not shared:
        print(
            "No tool is pinned in both .pre-commit-config.yaml and "
            "requirements_test.txt. Nothing to compare."
        )
        return 0

    mismatched = [p for p in shared if hooks[p] != reqs[p]]

    for package in shared:
        mark = "MISMATCH" if package in mismatched else "ok"
        print(
            f"  {mark:9} {package:<12} "
            f"pre-commit={hooks[package]:<10} "
            f"requirements={reqs[package]}"
        )

    if not mismatched:
        print()
        print(f"All {len(shared)} dual-pinned tool(s) agree.")
        return 0

    print()
    for package in mismatched:
        print(
            f"::error::{package} is pinned at {hooks[package]} in "
            f".pre-commit-config.yaml but {reqs[package]} in "
            f"requirements_test.txt."
        )
    print()
    print("  pre-commit is what gates CI, so while these disagree the")
    print("  linter enforced on a pull request is not the one you run")
    print("  locally. Set both to the same version, in one commit:")
    print()
    for package in mismatched:
        print(f"    .pre-commit-config.yaml  rev: v{reqs[package]}")
        print(f"    requirements_test.txt    {package}=={reqs[package]}")
    print()
    print(
        "  Dependabot only sees requirements_test.txt, so its pull "
        "requests need the rev edited by hand before merging."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
