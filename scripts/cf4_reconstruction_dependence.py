#!/usr/bin/env python3
"""Active PR-120 wrapper for the reconstruction-conditioned method record."""
from cf4_p0_conditioned_diagnostics import RECONSTRUCTION_SPEC, conditioned_main


if __name__ == "__main__":
    raise SystemExit(conditioned_main(RECONSTRUCTION_SPEC))
