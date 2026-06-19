import pytest

from bass.transfer.evidence_stability import evidence_shift_bound


def test_evidence_shift_bound_is_transfer_conditional_certificate():
    bound = evidence_shift_bound(0.25)

    assert bound["owner"] == "BASS"
    assert bound["implementation_scope"] == "bass_py"
    assert bound["claim_tier"] == "diagnostic_only"
    assert bound["transfer_conditional"] is True
    assert bound["native_solver_result"] is False
    assert bound["evidence_shift_upper_bound"] == pytest.approx(0.25)
    assert "|Delta log Z| <= sup |Delta log L|" in bound["definition"]
    assert "not native solver validation" in bound["caveats"]


def test_evidence_shift_bound_rejects_negative_or_nonfinite_values():
    with pytest.raises(ValueError, match="non-negative finite"):
        evidence_shift_bound(-0.1)
    with pytest.raises(ValueError, match="non-negative finite"):
        evidence_shift_bound(float("inf"))
