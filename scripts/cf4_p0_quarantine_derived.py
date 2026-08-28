#!/usr/bin/env python3
"""Fail-closed wrappers for CF4-derived cards quarantined by PR-120.

Active invocations emit only a canonical blocked-source record.  Exact
historical regeneration is available solely through an explicit legacy mode
whose fixed inputs and outputs live below ``legacy/cf4_p0``.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType


REPO = Path(__file__).resolve().parents[1]
_IMPORT_ROOTS = (REPO, REPO / "htt", REPO / "htt" / "src")
for root in reversed(_IMPORT_ROOTS):
    root_text = str(root)
    if root_text in sys.path:
        sys.path.remove(root_text)
    sys.path.insert(0, root_text)

from common.cf4_p0_quarantine import (  # noqa: E402
    CF4P0PolicyError,
    atomic_write_text,
    quarantine_block_payload,
    read_regular_text,
    require_legacy_reproduction,
)


@dataclass(frozen=True)
class DerivedSpec:
    artifact_id: str
    active_script: str
    active_json: str
    active_markdown: str
    legacy_script: str
    legacy_json: str
    legacy_markdown: str


IDENTIFIED_INTERVAL_SPECS = {
    "v7": DerivedSpec(
        artifact_id="k5_cf4_identified_interval_card",
        active_script="scripts/k5_cf4_identified_interval_card.py",
        active_json="docs/generated/k5_cf4_identified_interval_card.json",
        active_markdown="docs/generated/k5_cf4_identified_interval_card.md",
        legacy_script="legacy/cf4_p0/scripts/k5_cf4_identified_interval_card.py",
        legacy_json="legacy/cf4_p0/cards/k5_cf4_identified_interval_card.json",
        legacy_markdown="legacy/cf4_p0/cards/k5_cf4_identified_interval_card.md",
    ),
    "v8": DerivedSpec(
        artifact_id="k5_cf4_identified_interval_card_v8",
        active_script="scripts/k5_cf4_identified_interval_card_v8.py",
        active_json="docs/generated/k5_cf4_identified_interval_card_v8.json",
        active_markdown="docs/generated/k5_cf4_identified_interval_card_v8.md",
        legacy_script="legacy/cf4_p0/scripts/k5_cf4_identified_interval_card_v8.py",
        legacy_json="legacy/cf4_p0/cards/k5_cf4_identified_interval_card_v8.json",
        legacy_markdown="legacy/cf4_p0/cards/k5_cf4_identified_interval_card_v8.md",
    ),
    "v9": DerivedSpec(
        artifact_id="k5_cf4_identified_interval_card_v9",
        active_script="scripts/k5_cf4_identified_interval_card_v9.py",
        active_json="docs/generated/k5_cf4_identified_interval_card_v9.json",
        active_markdown="docs/generated/k5_cf4_identified_interval_card_v9.md",
        legacy_script="legacy/cf4_p0/scripts/k5_cf4_identified_interval_card_v9.py",
        legacy_json="legacy/cf4_p0/cards/k5_cf4_identified_interval_card_v9.json",
        legacy_markdown="legacy/cf4_p0/cards/k5_cf4_identified_interval_card_v9.md",
    ),
}


@dataclass(frozen=True)
class SingleCardSpec:
    artifact_id: str
    active_script: str
    active_json: str
    legacy_script: str
    legacy_json: str


SINGLE_CARD_SPECS = {
    "coverage": SingleCardSpec(
        artifact_id="k5_cf4_release_coverage",
        active_script="scripts/k5_cf4_release_coverage.py",
        active_json="docs/generated/k5_cf4_release_coverage.json",
        legacy_script="legacy/cf4_p0/scripts/k5_cf4_release_coverage.py",
        legacy_json="legacy/cf4_p0/cards/k5_cf4_release_coverage.json",
    ),
    "joint": SingleCardSpec(
        artifact_id="pr08_006_joint_artifact",
        active_script="scripts/pr08_006_joint_artifact.py",
        active_json="docs/generated/pr08_006_joint_artifact.json",
        legacy_script="legacy/cf4_p0/scripts/pr08_006_joint_artifact.py",
        legacy_json="legacy/cf4_p0/cards/pr08_006_joint_artifact.json",
    ),
    "forecast": SingleCardSpec(
        artifact_id="bass_extended_joint_forecast",
        active_script="scripts/bass_extended_joint_forecast.py",
        active_json="docs/generated/bass_extended_joint_forecast.json",
        legacy_script="legacy/cf4_p0/scripts/bass_extended_joint_forecast.py",
        legacy_json="legacy/cf4_p0/cards/bass_extended_joint_forecast.json",
    ),
}


def _load_module(
    path: Path, name: str, *, module_file: Path | None = None
) -> ModuleType:
    """Execute frozen bytes while preserving their original active-path root.

    Historical scripts resolve the repository via ``Path(__file__).parents``.
    Loading them from below ``legacy/cf4_p0`` would therefore change their
    import-time inputs.  Present the former active path as ``__file__`` while
    still compiling and executing the inventory-pinned archived bytes.
    """

    if not path.is_file():
        raise RuntimeError(f"cannot load frozen legacy producer: {path}")
    module = ModuleType(name)
    module.__file__ = str(module_file or path)
    module.__package__ = ""
    sys.modules[name] = module
    code = compile(path.read_bytes(), str(path), "exec")
    exec(code, module.__dict__)
    return module


def _verify_pinned_legacy(paths: tuple[str, ...]) -> None:
    """Require exact inventory hashes before and after a frozen execution."""

    for relative in paths:
        require_legacy_reproduction(
            enabled=True, artifact_path=relative, repo_root=REPO
        )


def _block_payload(spec: DerivedSpec) -> dict:
    payload = quarantine_block_payload(REPO)
    payload["artifact"] = {
        "artifact_id": spec.artifact_id,
        "artifact_kind": "derived_result_card_block_record",
        "active_json": spec.active_json,
        "active_markdown": spec.active_markdown,
        "producer": spec.active_script,
        "legacy_reproduction_only": [spec.legacy_json, spec.legacy_markdown],
        "legacy_public_use": False,
    }
    return payload


def _render_markdown(spec: DerivedSpec, payload: dict) -> str:
    finding_ids = ", ".join(row["finding_id"] for row in payload["findings"])
    return "\n".join(
        [
            f"# {spec.artifact_id} - CF4 P0 blocked source record",
            "",
            f"- Status: `{payload['status']}`",
            f"- Findings: `{finding_ids}`",
            "- Replacement value: `none`",
            "- Allowed use: `blocked_source_record_only`",
            f"- Canonical block: `docs/generated/cf4_p0_quarantine_block.json`",
            f"- Historical copy: `{spec.legacy_json}` (`legacy_reproduction_only`; public use false)",
            "",
            "Quarantine is propagation control, not scientific remediation.",
            "",
        ]
    )


def _active_texts(spec: DerivedSpec) -> tuple[str, str]:
    payload = _block_payload(spec)
    return (
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        _render_markdown(spec, payload),
    )


def _retarget_legacy(
    module: ModuleType,
    spec: DerivedSpec,
    *,
    json_output: Path,
    markdown_output: Path,
) -> None:
    module.REPO_ROOT = REPO
    module.OUT_JSON = json_output
    module.OUT_MD = markdown_output
    replacements = {
        "K5_COVERAGE": REPO / "legacy/cf4_p0/cards/k5_cf4_release_coverage.json",
        "FROZEN_CARD": REPO / "legacy/cf4_p0/cards/k5_cf4_identified_interval_card.json",
        "FROZEN_V7_CARD": REPO / "legacy/cf4_p0/cards/k5_cf4_identified_interval_card.json",
        "FROZEN_V8_CARD": REPO / "legacy/cf4_p0/cards/k5_cf4_identified_interval_card_v8.json",
    }
    for name, value in replacements.items():
        if hasattr(module, name):
            setattr(module, name, value)


def _run_legacy(spec: DerivedSpec, *, check: bool) -> int:
    pinned = (spec.legacy_script, spec.legacy_json, spec.legacy_markdown)
    _verify_pinned_legacy(pinned)
    try:
        frozen = {
            "json": (REPO / spec.legacy_json).read_bytes(),
            "markdown": (REPO / spec.legacy_markdown).read_bytes(),
        }
        with tempfile.TemporaryDirectory(prefix="htt-cf4-derived-") as temporary:
            temporary_root = Path(temporary)
            json_output = temporary_root / Path(spec.legacy_json).name
            markdown_output = temporary_root / Path(spec.legacy_markdown).name
            shutil.copy2(REPO / spec.legacy_json, json_output)
            shutil.copy2(REPO / spec.legacy_markdown, markdown_output)
            module = _load_module(
                REPO / spec.legacy_script,
                f"cf4_p0_legacy_{spec.artifact_id}",
                module_file=REPO / spec.active_script,
            )
            _retarget_legacy(
                module,
                spec,
                json_output=json_output,
                markdown_output=markdown_output,
            )
            result = int(module.main(["--check"] if check else []))
            if result == 0 and (
                json_output.read_bytes() != frozen["json"]
                or markdown_output.read_bytes() != frozen["markdown"]
            ):
                raise RuntimeError(
                    "legacy derived reproduction differs from frozen evidence; "
                    "canonical legacy bytes were not modified"
                )
    finally:
        _verify_pinned_legacy(pinned)
    return result


def derived_main(spec: DerivedSpec, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit a canonical PR-120 block record for a CF4-derived card."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    args = parser.parse_args(argv)
    if args.legacy_reproduction:
        return _run_legacy(spec, check=args.check)

    json_text, markdown_text = _active_texts(spec)
    targets = (
        (REPO / spec.active_json, json_text),
        (REPO / spec.active_markdown, markdown_text),
    )
    if args.check:
        stale = []
        for path, expected in targets:
            relative = path.relative_to(REPO).as_posix()
            try:
                current = read_regular_text(REPO, relative)
            except CF4P0PolicyError:
                current = None
            if current != expected:
                stale.append(relative)
        if stale:
            print("stale CF4-derived block record(s): " + ", ".join(stale), file=sys.stderr)
            return 1
        print(f"CF4-derived quarantine block current: {spec.artifact_id}")
        return 0
    for path, rendered in targets:
        atomic_write_text(REPO, path.relative_to(REPO).as_posix(), rendered)
    print(f"wrote active block records for {spec.artifact_id}")
    return 0


def _single_block_payload(spec: SingleCardSpec) -> dict:
    payload = quarantine_block_payload(REPO)
    payload["artifact"] = {
        "artifact_id": spec.artifact_id,
        "artifact_kind": "derived_result_card_block_record",
        "active_path": spec.active_json,
        "producer": spec.active_script,
        "legacy_reproduction_only_path": spec.legacy_json,
        "legacy_public_use": False,
    }
    return payload


def _retarget_single_legacy(
    module: ModuleType, spec: SingleCardSpec, *, output: Path
) -> None:
    module.REPO = REPO
    module.REPO_ROOT = REPO
    if hasattr(module, "GEN"):
        module.GEN = REPO / "docs/generated"
    if hasattr(module, "OUT"):
        module.OUT = output
    if hasattr(module, "OUT_JSON"):
        module.OUT_JSON = output
    if spec.artifact_id == "pr08_006_joint_artifact":
        active_loader = module._load

        def _legacy_aware_load(name: str) -> dict:
            if name == "k5_cf4_release_coverage.json":
                return json.loads(
                    (REPO / "legacy/cf4_p0/cards/k5_cf4_release_coverage.json").read_text(
                        encoding="utf-8"
                    )
                )
            return active_loader(name)

        module._load = _legacy_aware_load


def single_card_main(spec: SingleCardSpec, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit a canonical PR-120 block record for a CF4-derived card."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    args = parser.parse_args(argv)
    if args.legacy_reproduction:
        pinned = (spec.legacy_script, spec.legacy_json)
        _verify_pinned_legacy(pinned)
        try:
            frozen = (REPO / spec.legacy_json).read_bytes()
            with tempfile.TemporaryDirectory(prefix="htt-cf4-single-") as temporary:
                output = Path(temporary) / Path(spec.legacy_json).name
                shutil.copy2(REPO / spec.legacy_json, output)
                module = _load_module(
                    REPO / spec.legacy_script,
                    f"cf4_p0_legacy_{spec.artifact_id}",
                    module_file=REPO / spec.active_script,
                )
                _retarget_single_legacy(module, spec, output=output)
                result = int(module.main(["--check"] if args.check else []))
                if result == 0 and output.read_bytes() != frozen:
                    raise RuntimeError(
                        "legacy single-card reproduction differs from frozen evidence; "
                        "canonical legacy bytes were not modified"
                    )
        finally:
            _verify_pinned_legacy(pinned)
        return result

    rendered = json.dumps(_single_block_payload(spec), indent=2, sort_keys=True) + "\n"
    target = REPO / spec.active_json
    if args.check:
        try:
            current = read_regular_text(REPO, spec.active_json)
        except CF4P0PolicyError:
            current = None
        if current != rendered:
            print(f"stale CF4-derived block record: {spec.active_json}", file=sys.stderr)
            return 1
        print(f"CF4-derived quarantine block current: {spec.artifact_id}")
        return 0
    atomic_write_text(REPO, spec.active_json, rendered)
    print(f"wrote {spec.active_json} status=QUARANTINED_OPEN_FINDINGS")
    return 0


__all__ = [
    "DerivedSpec",
    "IDENTIFIED_INTERVAL_SPECS",
    "SINGLE_CARD_SPECS",
    "SingleCardSpec",
    "derived_main",
    "single_card_main",
]
