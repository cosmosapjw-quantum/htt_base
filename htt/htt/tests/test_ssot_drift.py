"""Anti-regression guard for SSOT T_CMB drift (SSOT-01).

Freezes `htt.core.ssot.C.T0_K` at the Fixsen (2009) central value. Any silent
future change to the htt-side SSOT constant will fail this test. See
`docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` for the audit trail.
"""
from htt.core.ssot import C


def test_tcmb_ssot_frozen_fixsen2009():
    """C.T0_K must equal the Fixsen 2009 central value (2.72548 K) byte-exact."""
    assert C.T0_K == 2.72548


def test_tcmb_ssot_units_are_internally_consistent():
    """C.T0_uK must be the exact μK conversion of the frozen Fixsen 2009 value."""
    assert C.T0_uK == C.T0_K * 1e6
