from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK.yaml"
)


def _load() -> dict[str, object]:
    return yaml.safe_load(CROSSWALK.read_text(encoding="utf-8"))


def test_exact_donor_identity_and_git_divergence_are_preserved() -> None:
    data = _load()
    donor = data["donor_physical_state_authority"]
    assert donor["published_head"] == "6bafca66285ef071081453313bb7d2d6b261599c"
    assert donor["relation_to_pr449"] == "GIT_DIVERGED_SEMANTIC_AUTHORITY_IMPORT_ONLY"
    policy = donor["import_policy"]
    assert policy["copy_production_code_into_report_branch"] is False
    assert policy["preserve_separate_git_ancestry"] is True
    rows = donor["source_files"]
    assert len(rows) == 7
    assert len({row["git_blob_sha1"] for row in rows}) == len(rows)


def test_registered_mes_channels_and_typed_absences() -> None:
    data = _load()
    sectors = {row["sector"]: row for row in data["sector_crosswalk"]}
    assert sectors["shear"]["mes_anchor"]["status"] == "VERIFIED"
    assert sectors["shear"]["mes_anchor"]["branch"] == "MES_G_SIGMA"
    assert sectors["vorticity"]["mes_anchor"]["status"] == "VERIFIED"
    assert sectors["vorticity"]["mes_anchor"]["branch"] == "MES_G_OMEGA"
    assert sectors["acceleration"]["mes_anchor"]["status"] == "NO_MES_ANCHOR"
    assert sectors["anisotropic_curvature_budget"]["mes_anchor"]["status"] == "NO_MES_ANCHOR"


def test_response_and_scope_firewalls() -> None:
    data = _load()
    sectors = {row["sector"]: row for row in data["sector_crosswalk"]}
    beta_ro = sectors["observer_radiation_velocity"]
    assert beta_ro["response_status"].startswith("WU010_")
    assert "NOT_GLOBAL_TILT" in beta_ro["identification_status"]
    firewall = data["scope_firewall"]
    assert firewall["scalar_only_mes_observational_rank"] == "RETIRED"
    assert firewall["scalar_mes_sector_bounds"] == "RETAINED_AS_CONDITIONAL_ANCHORS"
    assert firewall["scalar_to_tensor_reconstruction"] == "FORBIDDEN"
    assert firewall["observable_QO_equals_physical_sigma_omega"] == "FORBIDDEN"
    assert firewall["native_bass_solver"] == "EXCLUDED"
    assert firewall["corrected_planck_result"] == "NONE"
    assert firewall["finite_healpix_containment"] == "RANK_UNRESOLVED"


def test_k0_does_not_promote_provisional_claims() -> None:
    data = _load()
    candidates = data["provisional_claim_candidates"]
    assert len(candidates) == 10
    policy = data["claim_count_policy"]
    assert policy["no_claim_promotion_in_k0"] is True
    assert policy["final_count_frozen_in"] == "K2_CLAIM_LEDGER_RECOMPILE"
    assert data["terminal"].startswith("PASS_K0_")
