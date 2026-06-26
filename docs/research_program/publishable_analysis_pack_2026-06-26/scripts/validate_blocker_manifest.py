#!/usr/bin/env python3
"""Validate blocker-discharge input manifests.

The validator is intentionally strict about provenance fields and intentionally
silent about scientific promotion. A valid manifest means "ready to be used by a
blocker-discharge command", not "blocker closed".
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


COMMON_REQUIRED = {
    "schema_version",
    "blocker",
    "owner",
    "claim_tier",
    "config_hash",
    "input_hashes",
    "generating_command",
    "caveats",
}

SCHEMA_REQUIRED = {
    "htt.k1_e2e_manifest.v1": {
        "release_family",
        "component_method",
        "observed_map_id",
        "simulation_count",
        "map_paths",
        "mask_path",
        "beam_fwhm_arcmin",
        "input_nside",
        "analysis_nside",
        "ell_min",
        "ell_max",
        "statistic_ids",
        "source_url",
    },
    "htt.cf4_realization_manifest.v1": {
        "field_family",
        "realization_count",
        "grid_shape",
        "coordinate_frame",
        "velocity_units",
        "smoothing_scale_mpc_h",
        "bgc_status",
        "curl_status",
        "field_paths",
        "source_reference",
    },
    "htt.cf4_release_mock_manifest.v1": {
        "release_binding",
        "mock_count",
        "selection_function_id",
        "distance_error_model",
        "frame_convention",
        "sky_support_status",
        "mock_paths",
        "source_reference",
    },
}


def _require_hashes(values: Any, field: str, errors: list[str]) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"{field} must be a non-empty list")
        return
    for value in values:
        if not isinstance(value, str) or not value.startswith("sha256:"):
            errors.append(f"{field} entries must be sha256 labels: {value!r}")


def validate_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(COMMON_REQUIRED - set(payload))
    errors.extend(f"missing common field: {field}" for field in missing)
    schema = payload.get("schema_version")
    if schema not in SCHEMA_REQUIRED:
        errors.append(f"unknown schema_version: {schema!r}")
        return errors
    missing_schema = sorted(SCHEMA_REQUIRED[schema] - set(payload))
    errors.extend(f"missing schema field: {field}" for field in missing_schema)

    if "input_hashes" in payload:
        _require_hashes(payload["input_hashes"], "input_hashes", errors)
    if not str(payload.get("config_hash", "")).startswith("sha256:"):
        errors.append("config_hash must start with sha256:")
    if "blocked" not in str(payload.get("claim_tier", "")).lower():
        errors.append("claim_tier must remain blocked until real discharge output exists")

    count_fields = ["simulation_count", "realization_count", "mock_count"]
    for field in count_fields:
        if field in payload and (not isinstance(payload[field], int) or payload[field] <= 0):
            errors.append(f"{field} must be a positive integer")

    path_fields = ["map_paths", "field_paths", "mock_paths"]
    for field in path_fields:
        if field in payload and (not isinstance(payload[field], list) or not payload[field]):
            errors.append(f"{field} must be a non-empty list")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--json", action="store_true", help="print machine-readable result")
    args = parser.parse_args(argv)

    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate_manifest(payload)
    result = {
        "manifest": str(args.manifest),
        "schema_version": payload.get("schema_version"),
        "valid": not errors,
        "errors": errors,
        "claim_boundary": "valid input manifest is not a measured result",
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        print(f"invalid manifest: {args.manifest}")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"valid blocker input manifest: {args.manifest}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

