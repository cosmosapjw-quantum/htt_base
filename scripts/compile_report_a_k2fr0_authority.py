#!/usr/bin/env python3
"""Strict K2FR0 successor: compile source candidates, never promote science.

The original K2F compiler is retained as byte-pinned transformation history.
This entrypoint replaces its materialisation path. Inputs are parsed from the
same byte snapshot that is hashed. Linux RENAME_NOREPLACE publishes a complete
six-file directory without replacing even an empty destination. Publication
atomicity is a local-filesystem visibility guarantee, not a crash-durability
or hostile-filesystem guarantee. No observations or CAS proofs are run here.
"""
from __future__ import annotations

import argparse
import copy
import csv
import ctypes
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile
from typing import Any, Mapping

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import compile_report_a_k2f_authority as legacy

CompilationError = legacy.CompilationError
INPUT_PATHS = dict(legacy.INPUT_PATHS)
EXPECTED_INPUT_GIT_BLOBS = dict(legacy.EXPECTED_INPUT_GIT_BLOBS)
OUTPUT_NAMES = dict(legacy.OUTPUT_NAMES)
LEGACY_PATH = Path("scripts/compile_report_a_k2f_authority.py")
LEGACY_BLOB = "50aca195e6a5a433ee8c4370a38ee52b35e2f0e2"
PRESERVE_KEYS = (
    "canonical_notation_registry", "registered_survivor_source",
    "active_repairs", "vocabulary",
)
SCIENTIFIC_SCOPE_FIELDS = (
    "assumptions", "domain_binding", "scientific_boundary", "mathematical_domain",
)
SOURCE_CONTRACT_IDS = {
    "RA-KIN-001", "RA-KIN-003", "RA-KFUNC-001", "RA-MESA-001", "RA-MESA-002",
}
DONOR_IDS = {
    "RA-KIN-001", "RA-KIN-002", "RA-KIN-003", "RA-GEO-001", "RA-KFUNC-001", "RA-MESA-003",
}
ABSTRACT_THEOREM_IDS = {"RA-ID-001", "RA-ID-002"}
ZERO_COUNT_KEYS = (
    "observational_claim_count", "corrected_planck_rank_claim_count",
    "finite_healpix_no_go_claim_count", "bianchi_family_claim_count", "native_bass_claim_count",
)


class UniqueSafeLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than accepting last-key-wins authority."""


def _unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    out = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in out:
            raise CompilationError(f"duplicate YAML key {key!r}")
        out[key] = loader.construct_object(value_node, deep=deep)
    return out


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mapping(data: bytes, label: str) -> dict[str, Any]:
    value = yaml.load(data.decode("utf-8"), Loader=UniqueSafeLoader)
    if not isinstance(value, dict):
        raise CompilationError(f"{label} must be a YAML mapping")
    return value


def _check_path_components(path: Path) -> None:
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise CompilationError(f"symlinked path component: {component}")


def _snapshot(root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    payloads, identities = {}, {}
    for key, relative in {**INPUT_PATHS, "legacy_helper": LEGACY_PATH}.items():
        path = root / relative
        _check_path_components(path)
        if not path.is_file():
            raise CompilationError(f"registered source is absent: {relative}")
        data = path.read_bytes()
        digest = legacy._git_blob_sha1(data)
        expected = LEGACY_BLOB if key == "legacy_helper" else EXPECTED_INPUT_GIT_BLOBS[key]
        if digest != expected:
            raise CompilationError(f"Git blob mismatch for {relative}: expected {expected}, got {digest}")
        payloads[key], identities[key] = data, digest
    return payloads, identities


def _normalise_addition(source: Mapping[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(dict(source))
    claim_id = row.get("id")
    original = {
        "original_truth_status": row.get("truth_status"),
        "original_implementation_status": row.get("implementation_status"),
    }
    if row.get("truth_status") == "SOURCE_DEFINED_EXACT":
        if claim_id not in SOURCE_CONTRACT_IDS:
            raise CompilationError(f"unregistered vocabulary translation for {claim_id}")
        row["truth_status"] = "ESTABLISHED"
        row["authority_kind"] = "SOURCE_CONTRACT_NOT_PHYSICAL_MEASUREMENT"
    if row.get("implementation_status") == "SOURCE_IMPLEMENTED_IN_DIVERGED_DONOR":
        if claim_id not in DONOR_IDS:
            raise CompilationError(f"unregistered donor vocabulary translation for {claim_id}")
        row["implementation_status"] = "SOURCE_IMPLEMENTED"
        row["source_lineage"] = {
            "kind": "GIT_DIVERGED_DONOR", "donor_pr": 367,
            "donor_head": "6bafca66285ef071081453313bb7d2d6b261599c",
            "execution_inherited": False,
        }
    if row.get("implementation_status") == "SOURCE_SUPPORTED":
        if claim_id not in ABSTRACT_THEOREM_IDS:
            raise CompilationError(f"unregistered support vocabulary translation for {claim_id}")
        row["implementation_status"] = "NOT_APPLICABLE"
        row["implementation_support"] = {
            "kind": "ADJACENT_DONOR_SET_MECHANICS", "implementation_claimed": False,
            "note": "Source support is not an implementation of the full tensor response or identified set.",
        }
    if original != {
        "original_truth_status": row.get("truth_status"),
        "original_implementation_status": row.get("implementation_status"),
    }:
        row["status_translation"] = {**original, "policy": "K2FR0_EXPLICIT_ENUM_NORMALISATION"}
    return row


def compile_claim_ledger(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve base authority memory; normalise only declared candidate labels."""
    for key in PRESERVE_KEYS:
        if not isinstance(base.get(key), dict):
            raise CompilationError(f"base authority memory missing {key}")
    vocabulary = base["vocabulary"]
    for field in ("truth_status", "implementation_status", "report_role"):
        if not isinstance(vocabulary.get(field), list) or not vocabulary[field]:
            raise CompilationError(f"invalid vocabulary for {field}")
    normal = copy.deepcopy(dict(overlay))
    normal["additions"] = [_normalise_addition(row) for row in overlay["additions"]]
    for row in [*base["claims"], *normal["additions"]]:
        for field in ("truth_status", "implementation_status", "report_role"):
            if row.get(field) not in vocabulary[field]:
                raise CompilationError(f"claim {row.get('id')} has unknown {field} vocabulary: {row.get(field)!r}")
    for source in (base, overlay):
        if source.get("observational_data_used") is not False or source.get("merge_authorized") is not False:
            raise CompilationError("source scope/publication firewall is not explicitly closed")
        if source.get("corrected_planck_tensor_rank") is not None:
            raise CompilationError("corrected Planck result is outside scope")
        for key in ZERO_COUNT_KEYS:
            value = source.get("coverage", {}).get(key, 0)
            if type(value) is not int or value != 0:
                raise CompilationError(f"declared scope firewall {key} is not integer zero")

    draft = legacy.compile_claim_ledger(base, normal)
    rows = draft["claims"]
    missing_scope = [row["id"] for row in rows
                     if row["truth_status"] == "DERIVED_CONDITIONAL"
                     and not any(row.get(key) for key in SCIENTIFIC_SCOPE_FIELDS)]
    missing_grade = [row["id"] for row in rows
                     if row["truth_status"] == "NUMERICALLY_CHECKED"
                     and row["implementation_status"] not in {"IMPLEMENTATION_VERIFIED", "LOCAL_NON_BYTE_EXACT"}]
    source_promoted = [row["id"] for row in rows
                       if row.get("source_lineage", {}).get("kind") == "GIT_DIVERGED_DONOR"
                       and row["implementation_status"] == "IMPLEMENTATION_VERIFIED"]
    coverage = copy.deepcopy(draft["coverage"])
    coverage.update({
        "canonical_sorted_id_sha256_status": "COMPUTED_SOURCE_CANDIDATE_NOT_CANONICAL_PROMOTION",
        "all_claims_have_authority": all(bool(row.get("authority")) for row in rows),
        "all_conditional_claims_have_assumptions_or_boundary": not missing_scope,
        "all_numerical_claims_have_execution_grade": not missing_grade,
        "all_source_only_claims_are_not_labelled_implementation_verified": not source_promoted,
        "scope_count_basis": "Immutable source declarations; no natural-language scientific adjudication is claimed.",
    })
    out = copy.deepcopy(dict(base))
    out.update({
        "schema": "htt.report_a.integrated_claim_evidence_ledger.v5",
        "date": "2026-09-05", "status": "K2FR0_COMPILED_FORTY_CLAIM_SOURCE_CANDIDATE",
        "canonical_promotion": False, "publication_authority": False, "merge_authorized": False,
        "supersedes": {
            "immediate_base": {"path": str(INPUT_PATHS["base_claim_ledger"]),
                               "git_blob_sha1": EXPECTED_INPUT_GIT_BLOBS["base_claim_ledger"]},
            "prior_history": copy.deepcopy(base.get("supersedes", {})),
            "claim_overlay": {"path": str(INPUT_PATHS["claim_overlay"]),
                              "git_blob_sha1": EXPECTED_INPUT_GIT_BLOBS["claim_overlay"]},
        },
        "claims": rows, "coverage": coverage,
        "kinematical_reintegration": {
            "base_claim_count": len(base["claims"]),
            "added_claim_count": len(normal["additions"]),
            "revised_claim_count": len(normal["revisions"]),
            "candidate_claim_count": len(rows),
            "source_bindings": copy.deepcopy(overlay.get("k1r_inputs", {})),
            "execution_inherited": False,
        },
        "structural_findings": {
            "conditional_scope_not_explicit": missing_scope,
            "numerical_execution_grade_missing": missing_grade,
            "source_only_execution_promotions": source_promoted,
            "interpretation": "Findings remain visible; this compiler does not silently invent missing assumptions or certify theorems.",
        },
        "prior_freeze_obligations": copy.deepcopy(base.get("remaining_before_report_freeze", [])),
        "remaining_before_report_freeze": [
            "review materialised source candidates and unresolved structural findings",
            "integrate the forty-claim architecture into the revised manuscript",
            "complete applicable execution, scientific review and publication decisions",
        ],
        "terminal": "K2FR0_FORTY_CLAIM_SOURCE_CANDIDATE_NO_SCIENTIFIC_OR_PUBLICATION_PROMOTION",
    })
    for key in PRESERVE_KEYS:
        if out[key] != base[key]:
            raise CompilationError(f"authority memory was changed: {key}")
    return out


def _write_payload(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _publish_noreplace(stage: Path, destination: Path) -> None:
    if sys.platform != "linux":
        raise CompilationError("atomic no-replace publication requires Linux renameat2")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise CompilationError("renameat2 unavailable; no unsafe rename fallback")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(stage), -100, os.fsencode(destination), 1) != 0:
        number = ctypes.get_errno()
        raise CompilationError(f"atomic no-replace publication refused: {os.strerror(number)}")


def _atomic_publish(destination: Path, files: Mapping[str, bytes]) -> None:
    _check_path_components(destination.parent)
    if os.path.lexists(destination):
        raise CompilationError(f"refusing existing output destination {destination}")
    if not destination.parent.is_dir():
        raise CompilationError("output parent must already exist")
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.k2fr0-", dir=destination.parent))
    try:
        for name, data in files.items():
            if Path(name).name != name:
                raise CompilationError("output names must be plain filenames")
            _write_payload(stage / name, data)
        if {p.name for p in stage.iterdir()} != set(files):
            raise CompilationError("staged file set differs from six-file bundle")
        for name, data in files.items():
            if (stage / name).read_bytes() != data:
                raise CompilationError(f"staged output failed byte readback: {name}")
        _publish_noreplace(stage, destination)
    except Exception as exc:
        if isinstance(exc, CompilationError):
            raise
        raise CompilationError(f"staged publication failed: {exc}") from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def compile_authority_bundle(*, repository_root: Path, output_root: Path,
                             enforce_registered_input_blobs: bool = True) -> dict[str, Any]:
    if enforce_registered_input_blobs is not True:
        raise CompilationError("strict input binding is mandatory; unbound output is refused")
    root = Path(os.path.abspath(repository_root))
    destination = Path(os.path.abspath(output_root))
    _check_path_components(root)
    if os.path.lexists(destination):
        raise CompilationError(f"refusing existing output destination {destination}")
    payloads, identities = _snapshot(root)
    base = _mapping(payloads["base_claim_ledger"], "base claim ledger")
    overlay = _mapping(payloads["claim_overlay"], "claim overlay")
    ledger = compile_claim_ledger(base, overlay)
    claim_ids = [row["id"] for row in ledger["claims"]]
    if len(claim_ids) != 40 or len(set(claim_ids)) != 40:
        raise CompilationError("strict K2FR0 compilation requires forty unique claims")
    citations = legacy._compile_citations(
        _mapping(payloads["base_citation_matrix"], "citation base"),
        _mapping(payloads["citation_overlay"], "citation overlay"), claim_ids)
    molinari = citations["source_registry"].get("MOLINARI_2020")
    if not isinstance(molinari, dict):
        raise CompilationError("Molinari contextual source missing")
    molinari["previous_candidate_role"] = molinari.get("role")
    molinari["role"] = "AUTHORITATIVE_SURVEY_PARTIAL_IDENTIFICATION_CONTEXT"
    citations["citation_role_corrections"] = {
        "MOLINARI_2020": "Author's abstract identifies this chapter as a review, not an original proof of the project-specific construction."
    }
    sections = list(csv.DictReader(io.StringIO(payloads["section_map"].decode("utf-8"))))
    section_ids = [row.get("claim_id") for row in sections]
    if len(section_ids) != 40 or set(section_ids) != set(claim_ids):
        raise CompilationError("section map is not a forty-claim bijection")
    for row in sections:
        row["subsection_id"] = "S04.4" if row["claim_id"] == "RA-KFUNC-001" else ""
        row["subsection_title"] = "Physical tensor functionals and orbit morphology" if row["subsection_id"] else ""
    integration = legacy._compile_integration(
        _mapping(payloads["integration_matrix"], "integration matrix"), claim_ids)
    integration["physical_functional_subsection"] = {
        "claim_id": "RA-KFUNC-001", "subsection_id": "S04.4",
        "title": "Physical tensor functionals and orbit morphology", "manuscript_materialised": False,
    }
    bibliography = legacy.merge_bibliographies(payloads["base_bibliography"].decode("utf-8"),
                                              payloads["bibliography_supplement"].decode("utf-8"))
    try:
        from pybtex.database import parse_string
        parsed_bibliography = parse_string(bibliography, "bibtex")
    except Exception as exc:
        raise CompilationError(f"full BibTeX parser failed: {exc}") from exc
    parsed_keys = list(parsed_bibliography.entries)
    if len(parsed_keys) != 20 or set(parsed_keys) != set(citations["source_registry"]):
        raise CompilationError("twenty-entry parsed bibliography/source-registry mismatch")
    for key, entry in parsed_bibliography.entries.items():
        if not entry.fields.get("title") or not entry.fields.get("year"):
            raise CompilationError(f"bibliography entry {key} lacks title or year")
    objects = {"claim_ledger": ledger, "citation_matrix": citations, "integration_matrix": integration}
    rendered = {key: yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode("utf-8")
                for key, value in objects.items()}
    rendered["section_map"] = legacy._render_section_rows(sections).encode("utf-8")
    rendered["bibliography"] = bibliography.encode("utf-8")
    receipt = {
        "schema": "htt.report_a.k2fr0.compilation_receipt.v1", "date": "2026-09-05",
        "repository": "cosmosapjw-quantum/htt_base", "report_pr": 449,
        "source_binding": {"enforced": True, "all_registered_input_blobs_match": True,
                           "parser_uses_verified_byte_snapshot": True, "input_git_blobs": identities},
        "compiler_source_sha256": sha256(Path(__file__).read_bytes()),
        "output_sha256": {key: sha256(data) for key, data in rendered.items()},
        "canonical_sorted_id_sha256": ledger["coverage"]["canonical_sorted_id_sha256"],
        "claim_count": 40, "citation_rows": len(citations["claim_citations"]),
        "section_rows": len(sections),
        "integration_rows": sum(len(layer["claim_ids"]) for layer in integration["layers"]),
        "bibliography_keys": len(parsed_keys),
        "authority_memory_preserved": {key: ledger[key] == base[key] for key in PRESERVE_KEYS},
        "structural_findings": ledger["structural_findings"],
        "runtime": {"implementation": platform.python_implementation(), "python": platform.python_version(),
                    "pyyaml": yaml.__version__, "pybtex": importlib.metadata.version("pybtex"),
                    "matches_cpython312": platform.python_implementation() == "CPython" and sys.version_info[:2] == (3, 12)},
        "observational_data_used": False, "claim_promotion": False,
        "compiled_bundle_is_canonical": False, "scientific_verification_performed": False,
        "publication_authority": False, "merge_authorized": False,
        "terminal": "K2FR0_STRICT_SOURCE_CANDIDATE_MATERIALISED_NO_SCIENTIFIC_OR_PUBLICATION_PROMOTION",
    }
    files = {OUTPUT_NAMES[key]: data for key, data in rendered.items()}
    files[OUTPUT_NAMES["receipt"]] = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(files) != 6:
        raise CompilationError("expected one complete six-file bundle")
    _atomic_publish(destination, files)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if platform.python_implementation() != "CPython" or sys.version_info[:2] != (3, 12):
            raise CompilationError("production CLI requires CPython 3.12; library execution reports its own runtime")
        result = compile_authority_bundle(repository_root=args.repository_root, output_root=args.output_root)
    except (CompilationError, OSError, ValueError, yaml.YAMLError) as exc:
        print(json.dumps({"terminal": "K2FR0_MATERIALISATION_FAILED", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
