#!/usr/bin/env python3
"""Active v9 K5/CF4 card path: PR-120 block record only."""
try:
    from scripts.cf4_p0_quarantine_derived import IDENTIFIED_INTERVAL_SPECS, derived_main
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` execution.
    if exc.name not in {"scripts", "scripts.cf4_p0_quarantine_derived"}:
        raise
    from cf4_p0_quarantine_derived import IDENTIFIED_INTERVAL_SPECS, derived_main


def main(argv=None) -> int:
    return derived_main(IDENTIFIED_INTERVAL_SPECS["v9"], argv)


if __name__ == "__main__":
    raise SystemExit(main())
