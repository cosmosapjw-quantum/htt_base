#!/usr/bin/env python3
"""Active PR08 joint artifact path: PR-120 block record only."""
try:
    from scripts.cf4_p0_quarantine_derived import SINGLE_CARD_SPECS, single_card_main
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` execution.
    if exc.name not in {"scripts", "scripts.cf4_p0_quarantine_derived"}:
        raise
    from cf4_p0_quarantine_derived import SINGLE_CARD_SPECS, single_card_main


def main(argv=None) -> int:
    return single_card_main(SINGLE_CARD_SPECS["joint"], argv)


if __name__ == "__main__":
    raise SystemExit(main())
