from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
)
CONTRACT = BASE / "R4A1_SUPPORTED_RUNTIME_AUTHORITY_CONTRACT.yaml"


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


def test_r4a1_runs_on_the_declared_supported_python_runtime():
    contract = load_yaml(CONTRACT)
    runtime = contract["runtime_contract"]
    assert sys.implementation.name == "cpython"
    assert sys.version_info[:2] == (runtime["major"], runtime["minor"]) == (3, 12)


def test_r4a1_binds_the_exact_declared_git_blobs():
    contract = load_yaml(CONTRACT)
    for name, source in contract["source_blobs"].items():
        path = ROOT / source["path"]
        assert path.is_file(), name
        assert git_blob_sha1(path) == source["git_blob_sha1"], name


def test_r4a1_recomputes_the_canonical_claim_id_hash_from_the_ledger():
    contract = load_yaml(CONTRACT)
    ledger_path = ROOT / contract["source_blobs"]["claim_ledger"]["path"]
    ledger = load_yaml(ledger_path)
    ids = [claim["id"] for claim in ledger["claims"]]
    expected = contract["canonical_claim_id_contract"]
    assert len(ids) == len(set(ids)) == expected["claim_count"] == 30
    payload = "\n".join(sorted(ids)) + "\n"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert digest == expected["expected_sha256"]
    assert ledger["coverage"]["canonical_sorted_id_sha256"] is None
    assert ledger["coverage"]["canonical_sorted_id_sha256_status"] == (
        "PENDING_SUPPORTED_RUNTIME_REPLAY"
    )


def test_r4a1_cross_surface_claim_citation_and_bibliography_contract():
    contract = load_yaml(CONTRACT)
    paths = {
        name: ROOT / source["path"]
        for name, source in contract["source_blobs"].items()
    }
    ledger = load_yaml(paths["claim_ledger"])
    matrix = load_yaml(paths["citation_matrix"])
    report = paths["flattened_manuscript"].read_text(encoding="utf-8")
    bibliography = paths["formal_bibliography"].read_text(encoding="utf-8")

    claim_ids = [claim["id"] for claim in ledger["claims"]]
    citation_claim_ids = list(matrix["claim_citations"])
    registered_sources = set(matrix["source_registry"])
    rendered_bib_keys = bib_keys(bibliography)
    used_report_keys = report_citation_keys(report)

    assert len(claim_ids) == len(set(claim_ids)) == 30
    assert len(citation_claim_ids) == len(set(citation_claim_ids)) == 30
    assert set(citation_claim_ids) == set(claim_ids)
    assert rendered_bib_keys == registered_sources
    assert used_report_keys == registered_sources
    for claim_id in claim_ids:
        assert claim_id in report

    assert matrix["formal_bibliography"] == (
        "docs/research_reports/HTT_REPORT_A_REFERENCES.bib"
    )
    assert "# Appendix D. References and declared roles" not in report
    assert "No manual reference list is a competing authority." in report


def test_r4a1_preserves_the_closed_claim_firewall():
    contract = load_yaml(CONTRACT)
    paths = {
        name: ROOT / source["path"]
        for name, source in contract["source_blobs"].items()
    }
    ledger = load_yaml(paths["claim_ledger"])
    report = paths["flattened_manuscript"].read_text(encoding="utf-8")

    assert ledger["observational_data_used"] is False
    assert ledger["corrected_planck_tensor_rank"] is None
    assert ledger["merge_authorized"] is False
    assert ledger["coverage"]["observational_claim_count"] == 0
    assert ledger["coverage"]["finite_healpix_no_go_claim_count"] == 0
    assert ledger["coverage"]["native_bass_claim_count"] == 0

    assert "CURRENT_CORRECTED_TENSORIZED_PLANCK_RANK = NONE" in report
    assert "PLANCK_OR_FFP10_EXECUTION = DEFERRED_BY_OWNER" in report
    assert "FINITE_HEALPIX_CONTAINMENT = RANK_UNRESOLVED" in report
    assert "no finite-HEALPix no-go theorem is claimed" in report
    assert "no native BASS solver" in report
    assert paths["provenance_appendix"].is_file()
