from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
REGISTRY = BASE / "NOTATION_AND_CONVENTION_REGISTRY.yaml"
LEDGER = BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V3.yaml"
OVERLAY = BASE / "R4A1N_T9_AUTHORITY_OVERLAY.yaml"
PATCH = BASE / "R4A1N_MANUSCRIPT_DOMAIN_SYNC.patch"
APPENDIX = (
    ROOT
    / "docs"
    / "research_reports"
    / "appendices"
    / "HTT_REPORT_A_COVARIANT_AND_DOMAIN_CONVENTIONS.md"
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def claim(ledger: dict, claim_id: str) -> dict:
    return next(item for item in ledger["claims"] if item["id"] == claim_id)


def test_r4a1n_registry_is_v3_and_resolves_the_legacy_authority_alias():
    registry = load_yaml(REGISTRY)
    assert registry["schema"] == "htt.report_a.notation_and_convention_registry.v3"
    labels = registry["authority_labels"]
    assert labels["canonical"] == "NOTATION_AND_CONVENTION_REGISTRY_v3"
    assert labels["legacy_aliases"] == ["NOTATION_AND_CONVENTION_REGISTRY_v2"]
    assert registry["supersedes"]["prior_git_blob_sha1"] == (
        "91f319ba1e9d0be53b013456b5cfa78b49660b79"
    )


def test_r4a1n_observer_photon_and_local_boost_domains_are_explicit():
    registry = load_yaml(REGISTRY)
    assert registry["spacetime"]["metric_signature"] == "(-,+,+,+)"
    assert registry["spacetime"]["observer"]["normalization"] == "u^a u_a=-1"

    photon = registry["sky_and_boost"]["photon"]
    assert photon["causal_type"] == "FUTURE_DIRECTED_NULL"
    assert photon["null_condition"] == "p^a p_a=0"
    assert photon["measured_energy_definition"] == "E_gamma=-c p_a u^a>0"
    assert photon["decomposition"] == "p^a=(E_gamma/c)(u^a+e^a)"

    boost = registry["sky_and_boost"]["local_observer_boost"]
    assert boost["observer_spatiality"] == "u_a beta_obs^a=0"
    assert boost["domain"] == "0<=beta_obs^2<1"
    assert boost["boosted_normalization"] == "u_tilde^a u_tilde_a=-1"


def test_r4a1n_finite_sample_theorem_premises_match_t9_atomic_claims():
    registry = load_yaml(REGISTRY)
    ledger = load_yaml(LEDGER)
    notation = registry["statistical_notation"]

    row_expected = [
        "joint_exchangeability",
        "complete_row_permutation_equivariance",
        "fixed_tie_and_tail_rule",
    ]
    group_expected = [
        "null_law_invariant_under_declared_group",
        "reference_statistics_are_actual_group_orbit",
        "identity_included",
        "exact_or_valid_conditional_monte_carlo_rule",
    ]

    assert notation["exchangeable_row_rank"]["assumptions"] == row_expected
    assert notation["randomization_group_orbit"]["assumptions"] == group_expected
    assert claim(ledger, "RA-STAT-001")["assumptions"] == row_expected
    assert claim(ledger, "RA-STAT-004")["assumptions"] == group_expected

    registry_text = REGISTRY.read_text(encoding="utf-8")
    assert "joint_exchangeability_or_declared_group_randomization_hypothesis" in (
        notation["exactness_firewall"]["forbidden_legacy_premise"]
    )
    assert "joint_exchangeability_or_randomization_group" not in registry_text


def test_r4a1n_numerical_error_domain_makes_the_whitening_operator_defined():
    registry = load_yaml(REGISTRY)
    numerical = registry["numerical_uncertainty"]
    domain = numerical["domain"]
    assert domain["family_registry_nonempty"] is True
    assert domain["every_registered_family_nonempty"] is True
    assert domain["radius_condition"] == "r_f>0 for every registered family"
    assert domain["regularization_condition"] == "lambda_reg>0"
    assert numerical["positive_definiteness"] == (
        "lambda_reg>0 implies Gamma_E is positive definite"
    )


def test_r4a1n_t9_overlay_updates_authority_without_changing_claim_surface():
    overlay = load_yaml(OVERLAY)
    ledger = load_yaml(LEDGER)
    update = overlay["claim_authority_updates"]["RA-REP-002"]
    assert overlay["base_ledger"]["claim_count"] == len(ledger["claims"]) == 30
    assert update["remove_authority_label"] == "NOTATION_AND_CONVENTION_REGISTRY_v2"
    assert update["add_authority_label"] == "NOTATION_AND_CONVENTION_REGISTRY_v3"
    assert update["statement_changed"] is False
    assert update["truth_status_changed"] is False
    assert overlay["claim_firewall"]["corrected_tensorized_planck_rank"] is None
    assert overlay["claim_firewall"]["finite_healpix_containment"] == "RANK_UNRESOLVED"


def test_r4a1n_appendix_and_bounded_patch_preserve_publication_scope():
    appendix = APPENDIX.read_text(encoding="utf-8")
    patch = PATCH.read_text(encoding="utf-8")

    required_appendix = (
        "u^a u_a=-1",
        "p^a p_a=0",
        "E_\\gamma=-c\\,p_a u^a>0",
        "u_a\\beta_{\\rm obs}^a=0",
        "0\\leq\\beta_{\\rm obs}^2<1",
        "\\lambda_{\\rm reg}>0",
        "finite-HEALPix containment remains rank-unresolved",
        "native BASS solver claims remain outside the report",
    )
    for needle in required_appendix:
        assert needle in appendix

    required_patch = (
        "+u^a u_a=-1.",
        "+p^a p_a=0,",
        "+E_\\gamma=-c\\,p_a u^a>0.",
        "+u_a\\beta_{\\rm obs}^a=0,",
        "+0\\leq\\beta_{\\rm obs}^2<1,",
        "+\\widetilde u^a\\widetilde u_a=-1.",
        "+\\(r_f>0\\). Fix \\(\\lambda_{\\rm reg}>0\\)",
        "-and define",
        "+Define",
    )
    for needle in required_patch:
        assert needle in patch
