#!/usr/bin/env python3
"""Active PR-120 wrapper for the treatment-conditioned pair statistic."""
from cf4_p0_conditioned_diagnostics import PAIR_SPEC, conditioned_main


if __name__ == "__main__":
    raise SystemExit(conditioned_main(PAIR_SPEC))
