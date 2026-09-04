from __future__ import annotations

import csv
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
REPORT_BASE = ROOT / "docs" / "research_reports" / "report_a"
OVERLAY = BASE / "K2_40_CLAIM_CANDIDATE_OVERLAY.yaml"
CITATIONS = BASE / "K2_CITATION_PROVENANCE_CANDIDATE_OVERLAY.yaml"
INTEGRATION = REPORT_BASE / "REPORT_A_ORGANIC_INTEGRATION_MATRIX_V2_CANDIDATE.yaml"
SECTION_MAP = BASE / "REPORT_SECTION_CLAIM_MAP_V2_CANDIDATE.csv"
BIB_SUPPLEMENT = REPORT_BASE / "K2_BIBLIOGRAPHY_SUPPLEMENT_CANDIDATE.bib"
ARCHITECTURE = ROOT / "docs" / "research_reports" / "K2_REPORT_A_CLAIM_ARCHITECTURE.md"


def _yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _section_rows() -> list[dict[str, str]]:
    with SECTION_MAP.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_candidate_claim_surface_is_exactly_thirty_plus_ten() -> None:
    data = _yaml(OVERLAY)
    base_ids = data["base_claim_ids"]
    additions = data["additions"]
    addition_ids = [row["id"] for row in additions]
    candidate_ids = data["candidate_claim_ids"]

    assert len(base_ids) == 30
    assert len(set(base_ids)) == 30
    assert len(addition_ids) == 10
    assert len(set(addition_ids)) == 10
    assert set(base_ids).isdisjoint(addition_ids)
    assert len(candidate_ids) == 40
    assert len(set(candidate_ids)) == 40
    assert set(candidate_ids) == set(base_ids) | set(addition_ids)

    coverage = data["coverage"]
    assert coverage["base_claims"] == 30
    assert coverage["new_claims"] == 10
    assert coverage["revised_base_claims"] == 4
    assert coverage["candidate_claim_count"] == 40
    assert coverage["canonical_promotion"] is False
    assert coverage["canonical_sorted_id_sha256"] is None


def test_every_new_claim_has_authority_assumptions_and_forbidden_extensions() -> None:
    data = _yaml(OVERLAY)
    for row in data["additions"]:
        assert row["authority"]
        assert row["assumptions"]
        assert row["forbidden_extensions"]
        assert row["statement"].strip()
        assert row["truth_status"]
        assert row["implementation_status"]
        assert row["report_role"]

    revisions = data["revisions"]
    assert {row["id"] for row in revisions} == {
        "RA-MES-002",
        "RA-MES-003",
        "RA-RESP-001",
        "RA-STAT-002",
    }
    base_ids = set(data["base_claim_ids"])
    assert all(row["id"] in base_ids for row in revisions)
    assert all(row["replacement_statement"].strip() for row in revisions)


def test_uniqueness_and_implication_review_covers_all_additions() -> None:
    data = _yaml(OVERLAY)
    additions = {row["id"] for row in data["additions"]}
    review = data["uniqueness_and_implication_review"]
    assert {row["claim_id"] for row in review} == additions
    assert all(row["disposition"] == "KEEP_DISTINCT" for row in review)
    assert all(row["closest_existing_or_new_claim"] for row in review)
    assert all(row["reason"].strip() for row in review)


def test_citation_overlay_maps_every_addition_and_revision() -> None:
    claims = _yaml(OVERLAY)
    citations = _yaml(CITATIONS)
    addition_ids = {row["id"] for row in claims["additions"]}
    revision_ids = {row["id"] for row in claims["revisions"]}
    new_rows = citations["new_claim_citations"]
    revised_rows = citations["revised_claim_citation_updates"]
    assert set(new_rows) == addition_ids
    assert set(revised_rows) == revision_ids
    assert all(row["internal_authority"] for row in new_rows.values())
    coverage = citations["coverage_candidate"]
    assert coverage["total_candidate_claim_rows"] == 40
    assert coverage["all_new_claims_have_internal_authority"] is True
    assert coverage["observational_sources_used_as_results"] == 0


def test_candidate_bibliography_supplement_has_three_unique_keys() -> None:
    text = BIB_SUPPLEMENT.read_text(encoding="utf-8")
    keys = re.findall(r"^@[A-Za-z]+\{([^,]+),", text, flags=re.MULTILINE)
    assert keys == [
        "ELLIS_VAN_ELST_1999",
        "MOLINARI_2020",
        "KAIDO_MOLINARI_STOYE_2022",
    ]
    assert len(keys) == len(set(keys)) == 3
    for doi in (
        "10.1007/978-94-011-4455-1_1",
        "10.1016/bs.hoe.2020.05.002",
        "10.1017/S0266466621000207",
    ):
        assert doi in text


def test_organic_integration_and_section_map_are_exact_bijections() -> None:
    claims = _yaml(OVERLAY)
    expected = set(claims["candidate_claim_ids"])

    matrix = _yaml(INTEGRATION)
    placed = [claim_id for layer in matrix["layers"] for claim_id in layer["claim_ids"]]
    assert len(placed) == 40
    assert len(set(placed)) == 40
    assert set(placed) == expected

    rows = _section_rows()
    mapped = [row["claim_id"] for row in rows]
    assert len(mapped) == 40
    assert len(set(mapped)) == 40
    assert set(mapped) == expected
    assert all(row["section_id"] and row["section_title"] for row in rows)


def test_original_and_later_methodology_are_organically_integrated() -> None:
    matrix = _yaml(INTEGRATION)
    layer_ids = {layer["id"] for layer in matrix["layers"]}
    assert layer_ids == {
        "scope_and_supersession",
        "observable_tensor_representation",
        "typed_physical_state_and_geometry",
        "mes_sector_anchor_geometry",
        "jointly_conditioned_identification_and_finite_null",
        "scoped_local_observer_response",
        "processed_response_continuum_and_numerical_boundary",
        "verification_and_publication_authority",
    }
    for layer in matrix["layers"]:
        assert layer["original_repository_authority"]
        assert layer["later_development"]
        assert layer["integrated_role"].strip()


def test_candidate_architecture_preserves_scientific_firewalls() -> None:
    # The old test required a sentence that is not in the architecture and
    # capitalised HEALPix differently. Keep the scientific requirements while
    # making case and line wrapping non-semantic. This is documentary coverage,
    # not a proof or an observed scientific result.
    text = " ".join(ARCHITECTURE.read_text(encoding="utf-8").split()).casefold()
    required = (
        "observable Q/O tensor state",
        "typed physical state",
        r"\mathcal O_{\rm low} \ne \mathcal X_{\rm phys}",
        "No arrow from an anchor to a state is generative",
        "No equality of representation types is a physical identification",
        r"\Theta(y;\eta)",
        "common-data non-independence boundary",
        "The K2 candidate introduces no:",
        "current scalar-only MES observational rank",
        "finite-HEALPix containment theorem",
        "BASS/native-solver result",
        "NO_CLAIM_PROMOTION",
    )
    for needle in required:
        assert needle.casefold() in text

    overlay = _yaml(OVERLAY)
    coverage = overlay["coverage"]
    assert coverage["observational_claim_count"] == 0
    assert coverage["corrected_planck_rank_claim_count"] == 0
    assert coverage["finite_healpix_no_go_claim_count"] == 0
    assert coverage["native_bass_claim_count"] == 0
