import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_blocker_manifest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_blocker_manifest", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_example_manifests_validate():
    module = _load_module()
    for path in (ROOT / "examples").glob("*.example.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert module.validate_manifest(payload) == []


def test_manifest_requires_blocked_claim_tier_until_discharge():
    module = _load_module()
    payload = json.loads((ROOT / "examples" / "k1_e2e_manifest.example.json").read_text(encoding="utf-8"))
    payload["claim_tier"] = "measured"
    errors = module.validate_manifest(payload)
    assert any("claim_tier" in error for error in errors)


def test_manifest_rejects_missing_hashes():
    module = _load_module()
    payload = json.loads((ROOT / "examples" / "cf4_realization_manifest.example.json").read_text(encoding="utf-8"))
    payload["input_hashes"] = []
    errors = module.validate_manifest(payload)
    assert any("input_hashes" in error for error in errors)

