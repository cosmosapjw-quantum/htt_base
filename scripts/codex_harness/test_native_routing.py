from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("native_routing", ROOT / "scripts/codex_harness/native_routing.py")
assert SPEC is not None and SPEC.loader is not None
native_routing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native_routing)


def test_policy_is_runtime_gated_and_preserves_requested_vs_observed() -> None:
    policy = native_routing.load_policy()
    assert policy["availability_contract"]["requested_is_not_observed"] is True
    assert policy["global_guards"]["default_parallelism"] == 3
    assert policy["routes"]["routine_mechanical"]["requested"] == {"model": "gpt-5.6-luna", "effort": "low"}
    assert policy["routes"]["general_code"]["requested"] == {"model": "gpt-5.6-terra", "effort": "medium"}
    assert policy["routes"]["orchestrator"]["requested"] == {"model": "gpt-6.1-sol", "effort": "medium"}
    assert policy["routes"]["review_or_research"]["requested"] == {"model": "gpt-6-astra", "effort": "xhigh"}
    assert policy["routes"]["blocker_escalation"]["requested"] == {"model": "gpt-6-astra", "effort": "ultra"}
    assert policy["escalation"]["trigger_any"] == [
        "two_same_class_substantive_failures_with_raw_receipts",
        "a_genuinely_high_consequence_blocker_with_its_risk_recorded",
    ]


def test_resolver_uses_fallback_only_when_the_catalog_supports_it() -> None:
    policy = native_routing.load_policy()
    fallback = native_routing.resolve_route(policy, "general_code", {("gpt-6.1-sol", "medium")})
    assert fallback["selection"] == "FALLBACK_AVAILABLE"
    assert fallback["selected"] == {"model": "gpt-6.1-sol", "effort": "medium"}
    assert fallback["observed_runtime"] == "UNKNOWN"
    assert fallback["launch_performed"] is False

    unavailable = native_routing.resolve_route(policy, "review_or_research", {("gpt-6-sol", "high")})
    assert unavailable["selection"] == "UNAVAILABLE"
    assert unavailable["selected"] is None


def test_unknown_or_malformed_route_fails_closed(tmp_path: Path) -> None:
    policy = native_routing.load_policy()
    with pytest.raises(native_routing.RoutingPolicyError, match="unknown route"):
        native_routing.resolve_route(policy, "invented", set())

    wrong_effort = native_routing.resolve_route(policy, "general_code", {("gpt-6.1-sol", "high")})
    assert wrong_effort["selection"] == "UNAVAILABLE"

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema_version": 99, "routes": {}}), encoding="utf-8")
    with pytest.raises(native_routing.RoutingPolicyError, match="unsupported"):
        native_routing.load_policy(bad)

    root_scalar = tmp_path / "scalar.json"
    root_scalar.write_text("null", encoding="utf-8")
    with pytest.raises(native_routing.RoutingPolicyError, match="unsupported"):
        native_routing.load_policy(root_scalar)
