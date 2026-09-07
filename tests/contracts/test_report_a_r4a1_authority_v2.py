from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "codex_handoff" / "htt_tensorized_report_first_20260903"
CONTRACT = BASE / "R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT_V2.yaml"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def bib_keys(text: str) -> set[str]:
    return set(re.findall(r"(?m)^@[A-Za-z]+\{([^,]+),", text))


def report_citation_keys(text: str) -> set[str]:
    return set(re.findall(r"\[@([A-Z0-9_]+)\]", text))


def claim(ledger: dict, claim_id: str) -> dict:
    return next(item for item in ledger["claims"] if item["id"] == claim_id)


def test_r4a1n_v2_runs_on_the_declared_supported_python_runtime():
    contract = load_yaml(CONTRACT)
    runtime = contract["runtime_contract"]
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:2] == (runtime["major"], runtime["minor"]) == (3, 12)


def test_r4a1n_v2_binds_every_declared_git_blob():
    contract = load_yaml(CONTRACT)
    for name, source in contract["source_blobs"].items():
        path = ROOT / source["path"]
        assert path.is_file(), name
        assert git_blob_sha1(path) == source["git_blob_sha1"], name


def test_r4a1n_v2_recomputes_the_canonical_claim_id_hash():
    contract = load_yaml(CONTRACT)
    ledger_path = ROOT / contract["source_blobs"]["claim_ledger"]["path"]
    ledger = load_yaml(ledger_path)
    ids = [item["id"] for item in ledger["claims"]]
    expected = contract["canonical_claim_id_contract"]
    assert len(ids) == len(set(ids)) == expected["claim_count"] == 30
    payload = "\n".join(sorted(ids)) + "\n"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert digest == expected["expected_sha256"]
    assert ledger["coverage"]["canonical_sorted_id_sha256"] is None
    assert ledger["coverage"]["canonical_sorted_id_sha256_status"] == (
        "PENDING_SUPPORTED_RUNTIME_REPLAY"
    )


def test_r4a1n_v2_cross_surface_and_notation_contract():
    contract = load_yaml(CONTRACT)
    paths = {
        name: ROOT / source["path"]
        for name, source in contract["source_blobs"].items()
    }
    ledger = load_yaml(paths["claim_ledger"])
    matrix = load_yaml(paths["citation_matrix"])
    registry = load_yaml(paths["notation_registry_v3"])
    overlay = load_yaml(paths["t9_authority_overlay"])
    report = paths["flattened_manuscript"].read_text(encoding="utf-8")
    appendix = paths["convention_domain_appendix"].read_text(encoding="utf-8")
    bibliography = paths["formal_bibliography"].read_text(encoding="utf-8")

    ids = [item["id"] for item in ledger["claims"]]
    citation_ids = list(matrix["claim_citations"])
    assert len(ids) == len(set(ids)) == 30
    assert len(citation_ids) == len(set(citation_ids)) == 30
    assert set(citation_ids) == set(ids)
    assert bib_keys(bibliography) == set(matrix["source_registry"])
    assert report_citation_keys(report) == set(matrix["source_registry"])
    for claim_id in ids:
        assert claim_id in report

    assert registry["schema"] == contract["notation_and_domain_contract"][
        "canonical_registry_schema"
    ]
    row_assumptions = registry["statistical_notation"]["exchangeable_row_rank"][
        "assumptions"
    ]
    group_assumptions = registry["statistical_notation"][
        "randomization_group_orbit"
    ]["assumptions"]
    assert row_assumptions == claim(ledger, "RA-STAT-001")["assumptions"]
    assert group_assumptions == claim(ledger, "RA-STAT-004")["assumptions"]
    assert contract["notation_and_domain_contract"][
        "forbidden_legacy_premise"
    ] not in REGISTRY_TEXT_WITHOUT_FIREWALL_VALUE(registry)

    update = overlay["claim_authority_updates"]["RA-REP-002"]
    assert update["add_authority_label"] == registry["authority_labels"]["canonical"]
    assert overlay["base_ledger"]["claim_count"] == 30

    for needle in (
        "u^a u_a=-1",
        "p^a p_a=0",
        "E_\\gamma=-c\\,p_a u^a>0",
        "u_a\\beta_{\\rm obs}^a=0",
        "\\lambda_{\\rm reg}>0",
    ):
        assert needle in appendix


def REGISTRY_TEXT_WITHOUT_FIREWALL_VALUE(registry: dict) -> str:
    clone = dict(registry)
    statistical = dict(clone["statistical_notation"])
    firewall = dict(statistical["exactness_firewall"])
    firewall.pop("forbidden_legacy_premise", None)
    statistical["exactness_firewall"] = firewall
    clone["statistical_notation"] = statistical
    return yaml.safe_dump(clone, sort_keys=True)


def test_r4a1n_v2_preserves_the_closed_claim_firewall():
    contract = load_yaml(CONTRACT)
    paths = {
        name: ROOT / source["path"]
        for name, source in contract["source_blobs"].items()
    }
    ledger = load_yaml(paths["claim_ledger"])
    appendix = paths["convention_domain_appendix"].read_text(encoding="utf-8")

    assert ledger["observational_data_used"] is False
    assert ledger["corrected_planck_tensor_rank"] is None
    assert ledger["merge_authorized"] is False
    assert ledger["coverage"]["observational_claim_count"] == 0
    assert ledger["coverage"]["finite_healpix_no_go_claim_count"] == 0
    assert ledger["coverage"]["native_bass_claim_count"] == 0
    assert "corrected tensorised Planck rank remains absent" in appendix
    assert "finite-HEALPix containment remains rank-unresolved" in appendix
    assert "native BASS solver claims remain outside the report" in appendix
