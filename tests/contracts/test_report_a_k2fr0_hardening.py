"""Regression contract for K2FR0; source-first, not an execution receipt."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys

import pytest
import yaml

from scripts import compile_report_a_k2fr0_authority as compiler

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    return tuple(yaml.safe_load((ROOT / compiler.INPUT_PATHS[key]).read_text(encoding="utf-8"))
                 for key in ("base_claim_ledger", "claim_overlay"))


def mirror(destination):
    for relative in [*compiler.INPUT_PATHS.values(), compiler.LEGACY_PATH]:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return destination


def test_preserve_base_authority_memory_and_input_values():
    base, overlay = inputs()
    original = copy.deepcopy((base, overlay))
    result = compiler.compile_claim_ledger(base, overlay)
    for key in compiler.PRESERVE_KEYS:
        assert result[key] == base[key]
    assert result["supersedes"]["prior_history"] == base["supersedes"]
    assert result["registered_survivor_source"]["curated_report_projection_claims"] == 30
    assert result["kinematical_reintegration"]["candidate_claim_count"] == 40
    assert (base, overlay) == original
    assert result["canonical_promotion"] is False


def test_normalisation_does_not_inherit_donor_execution():
    base, overlay = inputs()
    result = compiler.compile_claim_ledger(base, overlay)
    rows = {row["id"]: row for row in result["claims"]}
    assert len(rows) == 40
    for row in rows.values():
        for field in ("truth_status", "implementation_status", "report_role"):
            assert row[field] in base["vocabulary"][field]
    kin = rows["RA-KIN-001"]
    assert kin["truth_status"] == "ESTABLISHED"
    assert kin["implementation_status"] == "SOURCE_IMPLEMENTED"
    assert kin["source_lineage"]["kind"] == "GIT_DIVERGED_DONOR"
    assert kin["source_lineage"]["execution_inherited"] is False
    assert kin["status_translation"]["original_truth_status"] == "SOURCE_DEFINED_EXACT"
    for key in ("RA-ID-001", "RA-ID-002"):
        assert rows[key]["implementation_status"] == "NOT_APPLICABLE"
        assert rows[key]["implementation_support"]["implementation_claimed"] is False


@pytest.mark.parametrize("field", ["truth_status", "implementation_status", "report_role"])
def test_unknown_vocabulary_is_rejected(field):
    base, overlay = inputs()
    base["claims"][0][field] = "INVENTED_STATUS"
    with pytest.raises(compiler.CompilationError, match="vocabulary"):
        compiler.compile_claim_ledger(base, overlay)


def test_conditional_coverage_is_recomputed_not_inherited():
    base, overlay = inputs()
    row = next(row for row in base["claims"] if row["id"] == "RA-MES-002")
    for key in compiler.SCIENTIFIC_SCOPE_FIELDS:
        row.pop(key, None)
    base["coverage"]["all_conditional_claims_have_assumptions_or_boundary"] = True
    result = compiler.compile_claim_ledger(base, overlay)
    assert result["coverage"]["all_conditional_claims_have_assumptions_or_boundary"] is False
    assert "RA-MES-002" in result["structural_findings"]["conditional_scope_not_explicit"]


def test_numerical_execution_grade_is_recomputed_not_inherited():
    base, overlay = inputs()
    row = next(row for row in base["claims"] if row["id"] == "RA-PROC-004")
    row["implementation_status"] = "SOURCE_IMPLEMENTED"
    result = compiler.compile_claim_ledger(base, overlay)
    assert result["coverage"]["all_numerical_claims_have_execution_grade"] is False
    assert "RA-PROC-004" in result["structural_findings"]["numerical_execution_grade_missing"]


def test_unbound_materialisation_is_refused(tmp_path):
    out = tmp_path / "out"
    with pytest.raises(compiler.CompilationError, match="strict"):
        compiler.compile_authority_bundle(repository_root=ROOT, output_root=out,
                                          enforce_registered_input_blobs=False)
    assert not out.exists()


def test_registered_input_mutation_is_rejected_before_publication(tmp_path):
    root = mirror(tmp_path / "repo")
    path = root / compiler.INPUT_PATHS["claim_overlay"]
    path.write_bytes(path.read_bytes() + b"# input drift\n")
    with pytest.raises(compiler.CompilationError, match="Git blob mismatch"):
        compiler.compile_authority_bundle(repository_root=root, output_root=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_symlinked_input_ancestor_is_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "docs").symlink_to(ROOT / "docs", target_is_directory=True)
    with pytest.raises(compiler.CompilationError, match="symlink"):
        compiler.compile_authority_bundle(repository_root=root, output_root=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_existing_receipt_and_destination_are_never_overwritten(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    receipt = out / compiler.OUTPUT_NAMES["receipt"]
    receipt.write_bytes(b"previous receipt\n")
    with pytest.raises(compiler.CompilationError, match="existing"):
        compiler.compile_authority_bundle(repository_root=ROOT, output_root=out)
    assert list(out.iterdir()) == [receipt]
    assert receipt.read_bytes() == b"previous receipt\n"


def test_mid_write_failure_leaves_no_published_bundle(tmp_path, monkeypatch):
    original = compiler._write_payload
    calls = []
    def fail_second(path, payload):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("injected write failure")
        return original(path, payload)
    monkeypatch.setattr(compiler, "_write_payload", fail_second)
    with pytest.raises(compiler.CompilationError, match="injected write failure"):
        compiler.compile_authority_bundle(repository_root=ROOT, output_root=tmp_path / "out")
    assert len(calls) == 2
    assert list(tmp_path.iterdir()) == []


def test_corrupt_staged_write_is_detected_before_publication(tmp_path, monkeypatch):
    original = compiler._write_payload
    def corrupt(path, payload):
        return original(path, payload + b"corruption")
    monkeypatch.setattr(compiler, "_write_payload", corrupt)
    with pytest.raises(compiler.CompilationError, match="staged"):
        compiler.compile_authority_bundle(repository_root=ROOT, output_root=tmp_path / "out")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform != "linux", reason="production publisher is Linux RENAME_NOREPLACE")
def test_destination_race_does_not_replace_even_an_empty_directory(tmp_path, monkeypatch):
    original = compiler._publish_noreplace
    def race(stage, destination):
        destination.mkdir()
        return original(stage, destination)
    monkeypatch.setattr(compiler, "_publish_noreplace", race)
    with pytest.raises(compiler.CompilationError):
        compiler.compile_authority_bundle(repository_root=ROOT, output_root=tmp_path / "out")
    assert (tmp_path / "out").is_dir()
    assert list((tmp_path / "out").iterdir()) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out"]


@pytest.mark.skipif(sys.platform != "linux", reason="production publisher is Linux RENAME_NOREPLACE")
def test_strict_six_file_bundle_is_deterministic_and_preserves_all_bijections(tmp_path):
    receipts = []
    for name in ("first", "second"):
        receipts.append(compiler.compile_authority_bundle(repository_root=ROOT, output_root=tmp_path / name))
    first, second = (tmp_path / name for name in ("first", "second"))
    assert receipts[0] == receipts[1]
    assert {p.name for p in first.iterdir()} == set(compiler.OUTPUT_NAMES.values())
    assert all((first / name).read_bytes() == (second / name).read_bytes()
               for name in compiler.OUTPUT_NAMES.values())
    receipt = json.loads((first / compiler.OUTPUT_NAMES["receipt"]).read_text())
    assert receipt["source_binding"]["enforced"] is True
    assert receipt["source_binding"]["all_registered_input_blobs_match"] is True
    assert receipt["claim_count"] == receipt["citation_rows"] == receipt["section_rows"] == receipt["integration_rows"] == 40
    assert receipt["bibliography_keys"] == 20
    assert receipt["claim_promotion"] is False
    assert receipt["scientific_verification_performed"] is False
    assert receipt["compiled_bundle_is_canonical"] is False
    assert receipt["publication_authority"] is False
    for key, digest in receipt["output_sha256"].items():
        assert compiler.sha256((first / compiler.OUTPUT_NAMES[key]).read_bytes()) == digest
    ledger = yaml.safe_load((first / compiler.OUTPUT_NAMES["claim_ledger"]).read_text())
    citations = yaml.safe_load((first / compiler.OUTPUT_NAMES["citation_matrix"]).read_text())
    assert ledger["coverage"]["canonical_sorted_id_sha256"] == receipt["canonical_sorted_id_sha256"]
    assert citations["source_registry"]["MOLINARI_2020"]["role"] == "AUTHORITATIVE_SURVEY_PARTIAL_IDENTIFICATION_CONTEXT"
    assert len(citations["claim_citations"]) == 40
