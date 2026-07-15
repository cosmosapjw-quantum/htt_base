"""Quarantined historical CF4-conditioned H0 sensitivity analysis.

The former module executed observational calculations at import time.  PR-120
removes that active route; historical bytes remain available through Git and
the frozen ``legacy/cf4_p0`` evidence lane.
"""
from __future__ import annotations

from htt.core.cf4_observational_input import require_cf4_observational_input


def run_h0_sensitivity(*args, **kwargs):
    """Fail closed; there is no active CF4-conditioned sensitivity result."""

    require_cf4_observational_input(consumer="htt.core.h0_sensitivity")


if __name__ == "__main__":
    run_h0_sensitivity()
