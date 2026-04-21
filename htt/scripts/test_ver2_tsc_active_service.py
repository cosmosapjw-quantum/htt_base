from __future__ import annotations

import importlib.util
import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT_PATH = ROOT / "ver2_tsc_active_service.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("ver2_tsc_active_service_test", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_script_json_output_contains_overlay_policy_ledger() -> None:
    module = _load_script_module()
    stdout = StringIO()
    with redirect_stdout(stdout):
        rc = module.main(["--json"])
    assert rc == 0
    payload = json.loads(stdout.getvalue())
    assert payload["publication_ready"] is False
    assert payload["overlay_policy_ledger"]["advisory_only"] is True
    assert payload["overlay_policy_ledger"]["channel_claim_ceiling"]["TT"] == "conditional"


def test_script_policy_json_outputs_claim_limited_demo() -> None:
    module = _load_script_module()
    stdout = StringIO()
    with redirect_stdout(stdout):
        rc = module.main(["--policy-json", "--claim-limited-demo"])
    assert rc == 0
    payload = json.loads(stdout.getvalue())
    assert payload["publication_ready"] is False
    assert "TT" in payload["claim_limited_channels"]
    assert "claim_ceiling_insufficient:TT=exploratory" in payload["publication_blockers"]


def test_script_write_dir_emits_bundle_and_policy_artifacts(tmp_path: Path) -> None:
    module = _load_script_module()
    stdout = StringIO()
    with redirect_stdout(stdout):
        rc = module.main(["--write-dir", str(tmp_path)])
    assert rc == 0

    bundle_json = tmp_path / "tsc_active_service_bundle.json"
    bundle_md = tmp_path / "tsc_active_service_bundle.md"
    policy_json = tmp_path / "tsc_policy_ledger.json"
    policy_md = tmp_path / "tsc_policy_ledger.md"
    assert bundle_json.exists()
    assert bundle_md.exists()
    assert policy_json.exists()
    assert policy_md.exists()

    payload = json.loads(bundle_json.read_text(encoding="utf-8"))
    assert payload["overlay_policy_ledger"]["advisory_only"] is True
    assert policy_md.read_text(encoding="utf-8").startswith("# TSC Policy Ledger")


def test_script_check_passes_for_pending_and_claim_limited_modes() -> None:
    module = _load_script_module()

    pending_stdout = StringIO()
    with redirect_stdout(pending_stdout):
        pending_rc = module.main(["--check"])
    assert pending_rc == 0
    assert "[PASS] TSC active-service export check" in pending_stdout.getvalue()

    limited_stdout = StringIO()
    with redirect_stdout(limited_stdout):
        limited_rc = module.main(["--check", "--claim-limited-demo"])
    assert limited_rc == 0
    assert "mode=claim-limited" in limited_stdout.getvalue()
