from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.observed_runs import run_planck_mes_wu009_reconciliation as reconciliation


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FILES = {
    "artifact_manifest.json",
    "authority_receipt.json",
    "contract_receipt.json",
    "reconciliation.json",
    "terminal.json",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlanckMesWu009ReconciliationTests(unittest.TestCase):
    def _generate(self, destination: Path) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/observed_runs/run_planck_mes_wu009_reconciliation.py"),
                "--output",
                str(destination),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_generation_is_deterministic_manifest_bound_and_map_free(self) -> None:
        with tempfile.TemporaryDirectory() as first_raw, tempfile.TemporaryDirectory() as second_raw:
            first = Path(first_raw) / "successor"
            second = Path(second_raw) / "successor"
            self._generate(first)
            self._generate(second)

            self.assertEqual({path.name for path in first.iterdir()}, EXPECTED_FILES)
            self.assertEqual({path.name for path in second.iterdir()}, EXPECTED_FILES)
            for name in EXPECTED_FILES:
                self.assertEqual(first.joinpath(name).read_bytes(), second.joinpath(name).read_bytes())
                self.assertTrue(first.joinpath(name).read_bytes().endswith(b"\n"))

            manifest = json.loads(first.joinpath("artifact_manifest.json").read_text())
            self.assertEqual(set(manifest["successor_outputs"]), EXPECTED_FILES - {"artifact_manifest.json"})
            for name, entry in manifest["successor_outputs"].items():
                self.assertEqual(entry["sha256"], _sha256(first / name))
            self.assertEqual(set(manifest["predecessor_inputs"]), set(reconciliation.PREDECESSOR_HASHES))
            self.assertEqual(
                manifest["implementation_inputs"],
                {
                    "scripts/observed_runs/run_planck_mes_wu009_reconciliation.py": {
                        "sha256": _sha256(
                            REPO_ROOT
                            / "scripts/observed_runs/run_planck_mes_wu009_reconciliation.py"
                        )
                    }
                },
            )

            receipt = json.loads(first.joinpath("reconciliation.json").read_text())
            self.assertFalse(receipt["observed_result"]["computed"])
            self.assertIsNone(receipt["observed_result"]["rank"])
            self.assertEqual(receipt["observed_result"]["state"], "NO_ADMISSIBLE_NEW_RESULT")
            self.assertEqual(receipt["overall_state"], "SUCCEEDED_NO_CLAIM_PROMOTION")

            terminal = json.loads(first.joinpath("terminal.json").read_text())
            self.assertEqual(
                terminal["bounded_implementation_review"],
                {
                    "state": "PENDING_INDEPENDENT_TASK2_REVIEW",
                    "P0_remaining": None,
                    "P1_remaining": None,
                },
            )

    def test_runtime_authorities_are_committed_portable_inputs(self) -> None:
        for relative in reconciliation.AUTHORITY_HASHES:
            self.assertFalse(relative.startswith(".superpowers/"), relative)
            self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_historical_results_and_stale_state_are_preserved_without_rewrite(self) -> None:
        protected_before = {
            path: _sha256(REPO_ROOT / path) for path in reconciliation.PREDECESSOR_HASHES
        }
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "successor"
            self._generate(destination)
            payload = json.loads(destination.joinpath("reconciliation.json").read_text())

        wu006 = payload["historical_results"]["WU006"]
        self.assertEqual(wu006["family_rank"], "27/301")
        self.assertEqual(wu006["local_ranks"], {"R_v0": "4/301", "R_v2": "4/301"})
        self.assertNotEqual(wu006["family_rank"], wu006["local_ranks"]["R_v0"])
        wu007 = payload["historical_results"]["WU007"]
        self.assertEqual(wu007["null_sensitivity_ranks"], ["61/1000", "55/1000"])
        self.assertEqual(wu007["interpretation"], "NULL_POOL_SENSITIVITY_NOT_INDEPENDENT_REPLICATION")
        wu008 = payload["historical_results"]["WU008"]
        self.assertEqual(wu008["reviewed_terminal_state"], "SUCCEEDED")
        self.assertEqual(wu008["embedded_result_state"], "EXECUTED_PENDING_REVIEW")
        self.assertEqual(wu008["reconciliation"], "STALE_EMBEDDED_PRE_TERMINAL_SUPERSEDED_BY_REVIEWED_TERMINAL")
        self.assertEqual(wu008["scope"], "OBSERVATION_BLIND_REGISTERED_200_REFERENCE_METHOD_POWER")
        self.assertEqual(
            protected_before,
            {path: _sha256(REPO_ROOT / path) for path in reconciliation.PREDECESSOR_HASHES},
        )

    def test_contracts_and_unavailable_lanes_are_typed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "successor"
            self._generate(destination)
            contracts = json.loads(destination.joinpath("contract_receipt.json").read_text())
            receipt = json.loads(destination.joinpath("reconciliation.json").read_text())

        self.assertEqual(contracts["status"], "SUCCEEDED_NO_CLAIM_PROMOTION")
        self.assertTrue(all(item["matched_expectation"] for item in contracts["checks"].values()))
        self.assertEqual(receipt["lanes"]["committed_carrier_gate_c"], "NOT_IDENTIFIED_FROM_COMMITTED_CARRIER")
        self.assertEqual(receipt["lanes"]["formal_p01_p27"], "BLOCKED_BY_MISSING_THEOREM_DOSSIER")
        for lane in ("raw_replay", "cas_replay", "iqu_eb_replay"):
            self.assertEqual(receipt["lanes"][lane], "LOCAL_ONLY_NOT_EXECUTED")

    def test_output_rejects_declared_raw_root_and_committed_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            raw_root = Path(raw).resolve()
            with self.assertRaises(ValueError):
                reconciliation.generate_reconciliation(raw_root / "child", raw_roots=(raw_root,))

        protected = REPO_ROOT / "docs/generated/planck_mes_irrep_injection_power"
        with self.assertRaises(ValueError):
            reconciliation.generate_reconciliation(protected / "wu009-overwrite")

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts/observed_runs/run_planck_mes_wu009_reconciliation.py"),
                "--check",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
