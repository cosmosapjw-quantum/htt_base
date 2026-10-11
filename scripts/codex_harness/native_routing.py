#!/usr/bin/env python3
"""Resolve the active native routing policy without launching an agent.

The managed runtime remains the authority for model availability.  This helper
turns a dispatch-time capability catalog into an auditable requested/selected
route and deliberately never turns a requested profile into observed runtime
identity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POLICY_PATH = Path(__file__).resolve().parents[2] / "docs/harness/NATIVE_ROUTING_POLICY_V1.json"


class RoutingPolicyError(ValueError):
    """A malformed policy is not safe to dispatch."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingPolicyError(f"cannot read routing policy {path}: {exc}") from exc
    if not isinstance(policy, dict) or policy.get("schema_version") != 1 or not isinstance(policy.get("routes"), dict):
        raise RoutingPolicyError("unsupported or malformed routing policy")
    return policy


def _validate_choice(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise RoutingPolicyError(f"{label} must be an object")
    model, effort = value.get("model"), value.get("effort")
    if not isinstance(model, str) or not model or not isinstance(effort, str) or not effort:
        raise RoutingPolicyError(f"{label} must contain non-empty model and effort")
    return {"model": model, "effort": effort}


def resolve_route(
    policy: dict[str, Any], route_name: str, available_profiles: set[tuple[str, str]]
) -> dict[str, Any]:
    """Return a non-launching route decision, failing closed if no model exists."""
    routes = policy.get("routes")
    if not isinstance(routes, dict) or route_name not in routes:
        raise RoutingPolicyError(f"unknown route: {route_name}")
    route = routes[route_name]
    if not isinstance(route, dict):
        raise RoutingPolicyError(f"route {route_name} must be an object")
    requested = _validate_choice(route.get("requested"), f"route {route_name}.requested")
    fallback_raw = route.get("fallback")
    fallback = None if fallback_raw is None else _validate_choice(fallback_raw, f"route {route_name}.fallback")

    selected = None
    selection = "UNAVAILABLE"
    if (requested["model"], requested["effort"]) in available_profiles:
        selected, selection = requested, "REQUESTED_AVAILABLE"
    elif fallback is not None and (fallback["model"], fallback["effort"]) in available_profiles:
        selected, selection = fallback, "FALLBACK_AVAILABLE"
    return {
        "route": route_name,
        "requested": requested,
        "selected": selected,
        "selection": selection,
        "observed_runtime": "UNKNOWN",
        "launch_performed": False,
        "availability_catalog_profiles": [
            {"model": model, "effort": effort}
            for model, effort in sorted(available_profiles)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve but do not launch a native routing profile.")
    parser.add_argument("route", help="route name declared in NATIVE_ROUTING_POLICY_V1.json")
    parser.add_argument(
        "--available-profile",
        action="append",
        default=[],
        metavar="MODEL/EFFORT",
        help="exact model/effort pair supplied by the managed runtime catalog",
    )
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    try:
        profiles = set()
        for raw in args.available_profile:
            model, separator, effort = raw.rpartition("/")
            if not separator or not model or not effort:
                raise RoutingPolicyError(f"invalid available profile {raw!r}; expected MODEL/EFFORT")
            profiles.add((model, effort))
        decision = resolve_route(load_policy(args.policy), args.route, profiles)
    except RoutingPolicyError as exc:
        parser.error(str(exc))
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["selection"] != "UNAVAILABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
