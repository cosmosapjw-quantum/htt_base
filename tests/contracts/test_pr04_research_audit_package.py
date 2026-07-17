from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import pytest

pytestmark = pytest.mark.xfail(
    reason="PR-120 quarantined the CF4-P0 final report (docs/final_report/main.tex deleted; PDF legacy-only, public_use=false); this builder is red by quarantine design until a post-quarantine report exists.",
    strict=False,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_pr04_research_audit_package.py"


def _load():
    spec = importlib.util.spec_from_file_location("pr04_research_audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pr04_research_audit_package"] = module
    spec.loader.exec_module(module)
    return module


def _payload():
    module = _load()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_pr04_research_audit_package.py",
    )
    return module, payload, entries


def test_builds_and_passes_required_gates():
    _module, payload, entries = _payload()
    assert payload["failed_gates"] == []
    assert all(payload["required_assertions"].values())
    assert len(entries) == payload["archive_entry_count"]


def test_bundles_report_proofs_implementations_gates_and_ledger():
    _module, payload, _entries = _payload()
    g = payload["group_counts"]
    assert payload["required_assertions"]["report_tex_and_pdf_included"]
    assert payload["required_assertions"]["pr04_proof_record_included"]
    assert g.get("theorem_implementation", 0) >= 9
    assert g.get("gate_test", 0) >= 6
    assert g.get("measurement_report", 0) >= 8
    assert g.get("pr_delta", 0) >= 7
    assert payload["required_assertions"]["twelve_figures"]


def test_manifest_keeps_blocks():
    _module, payload, _entries = _payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["family_identification"] is False
    assert payload["native_solver_result"] is False
    gates = payload["science_promotion_gates"]
    assert gates["family_identification_or_geometry_detection"] == "blocked"
    assert gates["global_tilt_from_cf4_distances"] == "blocked"


def test_no_raw_datasets_bundled():
    _module, payload, _entries = _payload()
    for r in payload["archive_entries"]:
        assert Path(r["archive_path"]).suffix.lower() not in {".npz", ".fits", ".csv", ".npy"}


def test_zip_deterministic_and_on_disk_current():
    module, payload, entries = _payload()
    assert module._build_zip_bytes(REPO_ROOT, payload, entries) == module._build_zip_bytes(REPO_ROOT, payload, entries)
    assert module.main(["--check"]) == 0
