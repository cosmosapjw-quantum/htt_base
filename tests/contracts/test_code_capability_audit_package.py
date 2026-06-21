from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_code_capability_audit_package.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("code_capability_audit_package", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["code_capability_audit_package"] = module
    spec.loader.exec_module(module)
    return module


def _payload():
    module = _load_module()
    payload, entries = module.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_code_capability_audit_package.py",
    )
    return module, payload, entries


def test_package_builds_and_passes_required_gates():
    _module, payload, entries = _payload()
    assert payload["failed_gates"] == []
    assert all(payload["required_assertions"].values())
    assert len(entries) == payload["archive_entry_count"]
    # Broad disclosure: hundreds of source files, not a token sample.
    assert payload["archive_entry_count"] > 500


def test_includes_broad_source_and_legacy_and_rust():
    _module, payload, _entries = _payload()
    counts = payload["group_counts"]
    assert counts.get("library_source", 0) > 300
    assert counts.get("rust_solver_source", 0) > 100
    assert counts.get("science_driver", 0) > 20
    assert counts.get("legacy_tsc", 0) > 0
    assert counts.get("data_pipeline", 0) > 0
    assert counts.get("execution_stack", 0) > 0


def test_excludes_tests_raw_data_and_gate_clis():
    module, payload, _entries = _payload()
    paths = [r["archive_path"] for r in payload["archive_entries"]]
    assert payload["required_assertions"]["no_test_files"]
    assert payload["required_assertions"]["no_raw_datasets"]
    assert payload["required_assertions"]["no_gate_blocker_clis"]
    for p in paths:
        base = p.rsplit("/", 1)[-1]
        assert "/tests/" not in p
        assert not base.startswith("test_") and not base.endswith("_test.py")
        assert Path(p).suffix.lower() not in module.RAW_DATA_EXTS
        assert base not in module.GATE_SCRIPTS


def test_guides_present():
    _module, payload, _entries = _payload()
    paths = {r["archive_path"] for r in payload["archive_entries"]}
    for guide in (
        "00_README.md",
        "AUDIT_PROMPT.md",
        "01_ARCHITECTURE_GUIDE.md",
        "02_CODE_MAP.md",
        "03_ENTRY_POINTS.md",
        "04_DATA_ACCESS.md",
    ):
        assert guide in paths


def test_manifest_keeps_family_id_and_native_solver_blocked():
    _module, payload, _entries = _payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["family_identification"] is False
    assert payload["native_solver_result"] is False


def test_zip_is_deterministic():
    module, payload, entries = _payload()
    assert module._build_zip_bytes(REPO_ROOT, payload, entries) == module._build_zip_bytes(
        REPO_ROOT, payload, entries
    )


def test_on_disk_package_is_up_to_date():
    module = _load_module()
    assert module.main(["--check"]) == 0
