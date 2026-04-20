"""VER2 claim-ledger helpers.

This module mirrors ``common.status_snapshot``: the canonical schema lives in
``common.contracts.ClaimLedgerEntry`` and this file provides a stable import
surface for later generator/export tooling without duplicating the contract.
"""
from __future__ import annotations

from dataclasses import asdict

from common.contracts import ClaimLedgerEntry


def claim_entry_to_dict(entry: ClaimLedgerEntry) -> dict[str, object]:
    """Return a JSON-ready dictionary for one claim-ledger row."""
    return asdict(entry)
