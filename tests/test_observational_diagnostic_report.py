"""Small synthetic inputs exercise reporting boundaries, not cosmological claims."""
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_observational_diagnostic_report.py"
if not SCRIPT.is_file():
    SCRIPT = Path(__file__).resolve().parents[2] / "scripts/build_observational_diagnostic_report.py"
SPEC = importlib.util.spec_from_file_location("observational_diagnostic_report", SCRIPT)
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def inputs():
    cf4 = {"task": "R2-02", "transfer_source": "none", "actual_posterior_status": "HOLD_TEST_INPUT",
           "source": {"source_sha256": {"synthetic": "a" * 64}}, "groups": 20,
           "distance": "synthetic fiducial coordinates", "frame": "synthetic J2000 sourceward",
           "actual_remainder": "UNKNOWN", "scope": "SYNTHETIC_TEST_ONLY", "claim_tier": "diagnostic_only",
           "coverage": [], "sensitivity": [], "injection": {"sentinel": "DO_NOT_PROMOTE"}}
    for sample, count in zip(REPORT.SAMPLES, (20, 10, 4)):
        cf4["coverage"].append({"sample": sample, "groups": count,
                                "fiducial_dA_min_median_max_Mpc": [1., 2., 3.],
                                "method_presence_counts": {method: count // 2 for method in REPORT.METHODS}})
        for scenario in REPORT.SCENARIOS:
            free = scenario != REPORT.SCENARIOS[0]
            sv = list(np.arange(13., 0., -1))
            if free:
                sv[-1] = 1e-14
            cf4["sensitivity"].append({"sample": sample,
                "scenario": {"name": scenario, "redshift_sigma_km_s": 100, "source_motion_sigma_km_s": 300,
                             "common_calibration_free": free, "method_nuisance": scenario == REPORT.SCENARIOS[2]},
                "singular_values": sv, "rank": 12 if free else 13, "rank_tolerance": 1e-10,
                "fixed_coefficient_scales": REPORT.SCALES, "rows": count, "nuisance_rank": 1 if free else 0})
    products = ["PR3_SMICA", "PR3_COMMANDER", "PR3_NILC", "PR3_SEVEM"]
    coeff = {p: np.arange(36.) * 1e-7 * (i + 1) for i, p in enumerate(products)}
    cmb = {"scope": "DESCRIPTIVE_REDUCED_SAME_SKY_CONTROL", "product_independence": False,
           "cross_product_covariance": None, "source_identities": {"synthetic": "b" * 64},
           "source_release": "SYNTHETIC_TEST_ONLY", "posterior_status": "HOLD_TEST_INPUT",
           "full_field_F4_status": "HOLD_TEST_INPUT", "coverage": {"common_valid_pixels": 100,
                            "pixel_count": 49152, "retained_ells": [2, 5]},
           "processing": {"id": "R8_SAME_SKY_PIXEL_CONTROL_V1", "nside": 64,
                          "fit_ells": [0, 5], "retained_ells": [2, 5], "input_products": products,
                          "valid_pixels": 100, "fits": [{"sample_id": p, "all_coefficients_K": coeff[p].tolist()} for p in products]},
           "contrasts": [{"products": [a, b], "retained_difference_norm_K": float(np.linalg.norm((coeff[a] - coeff[b])[4:])),
                          "quadrupole_difference_frobenius_K": 1e-6} for a, b in itertools.combinations(products, 2)]}
    desi = {"artifact_mode": "RELEASED_SUMMARY_REEXPRESSION", "transfer_source": "none",
            "law": {"conditioning_target": "PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE"},
            "measurement": {"qiso": 1., "qiso_sigma": .01, "DV_over_rd": 8., "DV_over_rd_sigma": .08,
                            "DV_over_rd_fid": 8., "zeff": .3}, "source": {"source_sha256": "c" * 64},
            "claim_tier": "C1", "scope": "SYNTHETIC_TEST_ONLY",
            "conditional_intervals": [{"coverage": .95, "qiso": [.98, 1.02], "DV_over_rd": [7.84, 8.16]}]}
    return cf4, cmb, desi


def test_preserves_unscaled_values_and_separates_manufactured_injection():
    cf4, cmb, _ = inputs()
    original = copy.deepcopy(cf4)
    display = REPORT.validate_cf4(cf4)
    assert cf4 == original
    assert display["sensitivity"][1]["singular_values"][-1] == 1e-14
    assert "injection" not in display
    assert display["actual_posterior_status"] == "HOLD_TEST_INPUT"
    view = REPORT.validate_cmb(cmb)
    assert len(view["retained_coefficients_K"]["PR3_SMICA"]) == 32
    assert view["retained_coefficients_K"]["PR3_SMICA"][0] == 4e-7
    assert view["product_independence"] is False


@pytest.mark.parametrize("problem", ["rank", "scale", "count", "duplicate"])
def test_rejects_cf4_semantic_schema_mismatch(problem):
    cf4, _, _ = inputs()
    if problem == "rank":
        cf4["sensitivity"][1]["rank"] = 13
    elif problem == "scale":
        cf4["sensitivity"][0]["fixed_coefficient_scales"] = [1.] * 13
    elif problem == "count":
        cf4["coverage"][0]["method_presence_counts"]["CAL"] = 21
    else:
        cf4["coverage"].append(copy.deepcopy(cf4["coverage"][0]))
    with pytest.raises(ValueError):
        REPORT.validate_cf4(cf4)


@pytest.mark.parametrize("problem", ["independence", "duplicate", "norm", "coefficients"])
def test_rejects_cmb_semantic_schema_mismatch(problem):
    _, cmb, _ = inputs()
    if problem == "independence":
        cmb["product_independence"] = True
    elif problem == "duplicate":
        cmb["contrasts"][-1] = copy.deepcopy(cmb["contrasts"][0])
    elif problem == "norm":
        cmb["contrasts"][0]["retained_difference_norm_K"] *= 2
    else:
        cmb["processing"]["fits"][0]["all_coefficients_K"].pop()
    with pytest.raises(ValueError):
        REPORT.validate_cmb(cmb)


def test_rejects_bad_desi_reexpression_and_nonfinite_input(tmp_path):
    _, _, desi = inputs()
    desi["measurement"]["DV_over_rd"] = 9.
    with pytest.raises(ValueError, match="affine"):
        REPORT.validate_desi(desi)
    path = tmp_path / "bad.json"
    path.write_text('{"hidden": [1, NaN]}')
    with pytest.raises(ValueError, match="nonfinite"):
        REPORT._load(path)


def test_fresh_directory_full_report_and_source_preservation(tmp_path):
    cf4, cmb, desi = inputs()
    paths = {}
    for name, record in (("cf4", cf4), ("cmb", cmb), ("desi", desi)):
        paths[name] = tmp_path / (name + ".json")
        paths[name].write_text(json.dumps(record))
    original = {name: p.read_bytes() for name, p in paths.items()}
    out = tmp_path / "report"
    metadata = REPORT.run(paths["desi"], paths["cf4"], paths["cmb"], out)
    assert metadata["scientific_claim_promotion"] is False
    assert metadata["raw_data_reexecution"] is False
    assert metadata["posterior"] == "NOT_PERFORMED"
    assert set(metadata["outputs"]) == {"report.md", "figure_data.json", "cf4_coverage.png", "cf4_coverage.pdf",
                                        "cf4_sensitivity.png", "cf4_sensitivity.pdf", "cmb_same_sky.png", "cmb_same_sky.pdf"}
    for name, p in paths.items():
        assert p.read_bytes() == original[name]
        assert metadata["inputs"][name]["sha256"] == hashlib.sha256(original[name]).hexdigest()
    text = (out / "report.md").read_text()
    assert "no cross-probe likelihood multiplication" in text
    assert "not posterior credible intervals" in text
    assert "HOLD_TEST_INPUT" in text
    assert "DO_NOT_PROMOTE" not in (out / "figure_data.json").read_text()
    assert (out / "cf4_coverage.png").read_bytes().startswith(b"\x89PNG")
    assert (out / "cmb_same_sky.pdf").read_bytes().startswith(b"%PDF")
    with pytest.raises(FileExistsError):
        REPORT.run(paths["desi"], paths["cf4"], paths["cmb"], out)


def test_invalid_input_leaves_no_apparently_complete_output(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{}")
    out = tmp_path / "report"
    with pytest.raises(ValueError):
        REPORT.run(path, path, path, out)
    assert not out.exists()
