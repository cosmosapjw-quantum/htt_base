#!/usr/bin/env python3
"""Retired mixed figure driver; exact source is frozen below legacy/cf4_p0.

The historical aggregate mixed independent and CF4/channel-c figures in one
process, so it cannot be partially regenerated without reviving blocked
consumers. Use the dedicated current manifest-backed generators instead.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "htt" / "htt"))

from htt.core.cf4_observational_input import require_cf4_observational_input  # noqa: E402


def main() -> None:
    require_cf4_observational_input(consumer="scripts/make_paper_figures.py")


if __name__ == "__main__":
    main()
