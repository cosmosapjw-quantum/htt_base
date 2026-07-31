#!/usr/bin/env python3
"""Build the deterministic PR-274 repository-bound admission result.

This command performs metadata and byte-binding preflight only.  It has no
observed-data analysis or pilot-execution mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Mapping

import yaml


ROOT = Path(__file__).resolve().parents[2]
for source_root in (ROOT, ROOT / "htt/src", ROOT / "htt"):
    value = str(source_root)
    if value not in sys.path:
        sys.path.insert(0, value)

from common.vector_tensor_data_admission import (  # noqa: E402
    NO_ADMITTED_DATA_PILOT,
    build_data_admission_report,
    candidates_from_registry,
    identity_registry_from_mapping,
)


SPEC = ROOT / "docs/research_program/vector_tensor/pr274_spec.yaml"
REGISTRY = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_CANDIDATE_INPUTS.yaml"
)
IDENTITY_REGISTRY = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_DATA_IDENTITY_REGISTRY.yaml"
)
RESULT = (
    ROOT
    / "docs/research_program/vector_tensor/data_admission/"
    "PR274_ADMISSION_RESULT.json"
)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    result: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise RuntimeError("PR-274 YAML mapping key is not hashable") from exc
        if duplicate:
            raise RuntimeError(f"duplicate PR-274 YAML mapping key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _repo_file(relative_text: object, *, label: str) -> Path:
    if not isinstance(relative_text, str) or not relative_text:
        raise RuntimeError(f"{label} path must be non-empty text")
    relative = PurePosixPath(relative_text)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in relative_text
    ):
        raise RuntimeError(f"{label} path must remain repository-relative")
    root = ROOT.resolve(strict=True)
    path = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"{label} path traverses a symlink")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise RuntimeError(f"{label} path is not a regular repository file")
    return resolved


def _load_yaml(path: Path) -> Mapping[str, object]:
    payload = yaml.load(
        path.read_text(encoding="utf-8"),
        Loader=_UniqueKeyLoader,
    )
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a mapping")
    return payload


def _verify_pr151_semantics(
    *,
    spec: Mapping[str, object],
    status: Mapping[str, object],
) -> None:
    canonical = spec["frozen_inputs"]["canonical_status"]
    if canonical["identity_mode"] != "live_semantic":
        raise RuntimeError("canonical status must use live_semantic identity")
    required_card = canonical["required_background_card"]
    background = status.get("background_in_progress")
    if not isinstance(background, list) or required_card not in background:
        raise RuntimeError("PR-151 is not background_in_progress")
    contracts = status.get("background_execution_contracts")
    if not isinstance(contracts, Mapping):
        raise RuntimeError("background execution contracts are missing")
    contract = contracts.get(required_card)
    if not isinstance(contract, Mapping):
        raise RuntimeError("PR-151 background execution contract is missing")
    required_use = canonical["required_partial_scientific_use"]
    if contract.get("partial_scientific_use") != required_use:
        raise RuntimeError("PR-151 partial scientific-use refusal drifted")
    completed = status.get("completed")
    if not isinstance(completed, list) or "PR-273" not in completed:
        raise RuntimeError("PR-273 success dependency is not completed")
    resolutions = status.get("execution_resolutions")
    resolution = (
        resolutions.get("PR-273")
        if isinstance(resolutions, Mapping)
        else None
    )
    if (
        not isinstance(resolution, Mapping)
        or resolution.get("resolution") != "COMPLETED_SUCCESS"
        or resolution.get("success_dependency_satisfied") is not True
    ):
        raise RuntimeError("PR-273 success resolution is not satisfied")


def _verify_frozen_inputs(
    spec: Mapping[str, object],
) -> tuple[dict[str, str], Mapping[str, object]]:
    frozen = spec.get("frozen_inputs")
    if not isinstance(frozen, Mapping) or not frozen:
        raise RuntimeError("PR-274 frozen input registry is missing")
    evidence: dict[str, str] = {}
    status_payload: Mapping[str, object] | None = None
    for label, raw_record in frozen.items():
        if not isinstance(raw_record, Mapping):
            raise RuntimeError(f"frozen input {label} is malformed")
        path = _repo_file(raw_record.get("path"), label=f"frozen input {label}")
        actual = _sha256(path)
        relative = path.relative_to(ROOT.resolve(strict=True)).as_posix()
        evidence[relative] = f"sha256:{actual}"
        if "sha256" in raw_record:
            expected = raw_record["sha256"]
            if actual != expected:
                raise RuntimeError(
                    f"frozen input {label} drifted: {actual} != {expected}"
                )
        elif raw_record.get("identity_mode") == "live_semantic":
            loaded = _load_yaml(path)
            _verify_pr151_semantics(spec=spec, status=loaded)
            status_payload = loaded
        else:
            raise RuntimeError(
                f"frozen input {label} has no supported identity contract"
            )
    if status_payload is None:
        raise RuntimeError("live canonical status evidence was not evaluated")
    return evidence, status_payload


def build() -> dict[str, object]:
    spec = _load_yaml(SPEC)
    if spec.get("pr_id") != "PR-274":
        raise RuntimeError("PR-274 spec identity drifted")
    if spec.get("separate_data_execution_authorization_present") is not False:
        raise RuntimeError("PR-274 cannot carry data-execution authorization")
    if spec.get("pilot_execution_in_this_change_set") != "forbidden":
        raise RuntimeError("PR-274 pilot-execution refusal drifted")

    source_evidence, status = _verify_frozen_inputs(spec)
    registry = _load_yaml(REGISTRY)
    identity_registry_payload = _load_yaml(IDENTITY_REGISTRY)
    identity_registry = identity_registry_from_mapping(
        identity_registry_payload
    )
    if identity_registry.entries:
        raise RuntimeError(
            "frozen PR-274 identity registry must remain empty; "
            "a populated revision requires separate review"
        )
    candidates = candidates_from_registry(registry)
    expected_ids = tuple(spec["candidate_contract"]["exact_ids"])
    actual_ids = tuple(value.candidate_id for value in candidates)
    if actual_ids != expected_ids:
        raise RuntimeError(
            f"candidate membership/order drifted: {actual_ids!r}"
        )

    report = build_data_admission_report(
        report_id="PR274-DATA-ADMISSION-RESULT-V1",
        registry_payload=registry,
        identity_registry_payload=identity_registry_payload,
        repository_root=ROOT,
        source_evidence=source_evidence,
        pr151_status="background_in_progress",
        pr151_partial_scientific_use=status[
            "background_execution_contracts"
        ]["PR-151"]["partial_scientific_use"],
        separate_execution_authorization_present=False,
    )
    payload = report.as_payload()
    if payload["status"] != NO_ADMITTED_DATA_PILOT:
        raise RuntimeError(
            "frozen PR-274 inputs unexpectedly produced an admitted candidate"
        )
    if payload["admitted_count"] != 0 or payload["pilot_executed"] is not False:
        raise RuntimeError("PR-274 admission/execution boundary drifted")
    if payload["candidate_count"] != len(expected_ids):
        raise RuntimeError("PR-274 candidate count drifted")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the committed result equals deterministic output",
    )
    args = parser.parse_args(argv)
    encoded = _json_bytes(build())
    if args.check:
        if not RESULT.is_file():
            raise RuntimeError(f"missing generated result: {RESULT}")
        if RESULT.read_bytes() != encoded:
            raise RuntimeError("committed PR-274 admission result is stale")
        print("OK: PR-274 admission result is deterministic and current")
        return 0
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_bytes(encoded)
    print(
        "WROTE "
        f"{RESULT.relative_to(ROOT)} "
        f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
