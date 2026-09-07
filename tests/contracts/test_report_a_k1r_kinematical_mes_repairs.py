from __future__ import annotations

from pathlib import Path
import re

import pytest
import yaml
from pybtex.database import parse_string


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
K0 = BASE / "K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK_V2.yaml"
EVIDENCE = BASE / "K1R_TYPED_KINEMATICAL_MES_EVIDENCE_LEDGER.yaml"
K2 = BASE / "K2_KINEMATICAL_CLAIM_RECOMPILE_INPUT_V2.yaml"
PACK = ROOT / "docs" / "research_reports" / "theory_packs" / "K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md"


def _yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


JOINT = "Theorem K1R-T8 — jointly conditioned physical identified set"
SINGLETON = "Theorem K1R-T9 — singleton feasible-fibre criterion"
STATUS = "Status and authority"
SPINE = "Integrated scientific spine"


def _prose(text: str) -> str:
    return " ".join(text.split()).casefold()


def _math(text: str) -> str:
    return "".join(text.split())


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    assert text.count(marker) == 1, heading
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def _active_text(section: str) -> str:
    # Historical block quotes and code examples cannot supply active assertions.
    section = re.sub(r"(?ms)^```[^\n]*\n.*?^```[^\n]*$", "", section)
    return "\n".join(line for line in section.splitlines() if not line.lstrip().startswith(">"))


def _paragraph(section: str, prefix: str) -> str:
    matches = [
        paragraph for paragraph in re.split(r"\n\s*\n", _active_text(section))
        if _prose(paragraph).startswith(_prose(prefix))
    ]
    assert len(matches) == 1, prefix
    return matches[0]


def _check_joint_document(text: str) -> None:
    joint = _section(text, JOINT)
    shared = _paragraph(joint, "The anchor and response restrictions")
    assert _prose(
        "Their appearance as separate set factors does not make them independent evidence"
    ) in _prose(shared)
    analysis = _paragraph(joint, "The complete data-to-output map")
    assert _prose(
        "The complete data-to-output map used in a finite-null rank must therefore "
        "include MES ceiling construction, anchor conditioning"
    ) in _prose(analysis)

    singleton = _section(text, SINGLETON)
    premise = _paragraph(singleton, "Consider")
    assert _prose(premise.split(r"\(", 1)[0]) == _prose("Consider an exact linear response")
    rank = _paragraph(singleton, "Full column rank")
    assert _prose(
        "Full column rank of the response is sufficient but not necessary"
    ) in _prose(rank)

    # Check the source's equations; mathematical letter case is significant.
    for section, expression in (
        (joint, r"\Theta(y;\eta)=D_\eta\cap B_{\rm MES}(y;\eta)\cap\mathcal R_\eta^{-1}(C_y(\eta))"),
        (singleton, r"\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R_\eta)"),
        (singleton, r"\Theta(y;\eta)=\{X_0\}\quad\Longleftrightarrow\quad\{h\in\ker\mathcal R_\eta:X_0+h\in F_y\}=\{0\}"),
    ):
        displays = re.findall(r"\\\[(.*?)\\\]", _active_text(section), re.DOTALL)
        assert any(_math(expression) in _math(display) for display in displays), expression


def _check_firewalls_document(text: str) -> None:
    prologue = _paragraph(_section(text, STATUS), "The donor is imported")
    for prohibition in (
        "no Planck/FFP10 execution",
        "no physical shear, vorticity or acceleration estimate",
        "no finite-HEALPix no-go theorem",
        "no native BASS result",
    ):
        assert _prose(prohibition) in _prose(prologue), prohibition
    spine = _paragraph(_section(text, SPINE), "No anchor-to-state")
    for prohibition in (
        "No anchor-to-state arrow is generative",
        "No observable-to-physical tensor map is admitted without a declared response",
    ):
        assert _prose(prohibition) in _prose(spine), prohibition
    assert "NO_CLAIM_PROMOTION" in _section(text, "Terminal").splitlines()


def _mutate_section_once(text: str, heading: str, target: str, replacement: str) -> str:
    section = _section(text, heading)
    pattern = re.compile(r"\s+".join(re.escape(word) for word in target.split()))
    assert len(list(pattern.finditer(section))) == 1, target
    changed, count = pattern.subn(lambda match: replacement, section)
    assert count == 1 and changed != section, target
    marker = f"## {heading}\n"
    before, after = text.split(marker, 1)
    assert after.startswith(section)
    mutated = before + marker + changed + after[len(section):]
    assert mutated != text, target
    return mutated


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
    _check_joint_document(text)

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
    _check_firewalls_document(text)

    crosswalk = _yaml(K0)
    firewall = crosswalk["scope_firewall"]
    assert firewall["scalar_only_mes_observational_rank"] == "RETIRED"
    assert firewall["corrected_planck_result"] == "NONE"
    assert firewall["finite_healpix_containment"] == "RANK_UNRESOLVED"
    assert firewall["native_bass_solver"] == "EXCLUDED"
    assert firewall["claim_promotion"] is False


CITATION_TITLES = {
    "RANDOMIZATION_2024": "Randomization Inference: Theory and Applications",
    "ROLDAN_NOTARI_QUARTIN_2016": "Interpreting the CMB aberration and Doppler measurements: boost or intrinsic dipole?",
    "LI_1999": "Relative perturbation theory: II. Eigenspace and singular subspace variations",
}
CITATION_MATRIX = BASE / "REPORT_A_CITATION_PROVENANCE_MATRIX_V2.yaml"


def test_citation_matrix_whole_file_preserves_titles_and_keys() -> None:
    data = _yaml(CITATION_MATRIX)
    bibliography = parse_string(
        (ROOT / "docs/research_reports/HTT_REPORT_A_REFERENCES.bib").read_text(encoding="utf-8"),
        "bibtex",
    )
    base = _yaml(BASE / "T9_INTEGRATED_CLAIM_EVIDENCE_LEDGER_V4.yaml")
    assert len(data["source_registry"]) == len(bibliography.entries) == 17
    assert set(data["source_registry"]) == set(bibliography.entries)
    assert len(data["claim_citations"]) == len(base["claims"]) == 30
    assert set(data["claim_citations"]) == {row["id"] for row in base["claims"]}
    for key, title in CITATION_TITLES.items():
        assert data["source_registry"][key]["title"] == title


@pytest.mark.parametrize("title", CITATION_TITLES.values(), ids=CITATION_TITLES.keys())
def test_each_unquoted_citation_title_is_rejected(title: str) -> None:
    corrected = CITATION_MATRIX.read_text(encoding="utf-8")
    yaml.safe_load(corrected)
    quoted = f'    title: "{title}"\n'
    assert corrected.count(quoted) == 1
    mutated = corrected.replace(quoted, f"    title: {title}\n", 1)
    assert mutated != corrected
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(mutated)


@pytest.mark.parametrize("variant", ("prose_reflow", "healpix_case"))
def test_documentary_guards_accept_harmless_formatting(variant: str) -> None:
    original = PACK.read_text(encoding="utf-8")
    if variant == "prose_reflow":
        changed = original
        for heading, prefix in (
            (JOINT, "The anchor and response restrictions"),
            (JOINT, "The complete data-to-output map"),
            (SINGLETON, "Full column rank"),
            (STATUS, "The donor is imported"),
            (SPINE, "No anchor-to-state"),
        ):
            paragraph = _paragraph(_section(changed, heading), prefix)
            changed = _mutate_section_once(changed, heading, paragraph, "  \n ".join(paragraph.split()))
    else:
        changed = _mutate_section_once(original, STATUS, "HEALPix", "HEALPIX")
    assert changed != original
    _check_joint_document(changed)
    _check_firewalls_document(changed)


DOCUMENT_MUTATIONS = (
    ("shared_data_deleted", "joint", JOINT, "does not make them independent evidence", ""),
    ("shared_data_reversed", "joint", JOINT, "does not make them independent evidence", "makes them independent evidence"),
    ("mes_ceiling_deleted", "joint", JOINT, "MES ceiling construction, ", ""),
    ("anchor_conditioning_deleted", "joint", JOINT, "anchor conditioning, ", ""),
    ("exact_deleted", "joint", SINGLETON, "an exact linear response", "a linear response"),
    ("linear_deleted", "joint", SINGLETON, "an exact linear response", "an exact response"),
    ("equivalence_reversed", "joint", SINGLETON, r"\Longleftrightarrow", r"\Longrightarrow"),
    ("zero_kernel_changed", "joint", SINGLETON, r"\}=\{0\}", r"\}=\{h_0\}"),
    ("math_case_changed", "joint", SINGLETON, r"F_y\cap(X_0+\ker\mathcal R_\eta)", r"F_y\cap(x_0+\ker\mathcal R_\eta)"),
    ("anchor_generative", "firewalls", SPINE, "No anchor-to-state arrow is generative", "An anchor-to-state arrow is generative"),
    ("response_prerequisite_removed", "firewalls", SPINE, "No observable-to-physical tensor map is admitted without a declared response", "An observable-to-physical tensor map is admitted without a declared response"),
    ("observation_exclusion_removed", "firewalls", STATUS, "no Planck/FFP10 execution,", ""),
    ("physical_estimate_exclusion_removed", "firewalls", STATUS, "no physical shear, vorticity or acceleration estimate,", ""),
    ("bass_exclusion_removed", "firewalls", STATUS, "no native BASS result", "a native BASS result"),
)
DOCUMENT_CHECKERS = {"joint": _check_joint_document, "firewalls": _check_firewalls_document}


@pytest.mark.parametrize("case", DOCUMENT_MUTATIONS, ids=[case[0] for case in DOCUMENT_MUTATIONS])
def test_documentary_guards_reject_semantic_mutations(case: tuple[str, ...]) -> None:
    _, checker, heading, target, replacement = case
    original = PACK.read_text(encoding="utf-8")
    DOCUMENT_CHECKERS[checker](original)
    changed = _mutate_section_once(original, heading, target, replacement)
    with pytest.raises(AssertionError):
        DOCUMENT_CHECKERS[checker](changed)


@pytest.mark.parametrize("case", (DOCUMENT_MUTATIONS[0], DOCUMENT_MUTATIONS[-1]), ids=("shared_data", "bass"))
def test_historical_quote_cannot_replace_active_prohibition(case: tuple[str, ...]) -> None:
    _, checker, heading, target, replacement = case
    original = PACK.read_text(encoding="utf-8")
    changed = _mutate_section_once(original, heading, target, replacement)
    quote = "\n".join("> " + line for line in _section(original, heading).splitlines())
    marker = f"## {heading}\n"
    changed = changed.replace(marker, marker + quote + "\n\n", 1)
    assert changed != original
    with pytest.raises(AssertionError):
        DOCUMENT_CHECKERS[checker](changed)
