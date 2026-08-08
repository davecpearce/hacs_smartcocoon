#!/usr/bin/env python3
"""Fail if hacs.json advertises a Home Assistant version we do not test.

`pytest-homeassistant-custom-component` pins `homeassistant` to an exact
version, so whatever it installs is the only version this integration is ever
run against. `hacs.json` is what HACS enforces when deciding whether a user
may install or update.

When those two disagree, the integration advertises support for releases
nothing has verified. That is how the declared minimum reached 2025.5.0 while
CI ran 2026.2.3 -- fifteen months of unverified claims, noticed only by
accident.

Run locally with:

    python scripts/check_declared_ha_version.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HACS_JSON = REPO_ROOT / "hacs.json"


def declared_version() -> str | None:
    """Return the minimum Home Assistant version hacs.json advertises."""
    try:
        return str(json.loads(HACS_JSON.read_text())["homeassistant"])
    except FileNotFoundError:
        print(f"::error::{HACS_JSON} not found")
    except (KeyError, json.JSONDecodeError) as exc:
        print(f"::error::Could not read 'homeassistant' from hacs.json: {exc}")
    return None


def installed_version() -> str | None:
    """Return the Home Assistant version actually installed for the tests."""
    try:
        # Imported here, not at module scope: the point of this branch is to
        # report a missing homeassistant cleanly rather than fail on import.
        # pylint: disable-next=import-outside-toplevel
        from homeassistant.const import __version__

        return str(__version__)
    except ImportError:
        print(
            "::error::homeassistant is not installed, so the tested version "
            "cannot be determined. Install requirements_test.txt first."
        )
    return None


def main() -> int:
    """Compare the two and explain the fix if they differ."""
    declared = declared_version()
    installed = installed_version()

    if declared is None or installed is None:
        return 1

    if declared == installed:
        print(
            f"hacs.json declares Home Assistant {declared}, which is the "
            f"version the tests run against."
        )
        return 0

    print(
        f"::error::hacs.json declares a minimum of Home Assistant "
        f"{declared}, but the tests run against {installed}."
    )
    print()
    print(
        "  These have to match. hacs.json is what HACS enforces when a user "
        "installs or updates, so a value nothing tests is a claim this "
        "project cannot back."
    )
    print()
    print("  The tested version comes from the")
    print("  pytest-homeassistant-custom-component pin in")
    print("  requirements_test.txt, so this usually means that pin moved.")
    print()
    print("  To fix, set both to the tested version:")
    print(f'    hacs.json            -> "homeassistant": "{installed}"')
    print(f"    requirements_test.txt -> homeassistant>={installed}")
    print()
    print(
        "  Raising the minimum stops HACS offering updates to anyone on an "
        "older release, so it is a deliberate narrowing of support, not "
        "bookkeeping."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
