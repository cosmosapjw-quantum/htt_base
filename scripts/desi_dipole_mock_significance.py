#!/usr/bin/env python3
"""Quarantined pre-formalism PR-151 mock producer.

This module exposes only a deterministic invalidation receipt.  It imports no
survey, numerical, or science library and cannot recreate a historical card.
"""
from __future__ import annotations

import argparse
import json
from typing import Sequence


INVALIDATION_STATUS = "INVALIDATED_PENDING_FORMALISM_REVALIDATION"


class InvalidatedHistoricalProducerError(RuntimeError):
    """The retired PR-151 producer is not an active analysis API."""


def invalidation_receipt() -> dict[str, object]:
    return {
        "schema": "htt.pr151_historical_producer_invalidation.v1",
        "producer": "desi_dipole_mock_significance",
        "execution_state": INVALIDATION_STATUS,
        "observed_data_executed": False,
        "scientific_result_emitted": False,
    }


def measure() -> dict[str, object]:
    raise InvalidatedHistoricalProducerError(
        "PR-151 historical producer is invalidated; a separately specified and validated successor formalism is required"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(invalidation_receipt(), sort_keys=True))
    return 7


if __name__ == "__main__":
    raise SystemExit(main())
