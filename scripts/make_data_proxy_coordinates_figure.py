#!/usr/bin/env python3
"""Active observed-sector proxy figure path: PR-120 blocked sidecars only."""
try:
    from scripts.cf4_p0_quarantine_derived import DATA_PROXY_SPEC, figure_block_main
except ModuleNotFoundError as exc:  # Direct ``python scripts/...`` execution.
    if exc.name not in {"scripts", "scripts.cf4_p0_quarantine_derived"}:
        raise
    from cf4_p0_quarantine_derived import DATA_PROXY_SPEC, figure_block_main


def main(argv=None) -> int:
    return figure_block_main(DATA_PROXY_SPEC, argv)


if __name__ == "__main__":
    raise SystemExit(main())
