"""Anti-regression guard for SSOT T_CMB drift (SSOT-01).

Freezes `htt.core.ssot.C.T0_K` at the Fixsen (2009) central value. Any silent
future change to the htt-side SSOT constant will fail this test. See
`docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` for the audit trail.
"""
from htt.core.ssot import C


def test_tcmb_ssot_frozen_fixsen2009():
    """C.T0_K must equal the Fixsen 2009 central value (2.72548 K) byte-exact."""
    assert C.T0_K == 2.72548


def test_tcmb_ssot_drift_documented():
    """C.T0_uK is known to be inconsistent with C.T0_K (2.7255e6 vs 2.72548e6).

    This test DOCUMENTS the known drift rather than enforcing it — it will
    start FAILING when the inconsistency is fixed, which is the signal to
    delete this test and replace it with `assert C.T0_uK == C.T0_K * 1e6`.
    See SSOT_TCMB_DRIFT_2026-04-19.md §4 item 2.
    """
    assert C.T0_uK == 2.7255e6, (
        "If this fails, the intra-SSOT T0_K/T0_uK inconsistency has been "
        "fixed. Replace with `assert C.T0_uK == C.T0_K * 1e6` and delete "
        "this note."
    )
