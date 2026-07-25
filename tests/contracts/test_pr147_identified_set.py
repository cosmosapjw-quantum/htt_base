"""PR-147 contract tests: nuisance-augmented CF4 identified sets."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")

from obsstat.cf4_identified_set import (
    IdentifiedSetError,
    SetStatus,
    classify_topology,
    comparability_table,
    cross_engine_endpoint_agreement,
    generate_caption,
    identified_set,
    lint_caption,
    load_data,
    mesh_sensitivity,
    misspecification_diagnostic,
    nuisance_box_hash,
    refuse_anomaly_claim,
    refuse_cf4_p0_closure,
    refuse_favourable_endpoint,
    refuse_nuisance_tuning,
    refuse_zero_containment_isotropy,
    require_reported_unbounded,
    simultaneous_coverage,
    unbounded_scenario,
    verify_nuisance_box_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUPS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
VARIANTS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"
needs_data = pytest.mark.skipif(not (GROUPS.is_file() and VARIANTS.is_file()),
                                reason="CF4 groups/variants npz absent")
BOX = {"observable": ["primary", "Vpec", "Vpwf"],
       "calibration_fraction": [-0.05, 0.0, 0.05],
       "sigma_nl_kms": [150, 250, 350], "monopole": [True],
       "n_shells": 3}


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr147_identified_set.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr147", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_relocated_sources_are_generation_time_provenance() -> None:
    runner = _load_runner()
    aliases = runner.SOURCE_ALIASES
    historical_source = "htt/src/common/cf4_identified_set.py"
    current_source = aliases[historical_source]
    stored_result = {
        "negative_scan": {
            "targets": {
                historical_source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current_result = {
        "negative_scan": {
            "targets": {
                current_source: {"sha256": "2" * 64, "hits": []},
            },
        },
    }
    result_rel = runner.OUTPUTS["identified_set"]
    assert runner._semantic_artifact(
        result_rel, stored_result
    ) == runner._semantic_artifact(result_rel, current_result)
    current_result["negative_scan"]["targets"][current_source]["hits"] = [
        {"line": 1},
    ]
    assert runner._semantic_artifact(
        result_rel, stored_result
    ) != runner._semantic_artifact(result_rel, current_result)

    stored_manifest = {
        "input_hashes": [
            f"{historical}:{'1' * 64}" for historical in aliases
        ],
        "raw_data_pins": {
            "groups_sha256": "groups",
            "variants_sha256": "variants",
        },
    }
    current_manifest = {
        "input_hashes": [
            f"{current}:{'2' * 64}" for current in aliases.values()
        ],
        "raw_data_pins": {
            "groups_sha256": "groups",
            "variants_sha256": "variants",
        },
    }
    manifest_rel = runner.OUTPUTS["manifest"]
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["variants_sha256"] = "changed"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["raw_data_pins"]["variants_sha256"] = "variants"
    current_manifest["input_hashes"][0] = f"{current_source}:not-a-sha"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


def test_classify_topology() -> None:
    assert classify_topology(300.0, 20.0, apex_nonid_deg=90,
                             unbounded_amp=2000) == SetStatus.BOUNDED
    assert classify_topology(300.0, 120.0, apex_nonid_deg=90,
                             unbounded_amp=2000) == SetStatus.UNDETERMINED
    assert classify_topology(5000.0, 20.0, apex_nonid_deg=90,
                             unbounded_amp=2000) == SetStatus.UNBOUNDED
    assert classify_topology(300.0, 20.0, apex_nonid_deg=90,
                             unbounded_amp=2000,
                             feasible=False) == SetStatus.EMPTY


@pytest.mark.parametrize("amp_hi, cone_deg, apex_deg, threshold, message", [
    (float("nan"), float("nan"), 90.0, 2000.0, "must be finite"),
    (-1.0, 20.0, 90.0, 2000.0, "amplitude must be non-negative"),
    (300.0, -5.0, 90.0, 2000.0, "apex cone must be within"),
    (300.0, 20.0, float("nan"), 2000.0, "must be finite"),
    (300.0, 20.0, 90.0, 0.0, "threshold must be positive"),
])
def test_classify_topology_rejects_invalid_numeric_domain(
    amp_hi: float,
    cone_deg: float,
    apex_deg: float,
    threshold: float,
    message: str,
) -> None:
    with pytest.raises(IdentifiedSetError, match=message):
        classify_topology(
            amp_hi,
            cone_deg,
            apex_nonid_deg=apex_deg,
            unbounded_amp=threshold,
        )


def test_guards() -> None:
    with pytest.raises(IdentifiedSetError, match="point estimate"):
        refuse_favourable_endpoint("favourable_endpoint")
    refuse_favourable_endpoint("whole_set_reported")   # fine
    with pytest.raises(IdentifiedSetError, match="isotropy"):
        refuse_zero_containment_isotropy("set_contains_zero_isotropy")
    with pytest.raises(IdentifiedSetError, match="frozen nuisance"):
        refuse_nuisance_tuning("after_observed_result")
    with pytest.raises(IdentifiedSetError, match="anomaly"):
        refuse_anomaly_claim("anomaly")
    with pytest.raises(IdentifiedSetError, match="PR-157"):
        refuse_cf4_p0_closure("cf4_p0_closed")
    with pytest.raises(IdentifiedSetError, match="effectively unbounded"):
        require_reported_unbounded("bounded", 3000.0, 2000.0)
    require_reported_unbounded("unbounded", 3000.0, 2000.0)   # fine


def test_caption_gate() -> None:
    iset = {"shells": [{"status": "bounded",
                        "amplitude_interval_kms": [116.0, 345.0]},
                       {"status": "bounded",
                        "amplitude_interval_kms": [286.0, 826.0]}]}
    text = generate_caption(iset)
    lint_caption(text)
    for bad in (" favourable endpoint is " + "the estimate.",
                " set contains zero so " + "isotropy.",
                " anomaly " + "detected."):
        with pytest.raises(IdentifiedSetError, match="forbidden"):
            lint_caption(text + bad)


@needs_data
def test_identified_set_bounded_and_widens_with_depth() -> None:
    data = load_data(GROUPS, VARIANTS)
    iset = identified_set(data, BOX, n_shells=3, apex_nonid_deg=90,
                          unbounded_amp=2000)
    statuses = [s["status"] for s in iset["shells"]]
    # the honest outcome with the monopole always fit: bounded at every shell
    assert all(s == "bounded" for s in statuses)
    # amplitude interval widens with depth
    widths = [s["amplitude_interval_kms"][1] - s["amplitude_interval_kms"][0]
              for s in iset["shells"]]
    assert widths[-1] > widths[0]


@needs_data
def test_misspecification_diagnostic_shows_artifact() -> None:
    # omitting the monopole while sweeping the calibration manufactures the
    # artificial unbounded/undetermined topology (the reason to fit the monopole)
    data = load_data(GROUPS, VARIANTS)
    ms = misspecification_diagnostic(data, BOX, apex_nonid_deg=90,
                                     unbounded_amp=2000)
    statuses = [r["status"] for r in ms["shells"]]
    assert "unbounded" in statuses or "undetermined" in statuses


def test_nuisance_box_hash_tamper_evident() -> None:
    pinned = nuisance_box_hash(BOX)
    assert verify_nuisance_box_hash(BOX, pinned) == pinned
    with pytest.raises(IdentifiedSetError, match="content address"):
        verify_nuisance_box_hash({**BOX, "calibration_fraction": [-0.1, 0.1]},
                                 pinned)


@needs_data
def test_cross_engine_endpoint_agreement() -> None:
    data = load_data(GROUPS, VARIANTS)
    iset = identified_set(data, BOX, n_shells=3, apex_nonid_deg=90,
                          unbounded_amp=2000)
    for shell in iset["shells"]:
        ce = cross_engine_endpoint_agreement(shell, 50.0)
        # the coarse grid must lie inside the authoritative continuous interval
        assert ce["grid_inside_continuous"]


@needs_data
def test_mesh_sufficient() -> None:
    data = load_data(GROUPS, VARIANTS)
    ms = mesh_sensitivity(data, BOX, n_shells=3, refine_points=5,
                          max_shift_kms=50)
    assert ms["mesh_sufficient"]


@needs_data
def test_genuine_simultaneous_coverage_is_conservative() -> None:
    data = load_data(GROUPS, VARIANTS)
    iset = identified_set(data, BOX, n_shells=3, apex_nonid_deg=90,
                          unbounded_amp=2000)
    cov = simultaneous_coverage(data, BOX, iset, n_inject=400, seed=20260722,
                                subsample=1500, family_conf=0.95)
    # the genuine (joint) simultaneous coverage covers well above chance; the
    # per-shell undershoot at depth (Rice-bias) is disclosed, not hidden
    assert cov["genuine_simultaneous_coverage"] >= 0.80
    assert "reconstruction" in cov["excluded_nuisance"]
    assert isinstance(cov["shells_undershooting_raw_bonferroni_target"], list)


@needs_data
def test_plausible_unbounded_reported() -> None:
    data = load_data(GROUPS, VARIANTS)
    ub = unbounded_scenario(data, {**BOX, "n_shells": 3}, apex_nonid_deg=90,
                            unbounded_amp=2000)
    assert ub["status"] == "unbounded"


@needs_data
def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr147_identified_set.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_data
def test_artifacts_and_mutations() -> None:
    iset = json.loads((REPO_ROOT / "docs/generated/pr147_identified_set.json")
                      .read_text(encoding="utf-8"))
    assert len(iset["shells"]) == 3
    # the frozen box (monopole always fit) gives all-bounded shells; the
    # artificial topology lives only in the mis-specification diagnostic
    assert all(s["status"] == "bounded" for s in iset["shells"])
    assert "misspecification_diagnostic" in iset
    assert iset["nuisance_box_sha256"]
    p0 = json.loads(
        (REPO_ROOT / "docs/generated/pr147_p0_remediation_candidates.json")
        .read_text(encoding="utf-8"))
    assert all(c["status"] == "OPEN" for c in p0["candidates"])
    report = json.loads((REPO_ROOT / "docs/generated/pr147_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr147_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["groups_sha256"]
