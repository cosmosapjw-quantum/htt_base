"""Focused falsifiers for the frozen conditional common-mode envelope."""

import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location("cmb_envelope", Path(__file__).with_name("envelope.py"))
envelope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(envelope)


def test_zero_radius_and_monotone_widening():
    result = envelope.compute()
    assert len(result["comparisons"]) == 57
    for row in result["comparisons"]:
        scenarios = row["scenarios"]
        assert abs(scenarios[0]["certified_outer_lower"] - row["base_lower"]) < 1e-12
        assert abs(scenarios[0]["feasible_outer_upper"] - row["base_feasible_upper"]) < 1e-12
        for before, after in zip(scenarios, scenarios[1:]):
            assert after["certified_outer_lower"] <= before["certified_outer_lower"] + 1e-12
            assert after["feasible_outer_upper"] + 1e-12 >= before["feasible_outer_upper"]
    for row in result["processing_support"]:
        base = np.array(row["base_support"])
        assert np.max(np.abs(np.array(row["scenarios"][0]["support_lower"]) - base)) < 1e-12
        assert np.max(np.abs(np.array(row["scenarios"][0]["support_upper"]) - base)) < 1e-12
        for before, after in zip(row["scenarios"], row["scenarios"][1:]):
            assert np.max(np.array(after["support_lower"]) - np.array(before["support_lower"])) <= 1e-12
            assert np.max(np.array(before["support_upper"]) - np.array(after["support_upper"])) <= 1e-12


def test_shared_common_mode_and_split_difference_kernel():
    g = np.arange(12, dtype=float) / 7
    f = np.arange(12, dtype=float) / 19
    fs = np.stack([g / 11, -g / 13])
    n = np.stack([g / 17, g / 23])
    baseline = envelope.split_model(g, f, fs, n)
    direction = np.zeros(12); direction[7] = 1
    for t in (0, 0.05, 1000, 1e8):
        transformed = envelope.split_model(g + t * direction, f - t * direction, fs, n)
        assert np.allclose(transformed, baseline, rtol=0, atol=1e-8)
        assert np.allclose(transformed[0] - transformed[1], baseline[0] - baseline[1], rtol=0, atol=1e-8)


def test_stf_norm_and_support_dual_units():
    result = envelope.compute()
    import json
    from htt.obsstat import planck_lowell_irrep_projection as projection
    source = json.loads(envelope.SOURCE.read_text())
    for bundle in source["bundles"]:
        q = projection.stf2_components_to_tensor(bundle["STF2_components_K_CMB"])
        o = projection.stf3_components_to_tensor(bundle["STF3_components_K_CMB"])
        direct = np.hypot(np.linalg.norm(q) / source["q0_K_CMB"],
                          np.linalg.norm(o) / source["o0_K_CMB"])
        from_harmonics = envelope.invariant_coordinates(bundle, source["q0_K_CMB"], source["o0_K_CMB"])
        assert abs(np.linalg.norm(from_harmonics) - direct) < 1e-12
    norm = next(x["norm"] for x in result["full_norms"] if x["source"] == "hash_pinned_primary" and x["lmax"] == 32)
    row = next(x for x in result["processing_support"] if x["source"] == "hash_pinned_primary" and x["lmax"] == 32)
    assert row["dual_norm"] == 1
    radius = 0.25 * norm
    for j, base in enumerate(row["base_support"]):
        low, high = envelope.support_interval(base, 1, radius)
        assert abs(low - row["scenarios"][3]["support_lower"][j]) < 1e-12
        assert abs(high - row["scenarios"][3]["support_upper"][j]) < 1e-12
    # A unit coordinate direction in the invariant representation is dual-unit.
    for j in (0, 4, 5, 11):
        u = np.zeros(12); u[j] = 1
        assert abs(np.linalg.norm(u) - 1) < 1e-12
        assert abs(np.dot(u, radius * u) - radius) < 1e-12


def test_nonzero_cross_noise_and_missing_law():
    n = np.array([1.0, 2.0])
    assert envelope.cross_power_expectation(np.zeros(2), float(n @ n)) == 5.0
    result = envelope.compute()
    assert result["cross_noise"]["trN12"] == "UNKNOWN"
    assert result["cross_noise"]["zero_assumption"] is False
    assert result["p_value"] is None and result["berger_boos_p"] is None
    assert result["physical_Pi"] is None
