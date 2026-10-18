"""Independent vector controls; no synthetic test is called a Planck null."""
import copy

import numpy as np
import pytest

import analyze_matched_splits as a


def fixture():
    rng = np.random.default_rng(194)
    common = rng.normal(size=(64, 5))*1e-6
    inner = common+rng.normal(size=(64, 5))*1e-8
    delta = inner-common
    raw = delta[:, 0]+rng.normal(size=64)*1e-8
    recon = raw+rng.normal(size=64)*1e-9
    result = {"matched_coefficients": {"common": common, "three_way_intersection": inner},
              "matched_contrast": delta, "original_coefficients": {
                  "common": np.zeros((64, 5)), "three_way_intersection": np.column_stack([raw]*5)},
              "shell_identity_relative": 1e-15, "split_linearity_relative": 1e-15}
    native = {"schema": "htt.L01_native_matched_split_stream/1",
              "status": "PASS_NATIVE_MATCHED_SPLIT_ACCOUNTING", "products": list(a.PRODUCTS),
              "nside": 2048, "native_SHT_run": False, "beam_applied_again": False,
              "paper_gate": "NOT_READY_TO_SUBMIT", "source_window_sha256": "fixed_window",
              "full_native_moment_replay": {key: 1e-15 for key in a.REGIONS},
              "result": result, "raw_moments": {"selected_pixels": {"common": 100}}, "seconds": 1.}
    anchor = {"native_window_sha256": "fixed_window", "contrast_raw_K_CMB": raw,
              "contrast_reconstructed_K_CMB": recon}
    bound = {"groups": {}, "all_refined_using_orthogonal_E_B_blocks": {
        "matched_reconstructed_angle_degrees_interval": [0, 180]}}
    for name, ix in a.groups().items():
        lengths = {"anchor_norm": np.linalg.norm(raw[ix]), "matched_norm": np.linalg.norm(delta[ix, 0]),
                   "reconstructed_norm": np.linalg.norm(recon[ix]),
                   "anchor_matched_distance": np.linalg.norm(raw[ix]-delta[ix, 0]),
                   "anchor_reconstructed_distance": np.linalg.norm(raw[ix]-recon[ix])}
        bound["groups"][name] = {"input_lengths_K_CMB": lengths,
                                "matched_reconstructed_angle_degrees_interval": [0, 180]}
    return native, anchor, bound


def test_angle_and_scalar_projection_against_independent_lstsq():
    x, y = np.array([2., 3., -1.]), np.array([1., 0., 1.])
    measured = a.compare(x, y)
    gain = max(0., np.linalg.lstsq(y[:, None], x, rcond=None)[0][0])
    assert measured["nonnegative_gain_right_to_left"] == pytest.approx(gain)
    assert measured["nonnegative_fit_residual_fraction"] == pytest.approx(np.linalg.norm(x-gain*y)/np.linalg.norm(x))
    assert measured["angle_degrees"] == pytest.approx(np.degrees(np.arccos(1/np.sqrt(28))))


def test_negative_cross_and_zero_are_not_silently_positive():
    result = a.compare(np.array([1., 0.]), np.array([-2., 0.]))
    assert result["cosine"] == -1 and result["nonnegative_gain_right_to_left"] == 0
    assert result["nonnegative_fit_residual_fraction"] == 1
    assert a.compare(np.zeros(2), np.ones(2))["angle_degrees"] is None


def test_orthogonal_basis_and_uniform_units_preserve_geometry():
    rng = np.random.default_rng(24)
    q, _ = np.linalg.qr(rng.normal(size=(7, 7)))
    x, y = rng.normal(size=(2, 7))
    first = a.compare(x, y)
    second = a.compare(1e-9*q@x, 1e-9*q@y)
    for field in ("cosine", "angle_degrees", "nonnegative_gain_right_to_left", "nonnegative_fit_residual_fraction"):
        assert first[field] == pytest.approx(second[field])


def test_subject_norms_retain_half_difference_factor_and_energy_partition():
    rng = np.random.default_rng(6)
    matrix = rng.normal(size=(64, 5))*1e-9
    d = a.diagnostics(matrix)
    expected = np.linalg.norm((matrix[:, 1]-matrix[:, 2])/2)*1e9
    assert d["all"]["norms_nK_CMB"]["HM_half_difference"] == pytest.approx(expected)
    for subject, norm in d["all"]["norms_nK_CMB"].items():
        assert norm**2 == pytest.approx(sum(d[key]["norms_nK_CMB"][subject]**2 for key in ("E", "B")))


def test_analyze_preserves_claim_ceiling_and_actual_vectors():
    native, anchor, bound = fixture()
    report, matrices, delta = a.analyze(native, anchor, bound)
    assert report["p_value"] is None and report["noise_covariance"] is None
    assert report["node_acceptance"] == "PARTIAL_EXECUTION_L01_PENDING"
    np.testing.assert_array_equal(delta, native["result"]["matched_contrast"])


@pytest.mark.parametrize("failure", ["replay", "support", "bound", "basis", "length"])
def test_missing_replay_or_wrong_source_geometry_rejected(failure):
    native, anchor, bound = copy.deepcopy(fixture())
    if failure == "replay": native["full_native_moment_replay"]["common"] = 1e-3
    if failure == "support": anchor["native_window_sha256"] = "different"
    if failure == "bound": bound["all_refined_using_orthogonal_E_B_blocks"]["matched_reconstructed_angle_degrees_interval"] = [170, 180]
    if failure == "basis": native["result"]["matched_coefficients"]["common"] = np.zeros((63, 5))
    if failure == "length": bound["groups"]["E"]["input_lengths_K_CMB"]["matched_norm"] *= 1.01
    with pytest.raises((ValueError, AssertionError)):
        a.analyze(native, anchor, bound)


@pytest.mark.parametrize("bad", [np.zeros((64, 4)), np.full((64, 5), np.nan), np.ones((64, 5), dtype=complex)])
def test_invalid_products_rejected(bad):
    with pytest.raises(ValueError): a.subjects(bad)
