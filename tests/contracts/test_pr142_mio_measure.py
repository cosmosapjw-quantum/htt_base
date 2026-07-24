"""PR-142 contract tests: MIO joint-measure F/Pi/G_F + matched null."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from common.mio_joint_measure import (
    COMPONENTS,
    DepartureTable,
    DepthPolicy,
    MeasureError,
    MeasureSpec,
    Pairing,
    feasible_range_GF,
    generate_caption,
    lint_caption,
    matched_null_distribution,
    measure_F,
    measure_Pi,
    pairing_counterexample,
    permutation_invariant,
    refuse_forbidden_role,
    refuse_measure_substitution,
    require_justified_measure,
    require_matched_null,
    require_registered_measure_family,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr142_mio_measure.py"
    spec = importlib.util.spec_from_file_location("run_pr142", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH

    measures_rel = runner.OUTPUTS["measures"]
    stored = {
        "F": {"value": 1.23456789},
        "negative_scan": {
            "targets": {source: {"sha256": "1" * 64, "hits": []}},
        },
    }
    current = {
        "F": {"value": 1.234567891},
        "negative_scan": {
            "targets": {source: {"sha256": "2" * 64, "hits": []}},
        },
    }
    assert runner._semantic_artifact(
        measures_rel, stored
    ) == runner._semantic_artifact(measures_rel, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        measures_rel, stored
    ) != runner._semantic_artifact(measures_rel, current)
    current["negative_scan"]["targets"][source] = {
        "sha256": "not-a-sha",
        "hits": [],
    }
    assert runner._semantic_artifact(
        measures_rel, stored
    ) != runner._semantic_artifact(measures_rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest_rel, stored
    ) == runner._semantic_artifact(manifest_rel, current)


def _table(seed=42, n=40, shift=1.2):
    rng = np.random.Generator(np.random.PCG64(seed))
    vals = rng.normal(0, 1, (n, 4))
    vals[:, COMPONENTS.index("Omega_tilt")] += shift
    return DepartureTable(values=vals, columns=COMPONENTS,
                          depth=tuple(i % 4 for i in range(n)),
                          pair=tuple(i // 2 for i in range(n)))


SPEC = MeasureSpec(COMPONENTS, (1.0, 1.0, 1.0, 1.0), Pairing.UNPAIRED,
                   DepthPolicy.RAW)


def test_canonical_order_enforced() -> None:
    with pytest.raises(MeasureError, match="canonical"):
        MeasureSpec(("W2", "Sigma2"), (1.0, 1.0), Pairing.UNPAIRED,
                    DepthPolicy.RAW)
    # a subset in canonical order is fine
    MeasureSpec(("Sigma2", "Omega_tilt"), (1.0, 1.0), Pairing.UNPAIRED,
                DepthPolicy.RAW)


def test_F_and_Pi_are_distinct_and_permutation_invariant() -> None:
    t = _table()
    assert measure_F(t, SPEC) != measure_Pi(t, SPEC)
    assert permutation_invariant(t, SPEC, "F", seed=1)
    assert permutation_invariant(t, SPEC, "Pi", seed=1)


def test_measure_appropriate_matched_nulls() -> None:
    t = _table()
    # Pi (signed) -> sign-flip null centered at 0, TWO-SIDED p
    pi_null = matched_null_distribution(t, SPEC, "Pi", 7, 3000,
                                        null_type="sign_flip")
    assert abs(pi_null["null_mean"]) < 0.1
    assert pi_null["sided"] == "two_sided"
    assert pi_null["p_value"] < 0.05
    # F (magnitude) -> reference-scale null, one-sided upper
    f_null = matched_null_distribution(t, SPEC, "F", 7, 3000,
                                       null_type="reference_scale")
    assert f_null["null_std"] > 0
    assert f_null["sided"] == "upper"
    # a sign-flip null for F is DEGENERATE and refused
    with pytest.raises(MeasureError, match="DEGENERATE"):
        matched_null_distribution(t, SPEC, "F", 7, 100, null_type="sign_flip")


def test_pi_two_sided_detects_negative_contrast() -> None:
    # a NEGATIVE contrast of equal magnitude must be detected (the one-sided
    # upper tail would mis-report it as p ~ 1) — the review regression
    neg = _table(shift=-1.2)
    d = matched_null_distribution(neg, SPEC, "Pi", 7, 3000,
                                  null_type="sign_flip")
    assert d["observed"] < 0
    assert d["p_value"] < 0.05


def test_reference_null_scale_validated_against_data() -> None:
    from common.mio_joint_measure import require_null_scale_consistent
    t = _table()
    require_null_scale_consistent(t, SPEC)   # null_scale=1 matches data ~1
    mis = MeasureSpec(COMPONENTS, (1.0, 1.0, 1.0, 1.0), Pairing.UNPAIRED,
                      DepthPolicy.RAW, null_scale=(0.5, 1.0, 1.0, 1.0))
    with pytest.raises(MeasureError, match="inconsistent"):
        require_null_scale_consistent(t, mis)


def test_paired_bootstrap_matches_paired_estimand() -> None:
    from common.mio_joint_measure import bootstrap_uncertainty
    t = _table()
    paired = MeasureSpec(COMPONENTS, (1.0, 1.0, 1.0, 1.0), Pairing.PAIRED,
                         DepthPolicy.RAW)
    se_paired = bootstrap_uncertainty(t, paired, "Pi", 11, 200)
    se_unpaired = bootstrap_uncertainty(t, SPEC, "Pi", 11, 200)
    # the paired and unpaired bootstraps quantify DIFFERENT estimands
    assert se_paired != se_unpaired
    assert se_paired > 0


def test_pairing_counterexample() -> None:
    t = _table()
    paired = MeasureSpec(COMPONENTS, (1.0, 1.0, 1.0, 1.0), Pairing.PAIRED,
                         DepthPolicy.RAW)
    pc = pairing_counterexample(t, paired, "F")
    assert pc["differ"] is True
    assert pc["paired"] != pc["unpaired"]


def test_gf_is_set_valued_and_correct() -> None:
    gf = feasible_range_GF({c: (-0.5, 0.7) for c in COMPONENTS}, SPEC)
    assert gf["is_scalar_posterior"] is False
    assert gf["degenerate_point"] is False
    # each interval spans 0, so lo_abs = 0 -> lo = 0; hi = sqrt(4 * 0.7^2)
    assert abs(gf["lo"]) < 1e-12
    assert abs(gf["hi"] - (4 * 0.7 ** 2) ** 0.5) < 1e-9
    # a degenerate single-point identified set is flagged but STILL not a
    # posterior
    deg = feasible_range_GF({c: (0.3, 0.3) for c in COMPONENTS}, SPEC)
    assert deg["degenerate_point"] is True
    assert deg["is_scalar_posterior"] is False


def test_unjustified_measure_no_calibrated_scalar() -> None:
    unjust = MeasureSpec(COMPONENTS, (1.0, 1.0, 1.0, 1.0), Pairing.UNPAIRED,
                         DepthPolicy.RAW, justified=False)
    with pytest.raises(MeasureError, match="no scientifically-justified"):
        require_justified_measure(unjust)
    with pytest.raises(MeasureError, match="no scientifically-justified"):
        matched_null_distribution(_table(), unjust, "F", 1, 100)


def test_guards() -> None:
    for role in ("posterior_probability", "evidence", "likelihood_term",
                 "truth_certificate", "htt_likelihood"):
        with pytest.raises(MeasureError, match="not a"):
            refuse_forbidden_role(role)
    refuse_forbidden_role("diagnostic_summary")   # a real role is fine
    with pytest.raises(MeasureError, match="distinct diagnostics"):
        refuse_measure_substitution("F", "Pi")
    # unmatched null spec refused
    other = MeasureSpec(COMPONENTS, (2.0, 1.0, 1.0, 1.0), Pairing.UNPAIRED,
                        DepthPolicy.RAW)
    with pytest.raises(MeasureError, match="unmatched null"):
        require_matched_null(SPEC, other)
    require_matched_null(SPEC, SPEC)   # matched is fine
    # post-hoc weight change without multiplicity refused
    with pytest.raises(MeasureError, match="registered diagnostic family"):
        require_registered_measure_family(SPEC, other, None, None)
    require_registered_measure_family(SPEC, other, "prev", 3)   # ok w/ family


def test_caption_gate() -> None:
    text = generate_caption("Pi", 0.0023, 0.26, "calibrated")
    lint_caption(text)
    for bad in (" f is the posterior " + "probability.",
                " the mio measure is the " + "evidence.",
                " f substitutes " + "for pi."):
        with pytest.raises(MeasureError, match="forbidden"):
            lint_caption(text + bad)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr142_mio_measure.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_and_mutations() -> None:
    meas = json.loads((REPO_ROOT / "docs/generated/pr142_measures_report.json")
                      .read_text(encoding="utf-8"))
    assert meas["F"]["null_type"] == "reference_scale"
    assert meas["Pi"]["null_type"] == "sign_flip"
    assert meas["Pi"]["sided"] == "two_sided"
    assert meas["Pi"]["p_value"] < 0.05
    inv = json.loads((REPO_ROOT / "docs/generated/pr142_invariance_report.json")
                     .read_text(encoding="utf-8"))
    assert inv["F_permutation_invariant"] is True
    assert inv["pairing_counterexample"]["differ"] is True
    gf = json.loads((REPO_ROOT / "docs/generated/pr142_gf_range.json")
                    .read_text(encoding="utf-8"))
    assert gf["is_scalar_posterior"] is False
    nj = json.loads((REPO_ROOT / "docs/generated/pr142_no_justified_demo.json")
                    .read_text(encoding="utf-8"))
    assert nj["status"] == "no_justified_measure"
    assert nj["calibrated_scalar_refused"] is True
    assert len(nj["measure_family_sensitivity"]) == 3
    assert nj["two_sided_pi"]["p_value"] < 0.05     # negative contrast found
    assert nj["mis_set_null_scale_refused"] is True
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr142_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr142_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
