import json
import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "docs/audits/revision_program_2026-06-18/package_inventory.json"
MD_OUT = ROOT / "docs/audits/revision_program_2026-06-18/package_inventory.md"
SCRIPT_OUT = ROOT / "scripts/inventory_revision_program_packages.py"


def _load_inventory_module():
    spec = importlib.util.spec_from_file_location("revision_program_inventory", SCRIPT_OUT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revision_package_inventory_check_mode_passes():
    result = subprocess.run(
        [
            "venv/bin/python",
            "scripts/inventory_revision_program_packages.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_revision_package_inventory_records_sources_and_smoke_results():
    payload = json.loads(JSON_OUT.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "htt.revision_program_inventory.v1"
    assert payload["owner"] == "COMMON"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["transfer_source"] == "none"
    assert set(payload["packages"]) == {
        "HTT_Bianchi_revision_program.zip",
        "htt_revision_upgrade_package_2026-06-17.zip",
    }
    for package in payload["packages"].values():
        assert package["sha256"]
        assert package["entries"]
        assert package["source_role"] == "external_revision_input"
    smoke_package_map = {
        "revision_program_run_all": "HTT_Bianchi_revision_program.zip",
        "upgrade_package_pytest": "htt_revision_upgrade_package_2026-06-17.zip",
    }
    for smoke_name, package_name in smoke_package_map.items():
        smoke = payload["smoke_tests"][smoke_name]
        package_sha = payload["packages"][package_name]["sha256"]
        assert smoke["status"] == "passed"
        assert smoke["verified_package_sha256"] == package_sha
        assert smoke["current_package_sha256"] == package_sha
        assert smoke["verified_at_utc"]
        assert smoke["exit_code"] == 0
        assert smoke["evidence_mode"] == "recorded_prior_smoke_result_hash_bound"
        assert str(ROOT) not in smoke["command"]
        assert "REPO_ROOT=$(pwd)" in smoke["command"]
    assert "synthetic/analytic scaffold" in payload["caveats"]
    assert "not publication evidence" in payload["caveats"]
    text = MD_OUT.read_text(encoding="utf-8")
    assert "HTT_Bianchi_revision_program.zip" in text
    assert "htt_revision_upgrade_package_2026-06-17.zip" in text
    assert "not publication evidence" in text
    assert str(ROOT) not in text
    assert "REPO_ROOT=$(pwd)" in text


def test_revision_package_inventory_downgrades_smoke_status_when_verified_hash_is_stale():
    module = _load_inventory_module()
    original = module.VERIFIED_SMOKE_EVIDENCE["revision_program_run_all"]
    module.VERIFIED_SMOKE_EVIDENCE["revision_program_run_all"] = {
        **original,
        "verified_package_sha256": "0" * 64,
    }
    payload = module.build_payload()

    smoke = payload["smoke_tests"]["revision_program_run_all"]
    assert smoke["current_package_sha256"] != smoke["verified_package_sha256"]
    assert smoke["status"] != "passed"
