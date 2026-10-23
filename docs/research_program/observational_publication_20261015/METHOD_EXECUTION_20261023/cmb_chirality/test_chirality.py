"""Targeted exact controls for the saved-carrier chirality candidate."""
import json

import chirality as c


def test_frozen_sources_and_fixture():
    assert c.source_check()["task_id"] == "R24-CMB-CHIRALITY"
    assert c.exact_controls() == "PASS"


def test_zero_strata_and_strict_boundary():
    z2 = c.tensor2((0, 0, 0, 0, 0))
    z3 = c.tensor3((0, 0, 0, 0, 0, 0, 0))
    assert c.chi(z2, z3) == c.metric(z2, z3) == 0
    sample = {"harmonic12_K_CMB": [0]*12, "STF2_components_K_CMB": [0]*5,
              "STF3_components_K_CMB": [0]*7}
    row = c.bundle_result(sample)
    assert row["zero_strata"] == ["CHI_ZERO_INCONCLUSIVE", "M_ZERO_NORMALIZED_UNDEFINED"]
    assert row["chi_over_m9_decimal80"] is None
    assert all(p["status"] == "INCONCLUSIVE" for p in row["perturbation_scenarios"])


def test_all_saved_carriers_and_mirror_bound():
    output = json.loads((c.HERE/"RESULT.json").read_text())
    rows = output["bundles"]
    assert len(rows) == 60 and len(output["comparisons"]) == 93
    assert len({c.key(z["carrier"]) for z in rows}) == 60
    for z in rows:
        b = z["carrier"]
        q, o = c.tensor2(b["STF2_components_K_CMB"]), c.tensor3(b["STF3_components_K_CMB"])
        x, m2 = c.chi(q,o), c.metric(q,o)
        assert c.ratio(x) == z["chi_exact"]
        assert c.ratio(abs(x)/(3*m2**4)) == z["mirror_SO3_distance_lower_exact"]
        assert x != 0 and m2 > 0 and z["perturbation_scenarios"][0]["status"] == "CERTIFIED_SIGN_PRESERVED"
        assert max(float(e) for e in z["decimal90_130_relative_errors"]) < 1e-60
        assert z["registered_decoder_completion_scaled_difference"] <= 1e-12
