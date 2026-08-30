from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from scripts.paper.planck_mes_wu009_claim_boundary import (
    Wu009ClaimBoundaryError,
    load_wu009_claim_boundary,
    require_paper_regeneration_authority,
    validate_wu009_claim_boundary_payloads,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = (
    REPO_ROOT
    / "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json"
)
RECONCILIATION = (
    REPO_ROOT
    / "docs/generated/planck_mes_wu009_reconciliation/reconciliation.json"
)
TERMINAL = REPO_ROOT / "docs/generated/planck_mes_wu009_reconciliation/terminal.json"
BUILDER = REPO_ROOT / "scripts/paper/build_planck_mes_first_paper.py"
STATUS = (
    REPO_ROOT
    / "docs/research_program/post_pr327/planck_mes_wu009_implementation_status.json"
)
PACKAGE_INDEX = (
    REPO_ROOT
    / "docs/codex_handoff/planck_mes_pmg_wu009_full_replay_local_execution/PACKAGE_INDEX.yaml"
)


def _payloads() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(
        json.loads(path.read_text(encoding="utf-8"))
        for path in (LEDGER, RECONCILIATION, TERMINAL)
    )  # type: ignore[return-value]


class Wu009ClaimBoundaryTests(unittest.TestCase):
    def test_valid_boundary_exposes_only_corrected_semantics(self) -> None:
        boundary = load_wu009_claim_boundary(LEDGER, RECONCILIATION, TERMINAL)

        self.assertEqual(boundary["format"], "PLANCK_MES_WU009_CLAIM_BOUNDARY_V1")
        ledger = boundary["ledger"]
        self.assertEqual(ledger["row_count"], 78)
        self.assertEqual(
            ledger["verdict_counts"],
            {
                "CORRECTED": 5,
                "PROVED": 61,
                "REFUTED": 5,
                "STRENGTHENED": 5,
                "UNDEFINED": 2,
            },
        )
        self.assertEqual(ledger["corrected_ids"], ["A03", "B21", "C14", "E02", "E06"])
        self.assertEqual(ledger["refuted_ids"], ["A10", "A11", "C07", "D08", "E15"])
        self.assertEqual(ledger["undefined_ids"], ["C18", "E05"])
        self.assertEqual(ledger["formal_proof_provenance"], "FORMAL_DOSSIER_PENDING")

        semantics = boundary["corrected_semantics"]
        self.assertIn("joint exchangeability", semantics["finite_rank"])
        self.assertIn("row-equivariant", semantics["finite_rank"])
        self.assertIn("upper/lower tail swap", semantics["decreasing_transformations"])
        self.assertIn("representation", semantics["positive_quadratic_inverse"])
        self.assertIn("absolute positive temperature", semantics["positive_quadratic_inverse"])
        self.assertIn("same-sky robustness", semantics["component_products_and_splits"])
        self.assertIn("matched dependence-preserving polarization null", semantics["polarization_rank_prerequisite"])
        self.assertEqual(
            semantics["cross_field_joint_conditional_diagnostics"], "EXPLORATORY_ONLY"
        )
        self.assertIn("cannot generally be multiplied", semantics["shared_data_e_values"])
        self.assertEqual(
            semantics["claim_ceiling"], "PRE_NATIVE_ATLAS_CONDITIONAL_MORPHOLOGY_ONLY"
        )

        historical = boundary["historical_results"]
        self.assertEqual(historical["WU006"]["family_rank"], "27/301")
        self.assertEqual(historical["WU006"]["local_ranks"], {"R_v0": "4/301", "R_v2": "4/301"})
        self.assertEqual(historical["WU007"]["null_sensitivity_ranks"], ["61/1000", "55/1000"])
        self.assertEqual(historical["WU008"]["scope"], "OBSERVATION_BLIND_REGISTERED_200_REFERENCE_METHOD_POWER")
        self.assertFalse(boundary["claim_promotion"])
        self.assertFalse(boundary["new_observed_rank"])
        self.assertFalse(boundary["paper_regeneration"]["authorized"])

    def test_exact_source_identity_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied = []
            for source in (LEDGER, RECONCILIATION, TERMINAL):
                target = root / source.name
                target.write_bytes(source.read_bytes())
                copied.append(target)
            copied[0].write_bytes(copied[0].read_bytes() + b"\n")
            with self.assertRaisesRegex(Wu009ClaimBoundaryError, "identity mismatch"):
                load_wu009_claim_boundary(*copied)

    def test_semantic_mutations_fail_closed(self) -> None:
        ledger, reconciliation, terminal = _payloads()
        mutations = []

        mutated = deepcopy(ledger)
        mutated["formal_dossier_replayed"] = True
        mutations.append(("formal replay promotion", mutated, reconciliation, terminal))

        mutated = deepcopy(ledger)
        next(row for row in mutated["rows"] if row["id"] == "A03")[
            "replacement_statement"
        ] = "O(3)-only invariants are complete for proper rotations."
        mutations.append(("O(3) completeness", mutated, reconciliation, terminal))

        mutated = deepcopy(ledger)
        next(row for row in mutated["rows"] if row["id"] == "C07")[
            "replacement_statement"
        ] = "An orthogonal residual makes beta nonidentifiable."
        mutations.append(("orthogonal nuisance promotion", mutated, reconciliation, terminal))

        mutated = deepcopy(ledger)
        next(row for row in mutated["rows"] if row["id"] == "E06")[
            "replacement_statement"
        ] = "Wasserstein distance unconditionally controls event probabilities."
        mutations.append(("unconditional Wasserstein", mutated, reconciliation, terminal))

        mutated = deepcopy(terminal)
        mutated["claim_promotion"] = True
        mutations.append(("claim promotion", ledger, reconciliation, mutated))

        mutated = deepcopy(reconciliation)
        mutated["observed_result"]["rank"] = "1/301"
        mutated["observed_result"]["computed"] = True
        mutations.append(("new observed rank", ledger, mutated, terminal))

        mutated = deepcopy(reconciliation)
        mutated["historical_results"]["WU007"]["interpretation"] = "INDEPENDENT_REPLICATION"
        mutations.append(("same-sky replication", ledger, mutated, terminal))

        for label, ledger_value, reconciliation_value, terminal_value in mutations:
            with self.subTest(label=label):
                with self.assertRaises(Wu009ClaimBoundaryError):
                    validate_wu009_claim_boundary_payloads(
                        ledger_value, reconciliation_value, terminal_value
                    )

    def test_paper_regeneration_authority_fails_closed(self) -> None:
        boundary = load_wu009_claim_boundary(LEDGER, RECONCILIATION, TERMINAL)
        with self.assertRaisesRegex(
            Wu009ClaimBoundaryError, "GATE_E_FROZEN_SUCCESSOR"
        ):
            require_paper_regeneration_authority(boundary)

        forged = deepcopy(boundary)
        forged["paper_regeneration"]["authorized"] = True
        with self.assertRaises(Wu009ClaimBoundaryError):
            require_paper_regeneration_authority(forged)

        fully_forged = deepcopy(boundary)
        fully_forged["paper_regeneration"] = {
            "authorized": True,
            "state": "AUTHORIZED_BY_GATE_E_FROZEN_SUCCESSOR",
            "required_binding": "GATE_E_FROZEN_SUCCESSOR",
            "gate_e_binding": {
                "state": "GATE_E_FROZEN_SUCCESSOR",
                "all_local_gates_terminal": True,
                "sha256": "1" * 64,
            },
        }
        with self.assertRaisesRegex(Wu009ClaimBoundaryError, "current V1 boundary"):
            require_paper_regeneration_authority(fully_forged)

    def test_builder_validation_cli_avoids_legacy_obsstat_and_writes_nothing(self) -> None:
        before = {
            path: path.read_bytes()
            for path in (
                REPO_ROOT / "papers/planck_mes_first_observation/main.tex",
                REPO_ROOT / "docs/generated/planck_mes_first_paper/analysis_summary.json",
            )
        }
        completed = subprocess.run(
            [sys.executable, str(BUILDER), "--validate-wu009-claim-boundary"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["status"], "PASS_WU009_CLAIM_BOUNDARY")
        self.assertEqual(
            receipt["paper_regeneration_state"],
            "BLOCKED_UNTIL_GATE_E_FROZEN_SUCCESSOR",
        )
        self.assertFalse(receipt["claim_promotion"])
        self.assertFalse(receipt["new_observed_rank"])
        self.assertNotIn("obsstat", completed.stderr)
        for path, expected in before.items():
            self.assertEqual(path.read_bytes(), expected)

    def test_status_and_handoff_bind_the_delivery_without_authorizing_paper(self) -> None:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        self.assertEqual(status["theorem_dossier_state"], "FORMAL_DOSSIER_PENDING")
        self.assertEqual(status["gate_d"]["state"], "LOCAL_EXECUTION_REQUIRED")
        self.assertEqual(status["gate_d9"]["state"], "LOCAL_EXECUTION_REQUIRED")
        self.assertEqual(
            status["empirical_inverse_state"],
            "NOT_ADMISSIBLE_UNTIL_ABSOLUTE_T_MONOPOLE_DIPOLE_VERIFIED",
        )
        self.assertEqual(
            status["paper_a_regeneration"]["state"],
            "BLOCKED_UNTIL_GATE_E_FROZEN_SUCCESSOR",
        )
        self.assertFalse(status["paper_outputs_regenerated"])
        self.assertFalse(status["claim_promotion"])

        package = yaml.safe_load(PACKAGE_INDEX.read_text(encoding="utf-8"))
        integration = package["paper_a_delivery_integration"]
        self.assertEqual(
            integration["state"], "BLOCKED_UNTIL_GATE_E_FROZEN_SUCCESSOR"
        )
        self.assertFalse(integration["claim_promotion"])
        for relative, record in integration["files"].items():
            actual = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, record["sha256"], relative)
        for relative, expected in integration["sealed_authority"].items():
            actual = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
