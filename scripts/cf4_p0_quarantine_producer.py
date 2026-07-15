#!/usr/bin/env python3
"""Shared fail-closed entry point for the quarantined CF4 P0 producers.

The active producer paths no longer expose a numerical ``measure`` operation.
They materialise the canonical PR-120 block record.  Exact historical code and
cards remain runnable only when both an explicit legacy mode and a legacy-only
output path are supplied.
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
    LegacyReproductionRequired,
    atomic_write_text,
    quarantine_block_payload,
    read_regular_text,
    require_legacy_reproduction,
)


@dataclass(frozen=True)
class ProducerSpec:
    artifact_id: str
    active_output: str
    active_producer: str
    legacy_script: str
    legacy_output: str


PRODUCERS = {
    "mv": ProducerSpec(
        artifact_id="cf4_mv_bulkflow_card",
        active_output="docs/generated/cf4_mv_bulkflow_card.json",
        active_producer="scripts/cf4_mv_bulkflow.py",
        legacy_script="legacy/cf4_p0/scripts/cf4_mv_bulkflow.py",
        legacy_output="legacy/cf4_p0/cards/cf4_mv_bulkflow_card.json",
    ),
    "mock": ProducerSpec(
        artifact_id="cf4_mock_significance_card",
        active_output="docs/generated/cf4_mock_significance_card.json",
        active_producer="scripts/cf4_mock_calibrated_significance.py",
        legacy_script="legacy/cf4_p0/scripts/cf4_mock_calibrated_significance.py",
        legacy_output="legacy/cf4_p0/cards/cf4_mock_significance_card.json",
    ),
    "ml": ProducerSpec(
        artifact_id="cf4_velocity_correlation_ml_card",
        active_output="docs/generated/cf4_velocity_correlation_ml_card.json",
        active_producer="scripts/cf4_velocity_correlation_ml.py",
        legacy_script="legacy/cf4_p0/scripts/cf4_velocity_correlation_ml.py",
        legacy_output="legacy/cf4_p0/cards/cf4_velocity_correlation_ml_card.json",
    ),
    "gls": ProducerSpec(
        artifact_id="cf4_bulkflow_lcdm_card",
        active_output="docs/generated/cf4_bulkflow_lcdm_card.json",
        active_producer="scripts/cf4_bulkflow_lcdm_variance.py",
        legacy_script="legacy/cf4_p0/scripts/cf4_bulkflow_lcdm_variance.py",
        legacy_output="legacy/cf4_p0/cards/cf4_bulkflow_lcdm_card.json",
    ),
}


def block_payload(spec: ProducerSpec) -> dict:
    """Return the canonical root block plus non-scientific artifact identity."""
    payload = quarantine_block_payload(REPO)
    payload["artifact"] = {
        "artifact_id": spec.artifact_id,
        "artifact_kind": "result_card_block_record",
        "active_path": spec.active_output,
        "producer": spec.active_producer,
        "legacy_reproduction_only_path": spec.legacy_output,
        "legacy_public_use": False,
    }
    return payload


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _load_module(
    path: Path, name: str, *, module_file: Path | None = None
) -> ModuleType:
    """Execute frozen bytes while preserving their original active-path root.

    Moving a script below ``legacy/cf4_p0`` changes ``Path(__file__).parents``.
    The frozen source historically resolved the repository from its active
    script path, so expose that old path as ``__file__`` without modifying the
    archived bytes.
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


def _legacy_mv_module() -> ModuleType:
    module = _load_module(
        REPO / PRODUCERS["mv"].legacy_script,
        "cf4_p0_legacy_mv_bulkflow",
        module_file=REPO / PRODUCERS["mv"].active_producer,
    )
    _retarget_legacy_module(module, PRODUCERS["mv"], REPO / PRODUCERS["mv"].legacy_output)
    return module


def _retarget_legacy_module(
    module: ModuleType, spec: ProducerSpec, output: Path
) -> None:
    """Retarget path constants without modifying the byte-frozen source."""
    module.REPO = REPO
    module.OUT = output
    path_overrides = {
        "CF4": REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz",
        "GROUPS": REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz",
        "VARIANTS": REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz",
        "OBS_DEFAULTS": REPO / "htt/workspace/data/obs_defaults.json",
    }
    for name, value in path_overrides.items():
        if hasattr(module, name):
            setattr(module, name, value)
    if hasattr(module, "MV_CARD"):
        module.MV_CARD = REPO / PRODUCERS["mv"].legacy_output
    if hasattr(module, "_load_cf4mv") and spec.artifact_id != "cf4_mv_bulkflow_card":
        module._load_cf4mv = _legacy_mv_module


def _run_legacy(spec: ProducerSpec, output_arg: str, *, check: bool) -> int:
    output = Path(output_arg)
    if not output.is_absolute():
        output = REPO / output
    try:
        output_relative = output.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError as exc:
        raise LegacyReproductionRequired(
            "legacy CF4 producer output escapes the repository"
        ) from exc
    if output_relative != spec.legacy_output:
        raise LegacyReproductionRequired(
            f"legacy producer {spec.artifact_id} must target exactly "
            f"{spec.legacy_output}, not {output_relative}"
        )
    if output.suffix != ".json":
        raise ValueError("legacy CF4 producer output must be a JSON card")
    pinned = [spec.legacy_script, spec.legacy_output]
    if spec.artifact_id != PRODUCERS["mv"].artifact_id:
        pinned.extend(
            [PRODUCERS["mv"].legacy_script, PRODUCERS["mv"].legacy_output]
        )
    for relative in pinned:
        require_legacy_reproduction(
            enabled=True, artifact_path=relative, repo_root=REPO
        )
    frozen_bytes = output.read_bytes()
    try:
        with tempfile.TemporaryDirectory(prefix="htt-cf4-legacy-") as temporary:
            temporary_output = Path(temporary) / output.name
            shutil.copy2(output, temporary_output)
            module = _load_module(
                REPO / spec.legacy_script,
                f"cf4_p0_legacy_{spec.artifact_id}",
                module_file=REPO / spec.active_producer,
            )
            _retarget_legacy_module(module, spec, temporary_output)
            result = int(module.main(["--check"] if check else []))
            if result == 0 and temporary_output.read_bytes() != frozen_bytes:
                raise LegacyReproductionRequired(
                    "legacy producer reproduction differs from the frozen output; "
                    "canonical legacy bytes were not modified"
                )
    finally:
        # The frozen source and canonical evidence are read-only authorities.
        # Execution occurs only against a disposable copy, then every authority
        # is rechecked so a successful return code cannot launder a mutation.
        for relative in pinned:
            require_legacy_reproduction(
                enabled=True, artifact_path=relative, repo_root=REPO
            )
    return result


def producer_main(spec: ProducerSpec, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit the canonical PR-120 CF4 P0 quarantine block record."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    parser.add_argument(
        "--legacy-output",
        help="explicit output below legacy/cf4_p0/; required in legacy mode",
    )
    args = parser.parse_args(argv)
    if args.legacy_reproduction:
        if not args.legacy_output:
            parser.error("--legacy-reproduction requires --legacy-output")
        return _run_legacy(spec, args.legacy_output, check=args.check)
    if args.legacy_output:
        parser.error("--legacy-output requires --legacy-reproduction")

    output = REPO / spec.active_output
    rendered = _render(block_payload(spec))
    if args.check:
        try:
            current = read_regular_text(REPO, spec.active_output)
        except CF4P0PolicyError:
            current = None
        if current != rendered:
            print(f"STALE quarantine block record: {spec.active_output}", file=sys.stderr)
            return 1
        print(f"CF4 P0 quarantine block current: {spec.active_output}")
        return 0
    atomic_write_text(REPO, spec.active_output, rendered)
    print(f"wrote {spec.active_output} status=QUARANTINED_OPEN_FINDINGS")
    return 0
