"""PR-134 contract tests: estimand/analysis registry."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from common.estimand_registry import (
    AnalysisContract,
    BranchComponent,
    EstimandRegistry,
    EstimandRegistryError,
    GenerativeBranch,
    compose_generative_model,
    generate_caption,
    lint_caption,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load(
    (REPO_ROOT / "docs/research_program/long_horizon_rescue/pr134_spec.yaml")
    .read_text(encoding="utf-8"))
BASE = SPEC["representative_contracts"][0]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr134_estimand_registry.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr134", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_estimand_source_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.ESTIMAND_SOURCE
    registry = runner.OUTPUTS["registry"]
    stored = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            }
        }
    }
    assert runner._semantic_artifact(
        registry, stored
    ) == runner._semantic_artifact(registry, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        registry, stored
    ) != runner._semantic_artifact(registry, current)

    manifest = runner.OUTPUTS["manifest"]
    stored = {"input_hashes": [f"{source}:{'1' * 64}"]}
    current = {"input_hashes": [f"{source}:{'2' * 64}"]}
    assert runner._semantic_artifact(
        manifest, stored
    ) == runner._semantic_artifact(manifest, current)


def _registry() -> EstimandRegistry:
    reg = EstimandRegistry()
    for row in SPEC["representative_contracts"]:
        reg.register(AnalysisContract.from_payload(row))
    return reg


def test_all_five_contracts_register_with_unique_fingerprints() -> None:
    reg = _registry()
    assert set(reg.ids()) == {"CF4_MV_BULKFLOW", "K1_CMB_ISOTROPY",
                              "DESI_NUMBER_COUNT_DIPOLE", "ACT_DR6_KAPPA",
                              "JWST_ANCHORS"}
    fps = {cid: reg.get(cid).estimand_fingerprint() for cid in reg.ids()}
    assert len(set(fps.values())) == 5


def test_hidden_default_field_rejected() -> None:
    for missing in ("estimand", "selection_window", "nuisance_family",
                    "preprocessing", "allowed_transformations"):
        with pytest.raises(EstimandRegistryError, match="missing fields"):
            AnalysisContract.from_payload(
                {k: v for k, v in BASE.items() if k != missing})
    with pytest.raises(EstimandRegistryError, match="non-empty"):
        AnalysisContract.from_payload(dict(BASE, estimand="   "))


def test_independent_dependency_needs_justification() -> None:
    # underscore, hyphen, and space separators must all be caught
    for label in ("independent", "iid", "independent_rows", "flat",
                  "assumed-independent", "independent-rows",
                  "assumed independent", "iid_gaussian",
                  "uncorrelated-pairs"):
        with pytest.raises(EstimandRegistryError, match="never the silent"):
            AnalysisContract.from_payload(
                dict(BASE, dependence_cluster=label))
    # a justified flat structure is admissible
    AnalysisContract.from_payload(dict(
        BASE, dependence_cluster="independent",
        dependence_justification="single-anchor forecast, no clustering"))
    # a genuinely correlated cluster does not falsely trip
    AnalysisContract.from_payload(
        dict(BASE, dependence_cluster="spatial_correlation_woodbury"))


def test_flattening_two_surveys_rejected_via_public_api() -> None:
    reg = EstimandRegistry()
    reg.register(AnalysisContract.from_payload(BASE))
    # a second distinct id with identical specification content = the
    # same channel -> refused through the public register() path
    with pytest.raises(EstimandRegistryError, match="flattening"):
        reg.register(AnalysisContract.from_payload(
            dict(BASE, analysis_id=BASE["analysis_id"] + "_CLONE")))


def test_whitespace_cannot_mint_a_distinct_channel_identity() -> None:
    reg = EstimandRegistry()
    reg.register(AnalysisContract.from_payload(BASE))
    clone = dict(
        BASE,
        analysis_id=BASE["analysis_id"] + "_SPACE",
        estimand=BASE["estimand"] + " ",
    )
    with pytest.raises(EstimandRegistryError, match="flattening"):
        reg.register(AnalysisContract.from_payload(clone))


def test_posthoc_edit_and_multiplicity() -> None:
    reg = EstimandRegistry()
    reg.register(AnalysisContract.from_payload(BASE))
    assert reg.multiplicity(BASE["analysis_id"]) == 1
    # in-place edit (same id) is refused
    with pytest.raises(EstimandRegistryError, match="NEW analysis_id"):
        reg.register(AnalysisContract.from_payload(
            dict(BASE, selection_window="secretly_widened")))
    # a rename-only revision that does NOT bump multiplicity is refused
    with pytest.raises(EstimandRegistryError, match="look-elsewhere"):
        reg.register(AnalysisContract.from_payload(
            dict(BASE, analysis_id="CF4_MV_BULKFLOW_V2",
                 selection_window="widened_window_v2",
                 supersedes=BASE["analysis_id"])))
    # a proper revision: new id, superseding, bumped multiplicity
    reg.register(AnalysisContract.from_payload(
        dict(BASE, analysis_id="CF4_MV_BULKFLOW_V2",
             selection_window="widened_window_v2",
             supersedes=BASE["analysis_id"],
             prior_null_multiplicity="lcdm_cosmic_variance_mocks_R_binned_"
             "look_elsewhere_corrected")))
    assert reg.multiplicity("CF4_MV_BULKFLOW_V2") == 2
    # superseding an unregistered predecessor is refused
    with pytest.raises(EstimandRegistryError, match="not registered"):
        reg.register(AnalysisContract.from_payload(
            dict(BASE, analysis_id="X", selection_window="w",
                 supersedes="GHOST",
                 prior_null_multiplicity="different")))


def test_active_inference_requires_registration() -> None:
    reg = _registry()
    reg.require_registered_for_inference("CF4_MV_BULKFLOW")
    with pytest.raises(EstimandRegistryError, match="not registered"):
        reg.require_registered_for_inference("GHOST_ANALYSIS")


def test_branch_separation() -> None:
    mean = BranchComponent("A",
                           GenerativeBranch.DETERMINISTIC_TEMPLATE_MEAN, "m")
    cov = BranchComponent("A",
                          GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR, "c")
    composed = compose_generative_model(mean, cov)
    assert composed["branches_kept_separate"] is True
    # mixing branch roles
    with pytest.raises(EstimandRegistryError, match="branch mixing"):
        compose_generative_model(cov, cov)
    with pytest.raises(EstimandRegistryError, match="branch mixing"):
        compose_generative_model(mean, mean)
    # cross-analysis
    with pytest.raises(EstimandRegistryError, match="cross-analysis"):
        compose_generative_model(
            mean, BranchComponent(
                "B", GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR, "c"))


@pytest.mark.parametrize("analysis_id, descriptor", [
    ("", "mean"),
    ("analysis", ""),
])
def test_branch_component_requires_nonempty_identity_and_descriptor(
    analysis_id: str, descriptor: str
) -> None:
    with pytest.raises(EstimandRegistryError, match="non-empty string"):
        BranchComponent(
            analysis_id,
            GenerativeBranch.DETERMINISTIC_TEMPLATE_MEAN,
            descriptor,
        )


def test_dependency_graph_named_clusters() -> None:
    graph = _registry().dependency_graph()
    assert len(graph) == 5
    assert "spatial_correlation_woodbury_offdiagonal" in graph
    assert all(members for members in graph.values())


def test_enum_field_raises_registry_error() -> None:
    # an invalid generative_branch must raise the branded error, not a
    # bare ValueError (so the runner's mutation harness catches it)
    with pytest.raises(EstimandRegistryError, match="generative_branch"):
        AnalysisContract.from_payload(dict(BASE, generative_branch="bogus"))


def test_caption_gate_comprehensive() -> None:
    text = generate_caption(_registry())
    lint_caption(text)
    # the five negative-scan phrases AND the generic over-claims are all
    # caught by the exported lint (not only the inline runner sweep)
    for suffix in (" All surveys share" + " one channel.",
                   " Dependency assumed" + " independent.",
                   " Template and covariance" + " merged.",
                   " We measured the" + " dipole.",
                   " Shear" + " detected.",
                   " Bianchi family" + " identified.",
                   " Finding" + " rescued.",
                   " Validated as" + " native."):
        with pytest.raises(EstimandRegistryError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr134_estimand_registry.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_registry_graph_mutations() -> None:
    registry = json.loads(
        (REPO_ROOT / "docs/generated/pr134_contract_registry.json")
        .read_text(encoding="utf-8"))
    assert len(registry["contracts"]) == 5
    assert registry["representative_only_no_data_run"] is True
    for contract in registry["contracts"].values():
        for f in SPEC["registry"]["required_fields"]:
            assert str(contract[f]).strip()
    graph = json.loads(
        (REPO_ROOT / "docs/generated/pr134_dependency_graph.json")
        .read_text(encoding="utf-8"))
    assert graph["independent_rows_default"] == "refused"
    branches = json.loads(
        (REPO_ROOT / "docs/generated/pr134_branch_separation.json")
        .read_text(encoding="utf-8"))
    assert branches["cross_analysis_mix_refused"] is True
    assert branches["valid_same_analysis_compose"]["branches_kept_separate"]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr134_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr134_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
