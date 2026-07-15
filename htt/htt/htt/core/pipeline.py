"""Quarantined legacy integrated pipeline entry point.

This v7-era pipeline bound channel ``c`` into evidence, tables, and figures.
It cannot run as an active PR-120 producer while the upstream findings remain
OPEN.  The production workspace pipeline is separate; historical reproduction
is confined to the frozen legacy lane.
"""
from __future__ import annotations

from htt.core.cf4_observational_input import require_cf4_observational_input


def main() -> None:
    require_cf4_observational_input(consumer="htt.core.pipeline legacy bundle")


if __name__ == "__main__":
    main()
