from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
K0 = BASE / "K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK_V2.yaml"
EVIDENCE = BASE / "K1R_TYPED_KINEMATICAL_MES_EVIDENCE_LEDGER.yaml"
K2 = BASE / "K2_KINEMATICAL_CLAIM_RECOMPILE_INPUT_V2.yaml"
PACK = ROOT / "docs" / "research_reports" / "theory_packs" / "K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md"


def _yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_geometry_dimension_and_parity_registry_is_explicit() -> None:
    data = _yaml(K0)
    geometry = data["state_factorisation"]["geometry"]
    scalar = geometry["scalar_coordinate"]
    assert scalar["name"] == "DeltaOmega_k"
    assert scalar["semantic_type"] == "SIGNED_SCALAR_CURVATURE_BUDGET_COORDINATE"
    assert scalar["dimension"] == 1
    assert scalar["forbidden_name"] == "anisotropic_curvature_budget"

    registry = {row["id"]: row for row in data["representation_registry"]}
    assert registry["DeltaOmega_k"]["o3_type"] == "SCALAR"
    assert registry["spatial_curvature_stf5"]["o3_type"] == "STF2_POLAR"
    assert registry["magnetic_weyl_stf5"]["o3_type"] == "STF2_AXIAL"

    dimensions = data["dimension_counts"]
    assert dimensions["general_core"]["raw_dimension"] == 18
    assert dimensions["general_core"]["locally_free_SO3_quotient_dimension"] == 15
    assert dimensions["geodesic_core"]["raw_dimension"] == 15
    assert dimensions["geodesic_core"]["locally_free_SO3_quotient_dimension"] == 12
    assert "locally free SO3 strata" in dimensions["qualifier"]
    assert "global orbit-separation" in dimensions["qualifier"]


def test_geodesic_acceleration_premise_is_not_a_numerical_anchor() -> None:
    data = _yaml(K0)
    acceleration = data["sector_authority"]["acceleration"]
    assert acceleration["branch_authority"]["branch"] == "MES_G_ACCEL"
    assert acceleration["branch_authority"]["status"] == "VERIFIED_STRUCTURAL"
    assert acceleration["branch_authority"]["meaning"] == "GEODESIC_DOMAIN_PREMISE_A_EQUALS_ZERO"
    assert acceleration["numerical_anchor"]["status"] == "NO_MES_ANCHOR"
    assert acceleration["numerical_anchor"]["meaning"] == "NO_NUMERICAL_RADIUS_OR_DENOMINATOR"
    assert acceleration["outside_geodesic_branch"] == "NO_ACTIVE_VERIFIED_ACCELERATION_BOUND"


def test_k1r_joint_identification_and_shared_data_firewall() -> None:
    text = PACK.read_text(encoding="utf-8")
    required = (
        "\\Theta(y;\\eta)",
        "B_{\\rm MES}(y;\\eta)",
        "Their appearance as separate set factors does not make them independent evidence",
        "MES ceiling construction, anchor conditioning",
        "feasible response-kernel fibre contains no other admissible state",
        "Full column rank of the response is sufficient but not necessary",
    )
    for needle in required:
        assert needle in text

    evidence = _yaml(EVIDENCE)
    rows = {row["id"]: row for row in evidence["results"]}
    identified = rows["K1R-T9-JOINT-IDENTIFIED-SET"]
    assert "not independent evidence" in identified["shared_data_rule"]
    assert "independent_evidence_multiplication_without_joint_law" in identified["forbidden"]
    assert "data_dependent_anchor_omitted_from_row_equivariance" in identified["forbidden"]


def test_product_gauge_quadratic_stress_and_coupled_set_are_separate() -> None:
    text = PACK.read_text(encoding="utf-8")
    assert "rho_{B_{\\rm prod}}(x)^2" in text
    assert "\\max_j S_j" in text
    assert "need not factorise after response, physics or nuisance constraints" in text
    assert "rho_{B_0}(1,1)=1" in text
    assert "rho_F(1,1)=2" in text
    assert "different diagnostics" in text

    evidence = _yaml(EVIDENCE)
    rows = {row["id"]: row for row in evidence["results"]}
    gauge = rows["K1R-T6-PRODUCT-GAUGE"]
    stress = rows["K1R-T7-QUADRATIC-STRESS"]
    assert "apply_product_gauge_to_coupled_response_feasible_set" in gauge["forbidden"]
    assert stress["realization_conditional_denominator"] == "RATIO_UNIDENTIFIED"
    assert "equate_gauge_margin_with_quadratic_exceedance" in stress["forbidden"]


def test_k2_v2_maps_twelve_results_to_a_provisional_40_claim_surface() -> None:
    data = _yaml(K2)
    candidate = data["candidate_surface"]
    assert candidate["proposed_new_atomic_claims"] == 10
    assert candidate["proposed_existing_claim_revisions"] == 4
    assert candidate["provisional_candidate_total"] == 40
    assert candidate["final_count_status"] == "PROVISIONAL_UNTIL_K2_UNIQUENESS_IMPLICATION_AND_CITATION_AUDIT"

    additions = data["proposed_new_claims"]
    revisions = data["proposed_existing_claim_revisions"]
    assert len(additions) == 10
    assert len({row["id"] for row in additions}) == 10
    assert {row["id"] for row in revisions} == {
        "RA-MES-002",
        "RA-MES-003",
        "RA-RESP-001",
        "RA-STAT-002",
    }

    coverage = data["source_theorem_coverage"]
    assert len(coverage) == 12
    assert all(targets for targets in coverage.values())
    policy = data["claim_count_policy"]
    assert policy["canonical_before_K2"] == 30
    assert policy["provisional_after_additions"] == 40
    assert policy["final_count_frozen"] is False


def test_k1r_scientific_firewalls_remain_closed() -> None:
    text = PACK.read_text(encoding="utf-8")
    required = (
        "no Planck/FFP10 execution",
        "no physical shear, vorticity or acceleration estimate",
        "no finite-HEALPIX no-go theorem",
        "no native BASS result",
        "No anchor-to-state arrow is generative",
        "No observable-to-physical tensor map is admitted without a declared response",
        "NO_CLAIM_PROMOTION",
    )
    for needle in required:
        assert needle in text

    crosswalk = _yaml(K0)
    firewall = crosswalk["scope_firewall"]
    assert firewall["scalar_only_mes_observational_rank"] == "RETIRED"
    assert firewall["corrected_planck_result"] == "NONE"
    assert firewall["finite_healpix_containment"] == "RANK_UNRESOLVED"
    assert firewall["native_bass_solver"] == "EXCLUDED"
    assert firewall["claim_promotion"] is False
