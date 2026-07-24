"""PR-147 contract tests: nuisance-augmented CF4 identified sets."""
from __future__ import annotations

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
from scripts.codex_harness import run_pr147_identified_set as pr147_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUPS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
VARIANTS = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"
needs_data = pytest.mark.skipif(not (GROUPS.is_file() and VARIANTS.is_file()),
                                reason="CF4 groups/variants npz absent")
BOX = {"observable": ["primary", "Vpec", "Vpwf"],
       "calibration_fraction": [-0.05, 0.0, 0.05],
       "sigma_nl_kms": [150, 250, 350], "monopole": [True],
       "n_shells": 3}


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


def test_negative_scan_resolves_relocated_live_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = pr147_runner.yaml.safe_load(
        pr147_runner.SPEC_PATH.read_text(encoding="utf-8")
    )
    captions = json.loads(
        (REPO_ROOT / pr147_runner.OUTPUTS["captions"]).read_text(
            encoding="utf-8"
        )
    )
    legacy_path = spec["model"]["module"]
    assert not (REPO_ROOT / legacy_path).exists()
    targets = pr147_runner._scan_targets(spec, captions)
    assert targets[legacy_path]["sha256"] == pr147_runner._sha(
        pr147_runner.LIVE_MODEL_PATH
    )

    bad_spec = dict(spec)
    bad_spec["model"] = dict(spec["model"])
    bad_spec["negative_scan"] = dict(spec["negative_scan"])
    bad_spec["negative_scan"]["targets"] = ["missing/not-the-model.py"]
    with pytest.raises(SystemExit, match="negative-scan target is missing"):
        pr147_runner._scan_targets(bad_spec, captions)

    forbidden_live = tmp_path / "cf4_identified_set.py"
    forbidden_live.write_text("anomaly detected\n", encoding="utf-8")
    monkeypatch.setattr(pr147_runner, "LIVE_MODEL_PATH", forbidden_live)
    with pytest.raises(SystemExit, match="negative scan found 1 hits"):
        pr147_runner._scan_targets(spec, captions)


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
