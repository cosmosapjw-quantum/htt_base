from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

import scripts.validate_planck_mes_pmg_wu009_full_replay as validator


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PACKAGE_FILES = {
    "PACKAGE_INDEX.yaml",
    "AUTHORITY_BINDING.yaml",
    "DATA_AVAILABILITY_BINDING.yaml",
    "WU009_EXECUTION_CONTRACT.yaml",
    "D9_RECIPE_TEMPLATE.yaml",
    "D9_LANE_TERMINALS.yaml",
    "CODEX_HANDOFF.md",
    "CODEX_HANDOFF_PROMPT.md",
}

LANE_PREREQUISITES = {
    "D.9.0": [],
    "D.9.A": ["D.9.0"],
    "D.9.B": ["D.9.0"],
    "D.9.C": ["D.9.B"],
    "D.9.D": ["D.9.0"],
    "D.9.E": ["D.9.0"],
    "D.9.F": ["D.9.A", "D.9.B", "D.9.C", "D.9.D", "D.9.E"],
    "D.9.G": ["D.9.F"],
    "D.9.H": ["D.9.G"],
    "D.9.Z": ["D.9.0", "D.9.A", "D.9.B", "D.9.C", "D.9.D", "D.9.E", "D.9.F", "D.9.G", "D.9.H"],
}
TEST_XACT_ARCHIVE_BYTES = b"synthetic xAct 1.3.0 archive for validator tests\n"
TEST_XACT_ARCHIVE_SHA256 = hashlib.sha256(TEST_XACT_ARCHIVE_BYTES).hexdigest()


def _reported_version(executable: Path, argument: str) -> str:
    completed = subprocess.run(
        [str(executable), argument],
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout.strip() or completed.stderr.strip())


def _bound_file(root: Path, name: str) -> dict[str, str]:
    path = root / "receipts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    kinds_and_metrics = {
        "eb-operator-identity.json": (
            "EB_OPERATOR_IDENTITY",
            {"coefficient_level": True, "operator_id": "TEST_OPERATOR", "target_mode_count": 24},
        ),
        "eb-response.json": (
            "EB_RESPONSE",
            {"condition_ceiling": 1000000.0, "condition_number": 20.0, "rank": 24},
        ),
        "eb-leakage.json": (
            "EB_LEAKAGE",
            {"out_of_band_alias_test": True, "pure_b_injection": True, "pure_e_injection": True},
        ),
        "eb-transfer.json": (
            "EB_TRANSFER",
            {"target_mode_count": 24, "transfer_bound": True},
        ),
        "null-identity.json": (
            "NULL_IDENTITY",
            {"bundle_id": "TEST_MATCHED_NULL", "row_count": 2},
        ),
        "null-covariance.json": (
            "NULL_COVARIANCE",
            {
                "b_mode_hypothesis_declared": True,
                "mapmaking_systematics_included": True,
                "polarization_noise_included": True,
                "te_covariance_preserved": True,
            },
        ),
        "null-pipeline.json": (
            "NULL_PIPELINE",
            {
                "adaptive_selection_rerun": True,
                "complete_rowwise_replay": True,
                "row_equivariant": True,
            },
        ),
    }
    if name.startswith("terminal-"):
        lane = name.removeprefix("terminal-").removesuffix(".json")
        kind = f"LANE_MANIFEST:{lane}"
        metrics = {"lane": lane}
        state = "SEALED"
    else:
        kind, metrics = kinds_and_metrics[name]
        state = "PASS"
    payload = {
        "schema": "htt.planck_mes_pmg_wu009.evidence_receipt.v1",
        "package_id": "PLANCK_MES_PMG_WU009_FULL_REPLAY_LOCAL_EXECUTION_20260830",
        "evidence_kind": kind,
        "state": state,
        "metrics": metrics,
    }
    artifact_roles = {
        "EB_OPERATOR_IDENTITY": {"operator_manifest"},
        "EB_RESPONSE": {"response_matrix", "rank_diagnostic", "condition_diagnostic"},
        "EB_LEAKAGE": {"pure_e_injection", "pure_b_injection", "out_of_band_alias"},
        "EB_TRANSFER": {"coefficient_transfer"},
        "NULL_IDENTITY": {"null_bundle_manifest"},
        "NULL_COVARIANCE": {
            "te_covariance",
            "polarization_noise",
            "mapmaking_systematics",
            "b_mode_hypothesis",
        },
        "NULL_PIPELINE": {"rowwise_pipeline", "adaptive_replay"},
    }
    roles = {"lane_manifest"} if kind.startswith("LANE_MANIFEST:") else artifact_roles[kind]
    metrics_digest = hashlib.sha256(
        json.dumps(metrics, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    artifacts = []
    for role in sorted(roles):
        safe_kind = kind.replace(":", "-").replace(".", "_")
        artifact_path = root / "receipts" / "artifacts" / f"{safe_kind}-{role}.json"
        source_path = root / "receipts" / "sources" / f"{safe_kind}-{role}.dat"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(f"synthetic evidence source for {kind} {role}\n".encode("utf-8"))
        artifact_payload = {
            "schema": "htt.planck_mes_pmg_wu009.evidence_artifact.v1",
            "package_id": "PLANCK_MES_PMG_WU009_FULL_REPLAY_LOCAL_EXECUTION_20260830",
            "evidence_kind": kind,
            "role": role,
            "receipt_metrics_sha256": metrics_digest,
            "source": {
                "path": str(source_path.resolve()),
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            },
        }
        artifact_path.write_text(
            json.dumps(artifact_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifacts.append(
            {
                "role": role,
                "path": str(artifact_path.resolve()),
                "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            }
        )
    payload["artifacts"] = artifacts
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _base_config(root: Path) -> dict:
    output = root / "output"
    raw = root / "raw"
    dossier = root / "dossier.tar"
    manifest = root / "explicit-input-manifest.txt"
    xact = root / "xact"
    xact_archive = root / "xAct_1.3.0.tgz"
    for directory in (output, raw, xact):
        directory.mkdir(parents=True, exist_ok=True)
    wolfram = root / "bin" / "wolframscript"
    wolfram.parent.mkdir(parents=True, exist_ok=True)
    wolfram.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-version\" ]; then\n"
        "  printf '%s\\n' 'Wolfram test identity'\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    os.chmod(wolfram, 0o755)
    xact_archive.write_bytes(TEST_XACT_ARCHIVE_BYTES)
    dossier.write_bytes(b"sealed theorem dossier\n")
    manifest.write_text("relative/input/file.fits sha256:placeholder\n", encoding="utf-8")
    return {
        "schema": "htt.planck_mes_pmg_wu009.instantiated_execution.v1",
        "package_id": "PLANCK_MES_PMG_WU009_FULL_REPLAY_LOCAL_EXECUTION_20260830",
        "execution_phase": "PREFLIGHT",
        "authority": {
            "accepted_design_commit": "bda8e489bff7c26fb5fb03fba59360028d01a2fe",
            "accepted_design_tree": "aa734e7933efc6f763d49aaf9f0d9c1bdad6b3b1",
            "scientific_base_commit": "5e81ed1635b8fe6fc944829a9fab7ab8d5b8c654",
        },
        "runtime": {
            "REPO_ROOT": str(REPO_ROOT.resolve()),
            "OUTPUT_ROOT": str(output.resolve()),
            "PLANCK_RAW_ROOT": str(raw.resolve()),
            "RAW_ROOTS": [str(raw.resolve())],
            "THEOREM_DOSSIER": str(dossier.resolve()),
            "THEOREM_DOSSIER_SHA256": hashlib.sha256(dossier.read_bytes()).hexdigest(),
            "XACT_PARENT": str(xact.resolve()),
        },
        "toolchains": {
            "python": {
                "executable": str(Path(sys.executable).resolve()),
                "version": _reported_version(Path(sys.executable).resolve(), "--version"),
                "sha256": hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
            },
            "wolfram": {
                "executable": str(wolfram.resolve()),
                "version": _reported_version(wolfram.resolve(), "-version"),
                "sha256": hashlib.sha256(wolfram.read_bytes()).hexdigest(),
            },
            "xact": {
                "parent": str(xact.resolve()),
                "version": "xAct 1.3.0",
                "source_archive": {
                    "path": str(xact_archive.resolve()),
                    "sha256": TEST_XACT_ARCHIVE_SHA256,
                },
            },
        },
        "inspection": {
            "explicit_manifest": str(manifest.resolve()),
            "explicit_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "recursive_scan": False,
            "commands": [],
        },
        "outputs": [str((output / "run").resolve())],
        "temperature_inverse": {
            "has_absolute_temperature": True,
            "includes_monopole": True,
            "includes_dipole": True,
        },
        "polarization": {
            "stokes_fields": ["I", "Q_stokes", "U"],
            "q_u_spin": 2,
            "eb_operator": {
                "coefficient_level": True,
                "target_mode_count": 24,
                "rank": 24,
                "condition_number": 20.0,
                "condition_ceiling": 1000000.0,
                "bounded": True,
                "pure_e_injection": True,
                "pure_b_injection": True,
                "out_of_band_alias_test": True,
                "identity_receipt": _bound_file(root, "eb-operator-identity.json"),
                "response_receipt": _bound_file(root, "eb-response.json"),
                "leakage_receipt": _bound_file(root, "eb-leakage.json"),
                "transfer_receipt": _bound_file(root, "eb-transfer.json"),
            },
            "matched_joint_null": {
                "matched": True,
                "reruns_complete_pipeline_per_row": True,
                "identity_receipt": _bound_file(root, "null-identity.json"),
                "covariance_receipt": _bound_file(root, "null-covariance.json"),
                "pipeline_receipt": _bound_file(root, "null-pipeline.json"),
            },
        },
        "claims": {
            "same_sky_role": "SAME_SKY_ROBUSTNESS_ONLY",
            "independent_replication": False,
            "product_substitution": False,
            "claim_promotion": False,
            "physical_cause_identified": False,
            "bianchi_family_identified": False,
            "foreground_exclusion": False,
            "cross_field_role": "EXPLORATORY_ONLY",
            "joint_rv_role": "EXPLORATORY_ONLY",
            "amplitude_conditional_role": "EXPLORATORY_ONLY",
            "shared_data_evalue_multiplication": False,
            "new_observed_rank": False,
        },
        "product_admissions": [
            {"requested_product": "SMICA", "admitted_product": "SMICA"}
        ],
        "terminals": [],
    }


def _seal_all_lanes(config: dict) -> None:
    config["execution_phase"] = "FINAL_SEAL"
    root = Path(config["runtime"]["OUTPUT_ROOT"]).parent
    config["terminals"] = [
        {
            "lane": lane,
            "phase_state": "EXECUTED",
            "terminal_state": "NO_ADMISSIBLE_NEW_RESULT",
            "prerequisites": LANE_PREREQUISITES[lane],
            "manifest_receipt": _bound_file(root, f"terminal-{lane}.json"),
        }
        for lane in sorted(validator.LANES)
    ]


class PlanckMesWu009PackageTests(unittest.TestCase):
    def _errors(self, config: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "config.yaml"
            path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
            with mock.patch.object(
                validator,
                "EXPECTED_XACT_ARCHIVE_SHA256",
                TEST_XACT_ARCHIVE_SHA256,
            ):
                return validator.validate_instantiated(path)

    def test_committed_package_has_exact_initial_files_and_validates(self) -> None:
        package = validator.DEFAULT_PACKAGE_ROOT
        self.assertEqual({path.name for path in package.iterdir()}, EXPECTED_PACKAGE_FILES)
        self.assertEqual(validator.validate_package(package), [])

    def test_valid_instantiation_passes_without_reading_raw_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = _base_config(root)
            path = root / "config.yaml"
            path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
            with mock.patch.object(
                validator,
                "EXPECTED_XACT_ARCHIVE_SHA256",
                TEST_XACT_ARCHIVE_SHA256,
            ):
                self.assertEqual(validator.validate_instantiated(path), [])

    def test_path_escape_and_recursive_scan_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["outputs"] = [str(Path(raw).resolve() / "escaped")]
            config["inspection"]["commands"] = ["find /raw -type f"]
            errors = self._errors(config)
        self.assertTrue(any("OUTPUT_PATH_ESCAPE" in item for item in errors), errors)
        self.assertTrue(any("RECURSIVE_SCAN_FORBIDDEN" in item for item in errors), errors)

    def test_relative_output_and_raw_write_command_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["outputs"] = ["relative-successor"]
            config["inspection"]["commands"] = [
                f"touch {config['runtime']['PLANCK_RAW_ROOT']}/mutated.fits"
            ]
            errors = self._errors(config)
        self.assertTrue(any("OUTPUT_PATH_NOT_ABSOLUTE" in item for item in errors), errors)
        self.assertTrue(any("READ_ONLY_INSPECTION_COMMANDS_REQUIRED" in item for item in errors), errors)

    def test_missing_runtime_identities_and_dossier_hash_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            del config["runtime"]["REPO_ROOT"]
            config["runtime"]["THEOREM_DOSSIER_SHA256"] = ""
            config["toolchains"]["wolfram"]["version"] = ""
            errors = self._errors(config)
        self.assertTrue(any("MISSING_RUNTIME_IDENTITY" in item for item in errors), errors)
        self.assertTrue(any("DOSSIER_IDENTITY_REQUIRED" in item for item in errors), errors)
        self.assertTrue(any("MISSING_TOOLCHAIN_IDENTITY" in item for item in errors), errors)

    def test_schema_and_runtime_paths_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["schema"] = "htt.unknown.v1"
            config["runtime"]["REPO_ROOT"] = "relative/repo"
            config["inspection"]["explicit_manifest"] = "relative-manifest.txt"
            errors = self._errors(config)
        self.assertIn("CONFIG_SCHEMA_MISMATCH", errors)
        self.assertTrue(any("RUNTIME_PATH_NOT_ABSOLUTE:REPO_ROOT" in item for item in errors), errors)
        self.assertIn("EXPLICIT_INPUT_MANIFEST_PATH_NOT_ABSOLUTE", errors)

    def test_repository_toolchain_and_authority_bindings_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = _base_config(root)
            empty_repo = root / "not-a-repository"
            empty_repo.mkdir()
            config["runtime"]["REPO_ROOT"] = str(empty_repo.resolve())
            config["toolchains"]["wolfram"]["executable"] = str((root / "missing-wolfram").resolve())
            config["toolchains"]["python"]["version"] = "USER_SUPPLIED"
            config["authority"]["accepted_design_tree"] = "0" * 40
            errors = self._errors(config)
        self.assertIn("REPO_ROOT_NOT_GIT_WORKTREE", errors)
        self.assertTrue(any("TOOLCHAIN_EXECUTABLE_UNRESOLVED:wolfram" in item for item in errors), errors)
        self.assertTrue(any("MISSING_TOOLCHAIN_IDENTITY:python" in item for item in errors), errors)
        self.assertIn("AUTHORITY_BINDING_MISMATCH", errors)

    def test_toolchain_identities_are_derived_not_self_asserted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["toolchains"]["python"]["version"] = "Python invented identity"
            config["toolchains"]["wolfram"]["sha256"] = "0" * 64
            config["toolchains"]["xact"]["version"] = "xAct invented identity"
            errors = self._errors(config)
        self.assertIn("TOOLCHAIN_VERSION_MISMATCH:python", errors)
        self.assertIn("TOOLCHAIN_HASH_MISMATCH:wolfram", errors)
        self.assertIn("XACT_VERSION_MISMATCH", errors)

    def test_empty_git_repository_cannot_self_assert_authority(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = _base_config(root)
            empty_repo = root / "empty-git-repository"
            empty_repo.mkdir()
            subprocess.run(["git", "init", "-q", str(empty_repo)], check=True)
            config["runtime"]["REPO_ROOT"] = str(empty_repo.resolve())
            errors = self._errors(config)
        self.assertTrue(any("REPOSITORY_AUTHORITY" in item for item in errors), errors)

    def test_missing_absolute_temperature_monopole_or_dipole_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["temperature_inverse"]["includes_dipole"] = False
            errors = self._errors(config)
        self.assertTrue(any("ABSOLUTE_T_MONOPOLE_DIPOLE_REQUIRED" in item for item in errors), errors)

    def test_unmatched_null_and_invalid_eb_operator_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["polarization"]["matched_joint_null"]["matched"] = False
            config["polarization"]["eb_operator"]["rank"] = 23
            config["polarization"]["eb_operator"]["bounded"] = False
            errors = self._errors(config)
        self.assertTrue(any("MATCHED_POLARIZATION_NULL_REQUIRED" in item for item in errors), errors)
        self.assertTrue(any("EB_OPERATOR_FULL_RANK_REQUIRED" in item for item in errors), errors)
        self.assertTrue(any("EB_OPERATOR_UNBOUNDED" in item for item in errors), errors)

    def test_operator_and_matched_null_receipts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            del config["polarization"]["eb_operator"]["response_receipt"]
            config["polarization"]["matched_joint_null"]["covariance_receipt"]["sha256"] = "0" * 64
            errors = self._errors(config)
        self.assertTrue(any("MISSING_BOUND_RECEIPT:EB_RESPONSE" in item for item in errors), errors)
        self.assertTrue(any("BOUND_RECEIPT_HASH_MISMATCH:NULL_COVARIANCE" in item for item in errors), errors)

    def test_arbitrary_bytes_cannot_masquerade_as_evidence_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            receipt = config["polarization"]["eb_operator"]["response_receipt"]
            path = Path(receipt["path"])
            path.write_bytes(b"arbitrary bytes\n")
            receipt["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            errors = self._errors(config)
        self.assertTrue(any("BOUND_RECEIPT_CONTENT_INVALID:EB_RESPONSE" in item for item in errors), errors)

    def test_evidence_artifact_roles_cannot_be_substituted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            identity_receipt = config["polarization"]["eb_operator"]["identity_receipt"]
            response_receipt = config["polarization"]["eb_operator"]["response_receipt"]
            identity_payload = json.loads(Path(identity_receipt["path"]).read_text(encoding="utf-8"))
            response_path = Path(response_receipt["path"])
            response_payload = json.loads(response_path.read_text(encoding="utf-8"))
            response_payload["artifacts"][0] = identity_payload["artifacts"][0]
            response_path.write_text(
                json.dumps(response_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            response_receipt["sha256"] = hashlib.sha256(response_path.read_bytes()).hexdigest()
            errors = self._errors(config)
        self.assertTrue(any("ARTIFACT_ROLE_SUBSTITUTION:EB_RESPONSE" in item for item in errors), errors)

    def test_same_sky_independence_and_product_substitution_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["claims"]["same_sky_role"] = "INDEPENDENT_CONFIRMATION"
            config["claims"]["independent_replication"] = True
            config["product_admissions"][0]["admitted_product"] = "COMMANDER"
            errors = self._errors(config)
        self.assertTrue(any("SAME_SKY_INDEPENDENCE_FORBIDDEN" in item for item in errors), errors)
        self.assertTrue(any("PRODUCT_SUBSTITUTION_FORBIDDEN" in item for item in errors), errors)

    def test_claim_firewall_covers_admissions_and_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["product_admissions"][0]["claim"] = "Bianchi family identified"
            receipt = config["polarization"]["eb_operator"]["identity_receipt"]
            path = Path(receipt["path"])
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["metrics"]["operator_id"] = "foreground ruled out"
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            receipt["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = Path(config["inspection"]["explicit_manifest"])
            manifest.write_text("foreground ruled out\n", encoding="utf-8")
            config["inspection"]["explicit_manifest_sha256"] = hashlib.sha256(
                manifest.read_bytes()
            ).hexdigest()
            errors = self._errors(config)
        self.assertIn("PRODUCT_ADMISSION_SCHEMA_MISMATCH", errors)
        self.assertTrue(any("FORBIDDEN_CLAIM_TEXT" in item for item in errors), errors)
        self.assertIn("FORBIDDEN_CLAIM_TEXT_IN_INPUT_MANIFEST", errors)

    def test_claim_promotion_and_unregistered_claim_fields_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["claims"]["claim_promotion"] = True
            config["claims"]["Bianchi family identified"] = True
            config["claims"]["foreground ruled out"] = True
            errors = self._errors(config)
        self.assertIn("CLAIM_PROMOTION_FORBIDDEN", errors)
        self.assertIn("CLAIM_SCHEMA_MISMATCH", errors)
        self.assertTrue(any("FORBIDDEN_CLAIM_TEXT" in item for item in errors), errors)

    def test_unknown_terminal_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            _seal_all_lanes(config)
            config["terminals"][0]["terminal_state"] = "MYSTERY_SUCCESS"
            errors = self._errors(config)
        self.assertTrue(any("UNKNOWN_TERMINAL_STATE" in item for item in errors), errors)

    def test_preflight_forbids_fabricated_terminal_records(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["terminals"] = [
                {"lane": "D.9.0", "terminal_state": "SUCCEEDED_NO_CLAIM_PROMOTION"}
            ]
            errors = self._errors(config)
        self.assertIn("PREFLIGHT_TERMINALS_MUST_BE_EMPTY", errors)

    def test_final_seal_requires_each_lane_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = _base_config(root)
            _seal_all_lanes(config)
            self.assertEqual(self._errors(config), [])

            config["terminals"][-1] = copy.deepcopy(config["terminals"][0])
            errors = self._errors(config)
        self.assertTrue(any("DUPLICATE_TERMINAL_LANE" in item for item in errors), errors)
        self.assertTrue(any("FINAL_SEAL_LANE_COVERAGE_MISMATCH" in item for item in errors), errors)

    def test_final_seal_requires_executed_phase_prerequisites_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            _seal_all_lanes(config)
            config["terminals"][0]["phase_state"] = "READY"
            config["terminals"][1]["prerequisites"] = []
            config["terminals"][2]["manifest_receipt"]["sha256"] = "0" * 64
            errors = self._errors(config)
        self.assertTrue(any("FINAL_TERMINAL_NOT_EXECUTED" in item for item in errors), errors)
        self.assertTrue(any("LANE_PREREQUISITE_MISMATCH" in item for item in errors), errors)
        self.assertTrue(any("BOUND_RECEIPT_HASH_MISMATCH:LANE_MANIFEST" in item for item in errors), errors)

    def test_successful_lane_cannot_consume_failed_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            _seal_all_lanes(config)
            by_lane = {item["lane"]: item for item in config["terminals"]}
            by_lane["D.9.B"]["terminal_state"] = "PRODUCT_NOT_PRESENT"
            by_lane["D.9.C"]["terminal_state"] = "SUCCEEDED_NO_CLAIM_PROMOTION"
            errors = self._errors(config)
        self.assertTrue(any("FAILED_PREREQUISITE_CONSUMED:D.9.C" in item for item in errors), errors)

    def test_output_bearing_lane_cannot_consume_failed_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            _seal_all_lanes(config)
            by_lane = {item["lane"]: item for item in config["terminals"]}
            by_lane["D.9.B"]["terminal_state"] = "PRODUCT_NOT_PRESENT"
            by_lane["D.9.C"]["terminal_state"] = "EXPLORATORY_ONLY"
            errors = self._errors(config)
        self.assertTrue(any("FAILED_PREREQUISITE_CONSUMED:D.9.C" in item for item in errors), errors)

    def test_unknown_execution_phase_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = _base_config(Path(raw))
            config["execution_phase"] = "PARTIAL_SUCCESS"
            errors = self._errors(config)
        self.assertIn("EXECUTION_PHASE_INVALID", errors)


if __name__ == "__main__":
    unittest.main()
