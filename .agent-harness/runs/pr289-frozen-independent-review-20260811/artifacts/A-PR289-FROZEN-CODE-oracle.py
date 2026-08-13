#!/usr/bin/env python3
"""Independent, assignment-local PR-289 replay and containment oracle."""

from __future__ import annotations

import argparse
import contextlib
import copy
from dataclasses import replace
from io import BytesIO, StringIO
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr289_data_identity_v2.py"
TEST_PATH = ROOT / "tests/contracts/test_data_identity_registry_v2.py"
OUTPUT_DEFAULT = (
    ROOT
    / ".agent-harness/runs/pr289-frozen-independent-review-20260811/artifacts/"
    "A-PR289-FROZEN-CODE-oracle-result.json"
)


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "stderr_tail": completed.stderr[-500:],
    }


def resign_record(module, record: dict[str, Any]) -> None:
    stable = dict(record)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record["record_id"] = module.canonical_sha256(stable)
    inspection = dict(record)
    inspection.pop("inspection_receipt_id")
    record["inspection_receipt_id"] = module.canonical_sha256(inspection)


def resign_bundle(module, payload: dict[str, Any]) -> None:
    payload["lane_admission_bundle_id"] = module.canonical_sha256(
        {
            "lane_id": payload["lane_id"],
            "product_id": payload["product_id"],
            "component_inventory_id": payload["records"][0][
                "component_inventory_id"
            ],
            "record_ids": [row["record_id"] for row in payload["records"]],
        }
    )


def record_replay_probes(module, support) -> dict[str, Any]:
    registry = module.load_lane_registry(support.REGISTRY_PATH)
    with tempfile.TemporaryDirectory(prefix="a-pr289-record-") as temporary:
        decision = module.evaluate_lane_identity(
            registry=registry,
            lane_id="PLANCK",
            descriptor=support._valid_descriptor(Path(temporary) / "planck"),
            inspected_at_utc=support.STAMP_A,
        )
        payload = decision.as_payload()
        row = payload["records"][0]
        row.update(
            {
                "source_locator_kind": "unregistered_locator_kind",
                "regular_file_status": "NOT_VERIFIED",
                "symlink_status": "ALIAS_PRESENT",
                "license_status": "UNBOUND",
                "units_contract_id": "",
                "coordinate_frame_id": "",
                "sign_orientation_convention_id": "",
                "directional_convention_id": "",
                "mask_id": "",
                "selection_id": "",
                "covariance_id": "",
                "covariance_status": "INVALID",
                "transfer_source": "native_bass",
                "transfer_function_spec_id": "unregistered-native-spec",
                "transfer_provenance_status": "NATIVE_VALIDATED",
                "sky_support_status": "INVALID",
            }
        )
        resign_record(module, row)
        resign_bundle(module, payload)
        semantic_replay = module.replay_lane_admission_decision(
            payload, registry=registry
        )
        constructor_copy = replace(
            decision.records[0], _construction_token=module._RECORD_TOKEN
        )

    with tempfile.TemporaryDirectory(prefix="a-pr289-ordinal-") as temporary:
        desi = module.evaluate_lane_identity(
            registry=registry,
            lane_id="DESI",
            descriptor=support._valid_descriptor(
                Path(temporary) / "desi", "DESI"
            ),
            inspected_at_utc=support.STAMP_A,
        )
        exported = desi.as_payload()
        positions = [
            index
            for index, record in enumerate(exported["records"])
            if record["component_id"] == "ezmock_inventory"
        ][:2]
        exported["records"][positions[0]] = copy.deepcopy(
            exported["records"][positions[1]]
        )
        resign_bundle(module, exported)
        ordinal_replay = module.replay_lane_admission_decision(
            exported, registry=registry
        )
    return {
        "semantic_record_replay_accepted": (
            semantic_replay.records[0].regular_file_status == "NOT_VERIFIED"
        ),
        "semantic_fields_accepted": {
            key: semantic_replay.records[0].as_payload()[key]
            for key in (
                "source_locator_kind",
                "regular_file_status",
                "symlink_status",
                "license_status",
                "units_contract_id",
                "coordinate_frame_id",
                "sign_orientation_convention_id",
                "directional_convention_id",
                "mask_id",
                "selection_id",
                "covariance_id",
                "covariance_status",
                "transfer_source",
                "transfer_function_spec_id",
                "transfer_provenance_status",
                "sky_support_status",
            )
        },
        "module_token_constructor_copy_accepted": (
            constructor_copy.as_payload() == decision.records[0].as_payload()
        ),
        "duplicate_ordinal_replay_accepted": (
            ordinal_replay.records[positions[0]].component_ordinal
            == ordinal_replay.records[positions[1]].component_ordinal
        ),
        "duplicate_component_id": "ezmock_inventory",
        "duplicate_ordinals": [
            ordinal_replay.records[index].component_ordinal
            for index in positions
        ],
        "desi_record_count": len(ordinal_replay.records),
    }


def module_loading_probe(runner) -> dict[str, Any]:
    module_name = "common.data_identity"
    expected = (ROOT / "htt/src/common/data_identity.py").resolve()
    real_module = sys.modules.get(module_name)

    class InconsistentLoader(importlib.abc.Loader):
        def create_module(self, spec):
            return None

        def exec_module(self, module) -> None:
            module.__file__ = str(expected)

            class Receipt:
                def as_payload(self) -> dict[str, Any]:
                    return {
                        "terminal": "INCONSISTENT_LOADER_EXECUTED",
                        "aggregate_status": "NO_ADMITTED_IDENTITIES",
                        "authorization_receipts": [
                            {"status": "NOT_AUTHORIZED"} for _ in range(6)
                        ],
                    }

            def load_lane_registry(path):
                return object()

            def build_data_identity_v2_receipt(**kwargs):
                return Receipt()

            load_lane_registry.__module__ = module_name
            build_data_identity_v2_receipt.__module__ = module_name
            module.load_lane_registry = load_lane_registry
            module.build_data_identity_v2_receipt = build_data_identity_v2_receipt

        def get_data(self, path: str) -> bytes:
            return expected.read_bytes()

    loader = InconsistentLoader()

    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname != module_name:
                return None
            spec = importlib.machinery.ModuleSpec(
                fullname, loader, origin=str(expected)
            )
            spec.has_location = True
            return spec

    finder = Finder()
    sys.meta_path.insert(0, finder)
    try:
        payload = runner._build()
    finally:
        sys.meta_path.remove(finder)
        sys.modules.pop(module_name, None)
        if real_module is not None:
            sys.modules[module_name] = real_module
    return {
        "inconsistent_loader_accepted": (
            payload["terminal"] == "INCONSISTENT_LOADER_EXECUTED"
        ),
        "reported_origin": str(expected),
        "reported_source_sha256": hashlib.sha256(expected.read_bytes()).hexdigest(),
    }


def output_containment_probe(runner) -> dict[str, Any]:
    old_root, old_output, old_build = runner.ROOT, runner.OUTPUT, runner._build
    try:
        with tempfile.TemporaryDirectory(prefix="a-pr289-output-") as temporary:
            base = Path(temporary)
            root = base / "repo"
            generated = root / "docs/generated"
            outside = base / "outside"
            generated.mkdir(parents=True)
            outside.mkdir()
            output = generated / "receipt.json"

            def replace_parent_during_build(root=root):
                generated.rename(root / "docs/generated-before-build")
                generated.symlink_to(outside, target_is_directory=True)
                return {
                    "terminal": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
                    "receipt_content_id": "sha256:" + "0" * 64,
                }

            runner.ROOT = root
            runner.OUTPUT = output
            runner._build = replace_parent_during_build
            with contextlib.redirect_stdout(StringIO()):
                returncode = runner._write()
            outside_output = outside / "receipt.json"
            return {
                "parent_replacement_accepted": (
                    returncode == 0 and outside_output.is_file()
                ),
                "returncode": returncode,
                "outside_output_created": outside_output.is_file(),
            }
    finally:
        runner.ROOT, runner.OUTPUT, runner._build = old_root, old_output, old_build


def archive_validation_probe(runner) -> dict[str, Any]:
    cases = {
        "parent_traversal": ("../escape.txt", tarfile.REGTYPE, ""),
        "absolute": ("/tmp/a-pr289-absolute", tarfile.REGTYPE, ""),
        "symlink": ("linked", tarfile.SYMTYPE, "outside"),
        "hardlink": ("hardlinked", tarfile.LNKTYPE, "outside"),
        "fifo": ("fifo", tarfile.FIFOTYPE, ""),
    }
    rejected: dict[str, bool] = {}
    for name, (member_name, member_type, link_name) in cases.items():
        raw = BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo(member_name)
            info.type = member_type
            info.linkname = link_name
            body = b"x" if member_type == tarfile.REGTYPE else b""
            info.size = len(body)
            archive.addfile(info, BytesIO(body) if body else None)
        raw.seek(0)
        with tempfile.TemporaryDirectory(prefix="a-pr289-archive-") as temporary:
            destination = Path(temporary)
            with tarfile.open(fileobj=raw, mode="r:") as archive:
                try:
                    runner._safe_extract_archive(archive, destination)
                except RuntimeError:
                    rejected[name] = True
                else:
                    rejected[name] = False
    return {"unsafe_members_rejected": rejected, "all_rejected": all(rejected.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]
    runner = load_path("a_pr289_runner", RUNNER_PATH)
    support = load_path("a_pr289_test_support", TEST_PATH)
    import common.data_identity as module

    aliases = []
    for name in ("python", "python3"):
        executable = shutil.which(name)
        if executable and executable not in [row["argv"][0] for row in aliases]:
            aliases.append(
                run(
                    [
                        executable,
                        "-B",
                        "scripts/codex_harness/run_pr289_data_identity_v2.py",
                        "check",
                    ]
                )
            )
    python310 = shutil.which("python3.10")
    python310_preflight = (
        run(
            [
                python310,
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "preflight",
            ]
        )
        if python310
        else {"available": False}
    )
    payload = {
        "schema": "htt.pr289.frozen_code_independent_oracle.v1",
        "candidate_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "record_replay": record_replay_probes(module, support),
        "module_loading": module_loading_probe(runner),
        "output_containment": output_containment_probe(runner),
        "archive_validation": archive_validation_probe(runner),
        "interpreter_alias_replays": aliases,
        "interpreter_alias_returncodes_differ": (
            len({row["returncode"] for row in aliases}) > 1
        ),
        "python310_preflight": python310_preflight,
        "oracle_status": "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
