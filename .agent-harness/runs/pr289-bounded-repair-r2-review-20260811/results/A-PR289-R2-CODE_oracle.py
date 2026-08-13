#!/usr/bin/env python3
"""Independent executable R2 oracle for frozen PR-289 candidate e7affa43."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.abc
import importlib.machinery
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import types


ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]

from common import data_identity as contracts  # noqa: E402
from scripts.codex_harness import run_pr289_data_identity_v2 as runner  # noqa: E402


REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
SPEC = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
RECEIPT = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
STAMP = "2026-08-09T00:00:00+00:00"


def resign_record(record: dict[str, object]) -> None:
    stable = dict(record)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record["record_id"] = contracts.canonical_sha256(stable)
    inspection = dict(record)
    inspection.pop("inspection_receipt_id")
    record["inspection_receipt_id"] = contracts.canonical_sha256(inspection)


def resign_bundle(payload: dict[str, object]) -> None:
    records = payload["records"]
    assert isinstance(records, list) and records
    payload["lane_admission_bundle_id"] = contracts.canonical_sha256(
        {
            "lane_id": payload["lane_id"],
            "product_id": payload["product_id"],
            "component_inventory_id": records[0]["component_inventory_id"],
            "record_ids": [row["record_id"] for row in records],
        }
    )


def semantic_replay_oracle(registry: contracts.LaneRegistryV2) -> dict[str, object]:
    mutations: dict[str, object] = {
        "source_locator_kind": "unregistered_locator_kind",
        "source_locator_identity": "sha256:" + "0" * 64,
        "release_name": "",
        "release_version": "v",
        "release_identity": "placeholder",
        "license_identity": "placeholder",
        "regular_file_status": "NOT_VERIFIED",
        "symlink_status": "ALIAS_PRESENT",
        "completeness_status": "INCOMPLETE",
        "units_contract_id": "",
        "coordinate_frame_id": "",
        "sign_orientation_convention_id": "",
        "directional_convention_id": "",
        "harmonic_convention_id": "",
        "mask_id": "",
        "selection_id": "",
        "sky_support_id": "",
        "covariance_id": "",
        "covariance_status": "INVALID",
        "null_ensemble_id": "",
        "null_ensemble_status": "INVALID",
        "transfer_source": "native_bass",
        "transfer_function_spec_id": "unregistered-native-spec",
        "transfer_provenance_status": "NATIVE_VALIDATED",
        "sky_support_status": "INVALID",
        "license_status": "UNBOUND",
        "acquisition_status": "INCOMPLETE",
    }
    rejected: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pr289-r2-semantic-") as temporary:
        descriptor = contracts._mutation_descriptor(
            Path(temporary) / "planck", registry.lane("PLANCK")
        )
        decision = contracts.evaluate_lane_identity(
            registry=registry,
            lane_id="PLANCK",
            descriptor=descriptor,
            inspected_at_utc=STAMP,
        )
        assert decision.complete
        original = decision.as_payload()
        for field_name, value in mutations.items():
            payload = copy.deepcopy(original)
            record = payload["records"][0]
            record[field_name] = value
            resign_record(record)
            resign_bundle(payload)
            try:
                contracts.replay_lane_admission_decision(payload, registry=registry)
            except contracts.DataIdentityError:
                rejected.append(field_name)
    return {
        "passed": rejected == list(mutations),
        "mutations": list(mutations),
        "rejected": rejected,
    }


def repeated_ordinal_oracle(registry: contracts.LaneRegistryV2) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="pr289-r2-ordinal-") as temporary:
        descriptor = contracts._mutation_descriptor(
            Path(temporary) / "desi", registry.lane("DESI")
        )
        decision = contracts.evaluate_lane_identity(
            registry=registry,
            lane_id="DESI",
            descriptor=descriptor,
            inspected_at_utc=STAMP,
        )
        assert decision.complete
        payload = decision.as_payload()
        positions = [
            index
            for index, record in enumerate(payload["records"])
            if record["component_id"] == "ezmock_inventory"
        ][:2]
        payload["records"][positions[0]] = copy.deepcopy(
            payload["records"][positions[1]]
        )
        resign_bundle(payload)
        try:
            contracts.replay_lane_admission_decision(payload, registry=registry)
        except contracts.DataIdentityError as exc:
            return {
                "passed": "ordinal" in str(exc) or "inventory" in str(exc),
                "marker": str(exc),
                "actual_registered_cardinality": len(positions),
            }
    return {"passed": False, "marker": "duplicate ordinal survived"}


def hostile_loader_oracle() -> dict[str, object]:
    module_name = "common.data_identity"
    expected = (ROOT / "htt/src/common/data_identity.py").resolve()
    expected_sha = hashlib.sha256(expected.read_bytes()).hexdigest()
    previous_module = sys.modules.get(module_name)
    previous_meta = list(sys.meta_path)
    fake = types.ModuleType(module_name)

    def must_not_execute(*_args, **_kwargs):
        raise AssertionError("preloaded hostile replacement executed")

    fake.build_data_identity_v2_receipt = must_not_execute
    fake.load_lane_registry = must_not_execute

    class HostileLoader(importlib.abc.Loader):
        def create_module(self, _spec):
            return None

        def exec_module(self, module) -> None:
            module.__file__ = str(expected)
            module.build_data_identity_v2_receipt = must_not_execute
            module.load_lane_registry = must_not_execute

    hostile_loader = HostileLoader()

    class HostileFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, _path, _target=None):
            if fullname != module_name:
                return None
            spec = importlib.machinery.ModuleSpec(
                fullname, hostile_loader, origin=str(expected)
            )
            spec.has_location = True
            return spec

    try:
        sys.modules[module_name] = fake
        sys.meta_path[:] = [HostileFinder(), *previous_meta]
        payload = runner._build()
        loaded = sys.modules[module_name]
        return {
            "passed": (
                payload["terminal"] == contracts.PASS_TOKEN
                and Path(loaded.__file__).resolve() == expected
                and loaded.__pr289_loaded_sha256__ == expected_sha
                and runner._source_bindings()["htt/src/common/data_identity.py"]
                == expected_sha
            ),
            "terminal": payload["terminal"],
            "loaded_sha256": loaded.__pr289_loaded_sha256__,
        }
    finally:
        sys.meta_path[:] = previous_meta
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module


def late_build_parent_replacement_oracle() -> dict[str, object]:
    saved = (runner.ROOT, runner.OUTPUT, runner._build, runner.os.replace)
    real_replace = runner.os.replace
    with tempfile.TemporaryDirectory(prefix="pr289-r2-late-build-") as temporary:
        root = Path(temporary) / "repo"
        parent = root / "docs/generated"
        parent.mkdir(parents=True)
        output = parent / "receipt.json"
        detached = root / "docs/generated-detached"
        payload = {
            "terminal": contracts.PASS_TOKEN,
            "receipt_content_id": "sha256:" + "0" * 64,
        }

        def replace_after_last_assertion(
            source, destination, *, src_dir_fd=None, dst_dir_fd=None
        ):
            parent.rename(detached)
            parent.mkdir()
            return real_replace(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        try:
            runner.ROOT, runner.OUTPUT = root, output
            runner._build = lambda root=root: payload
            runner.os.replace = replace_after_last_assertion
            error = None
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                try:
                    return_code = runner._write()
                except RuntimeError as exc:
                    error = str(exc)
                    return_code = 1
            return {
                "passed": return_code != 0 and not output.exists(),
                "return_code": return_code,
                "error": error,
                "reported_stdout": captured.getvalue().strip(),
                "advertised_output_exists": output.exists(),
                "detached_output_exists": (detached / output.name).exists(),
            }
        finally:
            runner.ROOT, runner.OUTPUT, runner._build, runner.os.replace = saved


def late_check_parent_replacement_oracle() -> dict[str, object]:
    saved = (runner.ROOT, runner.OUTPUT, runner._build, runner._read_bound_output)
    real_read = runner._read_bound_output
    with tempfile.TemporaryDirectory(prefix="pr289-r2-late-check-") as temporary:
        root = Path(temporary) / "repo"
        parent = root / "docs/generated"
        parent.mkdir(parents=True)
        output = parent / "receipt.json"
        detached = root / "docs/generated-detached"
        payload = {
            "terminal": contracts.PASS_TOKEN,
            "receipt_content_id": "sha256:" + "0" * 64,
        }
        output.write_bytes(runner._encoded(payload))
        calls = 0

        def read_after_last_assertion(*, output: Path, parent_fd: int) -> bytes:
            nonlocal calls
            calls += 1
            if calls == 2:
                parent.rename(detached)
                parent.mkdir()
                (parent / output.name).write_bytes(b"ATTACKER\n")
            return real_read(output=output, parent_fd=parent_fd)

        try:
            runner.ROOT, runner.OUTPUT = root, output
            runner._build = lambda root=root: payload
            runner._read_bound_output = read_after_last_assertion
            error = None
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                try:
                    return_code = runner._check(root=root)
                except RuntimeError as exc:
                    error = str(exc)
                    return_code = 1
            public_bytes = output.read_bytes()
            return {
                "passed": return_code != 0,
                "return_code": return_code,
                "error": error,
                "reported_stdout": captured.getvalue().strip(),
                "advertised_output_sha256": hashlib.sha256(public_bytes).hexdigest(),
                "advertised_output_is_attacker_bytes": public_bytes == b"ATTACKER\n",
                "detached_output_exists": (detached / output.name).exists(),
            }
        finally:
            (
                runner.ROOT,
                runner.OUTPUT,
                runner._build,
                runner._read_bound_output,
            ) = saved


def interpreter_alias_oracle() -> dict[str, object]:
    results: dict[str, object] = {}
    outputs: list[str] = []
    for executable in (Path("/usr/bin/python"), Path("/usr/bin/python3"), Path("/usr/bin/python3.10")):
        if not executable.exists():
            results[str(executable)] = {"available": False}
            continue
        completed = subprocess.run(
            [
                str(executable),
                "-B",
                "scripts/codex_harness/run_pr289_data_identity_v2.py",
                "check",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        outputs.append(completed.stdout)
        results[str(executable)] = {
            "available": True,
            "return_code": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr": completed.stderr,
        }
    available = [row for row in results.values() if row["available"]]
    return {
        "passed": all(row["return_code"] == 0 for row in available)
        and len(set(outputs)) == 1,
        "results": results,
    }


def mutation_receipt_oracle() -> dict[str, object]:
    import yaml

    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    expected = [row["mutation_id"] for row in spec["mutation_registry"]]
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    rows = payload["mutation_results"]
    observed = [row["mutation_id"] for row in rows]
    exact_fields = {"mutation_id", "executed", "activated", "killed", "observed_marker"}
    return {
        "passed": len(rows) == 32
        and observed == expected
        and all(
            set(row) == exact_fields
            and row["executed"] is True
            and row["activated"] is True
            and row["killed"] is True
            and bool(row["observed_marker"])
            for row in rows
        ),
        "count": len(rows),
        "ordered_ids": observed,
    }


def archive_containment_oracle() -> dict[str, object]:
    cases = {
        "traversal": ("../escape", tarfile.REGTYPE, b"x"),
        "absolute": ("/absolute", tarfile.REGTYPE, b"x"),
        "symlink": ("linked", tarfile.SYMTYPE, b""),
        "hardlink": ("hardlinked", tarfile.LNKTYPE, b""),
    }
    rejected: list[str] = []
    for case, (name, member_type, raw) in cases.items():
        with tempfile.TemporaryDirectory(prefix="pr289-r2-archive-") as temporary:
            archive_bytes = io.BytesIO()
            with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
                info = tarfile.TarInfo(name)
                info.type = member_type
                if member_type == tarfile.REGTYPE:
                    info.size = len(raw)
                    archive.addfile(info, io.BytesIO(raw))
                else:
                    info.linkname = "outside"
                    archive.addfile(info)
            archive_bytes.seek(0)
            with tarfile.open(fileobj=archive_bytes, mode="r:") as archive:
                try:
                    runner._safe_extract_archive(archive, Path(temporary))
                except RuntimeError:
                    rejected.append(case)
    return {"passed": rejected == list(cases), "rejected": rejected}


def main() -> int:
    registry = contracts.load_lane_registry(REGISTRY)
    results = {
        "schema": "htt.pr289.r2_code_oracle.v1",
        "candidate_sha": "e7affa4302f60cb02a664b315693b22e2372ef33",
        "semantic_replay": semantic_replay_oracle(registry),
        "repeated_role_ordinal": repeated_ordinal_oracle(registry),
        "hostile_loader_verified_bytes": hostile_loader_oracle(),
        "late_build_parent_replacement": late_build_parent_replacement_oracle(),
        "late_check_parent_replacement": late_check_parent_replacement_oracle(),
        "interpreter_alias_receipt": interpreter_alias_oracle(),
        "mutation_receipt": mutation_receipt_oracle(),
        "archive_containment": archive_containment_oracle(),
    }
    results["overall_passed"] = all(
        row["passed"] for key, row in results.items() if isinstance(row, dict) and key not in {"schema"}
    )
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if results["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
