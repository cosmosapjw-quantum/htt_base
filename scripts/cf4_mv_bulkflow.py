#!/usr/bin/env python3
"""Active CF4 MV producer: PR-120 quarantine block only."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.cf4_p0_quarantine_producer import PRODUCERS, block_payload, producer_main


def measure() -> dict:
    return block_payload(PRODUCERS["mv"])


def main(argv=None) -> int:
    return producer_main(PRODUCERS["mv"], argv)


if __name__ == "__main__":
    raise SystemExit(main())
