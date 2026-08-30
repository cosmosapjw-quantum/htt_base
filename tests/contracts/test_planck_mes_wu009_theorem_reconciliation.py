"""Red/green contracts for the bounded PMG-WU-009 Gate-A/B work."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path
import tempfile
import unittest

from scripts.observed_runs import planck_mes_wu009_contracts as contracts


ROOT = Path(__file__).resolve().parents[2]
LEDGER = (
    ROOT
    / "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json"
)


class LedgerContractTests(unittest.TestCase):
    def test_ledger_has_exact_authority_rows_and_pending_provenance(self) -> None:
        ledger = contracts.load_ledger(LEDGER)
        diagnostic = contracts.validate_ledger(ledger)
        self.assertEqual(diagnostic.state, contracts.ContractState.PASS, diagnostic)
        self.assertEqual(len(ledger["rows"]), 78)
        self.assertEqual(
            {row["id"] for row in ledger["rows"]}, contracts.EXPECTED_ROW_IDS
        )
        self.assertEqual(ledger["authority_source"], "USER_SUPPLIED_SUMMARY")
        self.assertEqual(
            ledger["formal_proof_provenance"], "FORMAL_DOSSIER_PENDING"
        )

    def test_every_row_preserves_summary_only_release_boundary(self) -> None:
        for row in contracts.load_ledger(LEDGER)["rows"]:
            self.assertEqual(
                row["evidence_status"],
                "SUMMARY_ONLY_FORMAL_DOSSIER_PENDING",
            )
            self.assertEqual(
                row["release_status"],
                "NOT_RELEASED_FORMAL_DOSSIER_PENDING",
            )
            self.assertRegex(row["summary_proof_reference"], r"^USER_SUMMARY:P\d{2}$")
            self.assertNotIn("LOCALLY_REPLAYED", str(row))

    def test_top_level_schema_and_proof_replay_metadata_fail_closed(self) -> None:
        baseline = contracts.load_ledger(LEDGER)
        mutations = (
            ("schema_version", 999),
            ("schema_version", True),
            ("schema_version", 1.0),
            ("format", "UNKNOWN"),
            ("row_count", 77),
            ("row_count", 78.0),
            ("formal_dossier_replayed", True),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                payload = deepcopy(baseline)
                payload[field] = value
                diagnostic = contracts.validate_ledger(payload)
                self.assertEqual(diagnostic.state, contracts.ContractState.REJECT)

    def test_self_check_does_not_mask_tampered_replay_metadata(self) -> None:
        payload = contracts.load_ledger(LEDGER)
        payload["formal_dossier_replayed"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = contracts.run_self_check(path)
        self.assertEqual(result["status"], "FAILED_CONTRACT_CHECK")
        self.assertIs(result["formal_dossier_replayed"], True)


class GeometryContractTests(unittest.TestCase):
    def test_stf_cubic_bound_is_saturated_by_uniaxial_spectrum(self) -> None:
        result = contracts.stf_cubic_contract((2.0, -1.0, -1.0))
        self.assertEqual(result.state, contracts.ContractState.PASS)
        self.assertTrue(result.metrics["saturated"])
        self.assertAlmostEqual(result.metrics["absolute_cubic"], 6.0)
        self.assertAlmostEqual(result.metrics["bound"], 6.0)

    def test_generic_stratum_abstains_at_singular_krylov_matrix(self) -> None:
        generic = contracts.generic_stratum_contract(
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        )
        singular = contracts.generic_stratum_contract(
            ((1.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        )
        self.assertEqual(generic.state, contracts.ContractState.PASS)
        self.assertEqual(singular.state, contracts.ContractState.ABSTAIN)
        self.assertEqual(singular.code, "BLOCKED_BY_DEGENERATE_STRATUM")

    def test_generic_stratum_is_overflow_safe_and_scale_invariant(self) -> None:
        for scale in (1.0e-308, 1.0e308):
            with self.subTest(scale=scale):
                result = contracts.generic_stratum_contract(
                    ((scale, 0.0, 0.0), (0.0, scale, 0.0), (0.0, 0.0, scale))
                )
                self.assertEqual(result.state, contracts.ContractState.PASS)
                self.assertTrue(math.isfinite(result.metrics["relative_margin"]))
                self.assertTrue(
                    math.isfinite(result.metrics["normalized_determinant"])
                )

    def test_generic_stratum_rejects_invalid_tolerance_inputs(self) -> None:
        singular = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0))
        for tolerance in (-1.0, 0.0, math.nan, math.inf):
            with self.subTest(tolerance=tolerance):
                with self.assertRaises(ValueError):
                    contracts.generic_stratum_contract(
                        singular,
                        tolerance=tolerance,
                    )

    def test_mirror_negative_control_exposes_o3_chirality_loss(self) -> None:
        result = contracts.mirror_chirality_control(
            (1.0, 2.0, 3.0, 4.0),
            (1.0, 2.0, 3.0, 4.0),
            5.0,
            -5.0,
        )
        self.assertEqual(result.state, contracts.ContractState.PASS)
        self.assertEqual(result.code, "MIRROR_CHIRALITY_LOSS_DETECTED")


class StatisticalContractTests(unittest.TestCase):
    def test_weak_finite_ranks_are_superuniform_with_ties(self) -> None:
        result = contracts.finite_rank_superuniformity_contract((0.0, 0.0, 1.0))
        self.assertEqual(result.state, contracts.ContractState.PASS)
        self.assertEqual(
            result.metrics["pvalues"],
            (Fraction(1, 1), Fraction(1, 1), Fraction(1, 3)),
        )

    def test_decreasing_transform_swaps_loo_midrank_tail(self) -> None:
        result = contracts.decreasing_tail_swap_contract(
            (0.0, 0.0, 2.0, 5.0), (0.0, 0.0, -2.0, -5.0)
        )
        self.assertEqual(result.state, contracts.ContractState.PASS)
        self.assertTrue(result.metrics["tail_swap_verified"])

    def test_row_equivariance_and_broken_negative_control(self) -> None:
        rows = (1.0, 3.0, 8.0)

        def equivariant(values):
            return tuple(sum(abs(value - other) for other in values) for value in values)

        def privileges_first_row(values):
            return (values[0],) * len(values)

        self.assertEqual(
            contracts.row_equivariance_contract(rows, equivariant).state,
            contracts.ContractState.PASS,
        )
        broken = contracts.row_equivariance_contract(rows, privileges_first_row)
        self.assertEqual(broken.state, contracts.ContractState.REJECT)
        self.assertEqual(broken.code, "BLOCKED_BY_NON_EQUIVARIANT_ADAPTATION")

    def test_symmetric_data_dependent_selection_preserves_label_symmetry(self) -> None:
        symmetric = contracts.selection_symmetry_contract(
            (1.0, 4.0, 2.0), lambda values: values.index(max(values))
        )
        privileged = contracts.selection_symmetry_contract(
            (1.0, 4.0, 2.0), lambda values: 0
        )
        self.assertEqual(symmetric.state, contracts.ContractState.PASS)
        self.assertEqual(privileged.state, contracts.ContractState.REJECT)

    def test_conditional_e_increments_compose_but_marginals_do_not(self) -> None:
        valid = (
            contracts.EPath(0.25, (0.5, 0.0)),
            contracts.EPath(0.25, (0.5, 2.0)),
            contracts.EPath(0.25, (1.5, 0.0)),
            contracts.EPath(0.25, (1.5, 2.0)),
        )
        shared_marginal = (
            contracts.EPath(0.5, (0.0, 0.0)),
            contracts.EPath(0.5, (2.0, 2.0)),
        )
        self.assertEqual(
            contracts.conditional_e_composition_contract(valid).state,
            contracts.ContractState.PASS,
        )
        rejected = contracts.conditional_e_composition_contract(shared_marginal)
        self.assertEqual(rejected.state, contracts.ContractState.REJECT)
        self.assertEqual(rejected.code, "MARGINAL_ONLY_E_VALUE_MULTIPLICATION")


class InverseAndLikelihoodContractTests(unittest.TestCase):
    def test_boost_response_condition_bound_is_sharp(self) -> None:
        result = contracts.boost_response_condition_contract((5.0, -4.0, -1.0))
        self.assertEqual(result.state, contracts.ContractState.PASS)
        self.assertAlmostEqual(result.metrics["condition_number"], 5.0 / 3.0)
        self.assertTrue(result.metrics["saturated"])

    def test_positive_quadratic_requires_strict_domain_and_absolute_t(self) -> None:
        accepted = contracts.positive_quadratic_domain_contract(
            certified_minimum=0.25,
            has_absolute_temperature=True,
            includes_monopole=True,
            includes_dipole=True,
        )
        boundary = contracts.positive_quadratic_domain_contract(
            certified_minimum=0.0,
            has_absolute_temperature=True,
            includes_monopole=True,
            includes_dipole=True,
        )
        ablated = contracts.positive_quadratic_domain_contract(
            certified_minimum=0.25,
            has_absolute_temperature=False,
            includes_monopole=False,
            includes_dipole=False,
        )
        self.assertEqual(accepted.state, contracts.ContractState.PASS)
        self.assertEqual(boundary.state, contracts.ContractState.REJECT)
        self.assertEqual(ablated.state, contracts.ContractState.ABSTAIN)
        self.assertEqual(
            ablated.code,
            "NOT_ADMISSIBLE_MISSING_ABSOLUTE_T_MONOPOLE_DIPOLE",
        )

    def test_inverse_square_fit_is_refused_for_untruncated_direct_t_noise(self) -> None:
        rejected = contracts.temperature_likelihood_contract(
            contracts.TemperatureNoiseModel.UNTRUNCATED_GAUSSIAN_DIRECT_T,
            contracts.FitObjective.UNWEIGHTED_INVERSE_SQUARE,
        )
        accepted = contracts.temperature_likelihood_contract(
            contracts.TemperatureNoiseModel.UNTRUNCATED_GAUSSIAN_DIRECT_T,
            contracts.FitObjective.GAUSSIAN_DIRECT_T_WEIGHTED_LEAST_SQUARES,
        )
        self.assertEqual(rejected.state, contracts.ContractState.REJECT)
        self.assertEqual(rejected.code, "INVERSE_SQUARE_LIKELIHOOD_REFUSED")
        self.assertEqual(accepted.state, contracts.ContractState.PASS)

    def test_bounded_body_is_not_silently_treated_as_cone(self) -> None:
        result = contracts.projection_glrt_domain_contract(
            contracts.ProjectionDomain.BOUNDED_CONVEX_BODY
        )
        self.assertEqual(result.state, contracts.ContractState.REJECT)
        self.assertEqual(result.code, "BOUNDED_BODY_IS_NOT_A_CONE")
        self.assertEqual(result.metrics["interval_counterexample_lr"], 3.0)
        self.assertEqual(result.metrics["interval_counterexample_projection_sq"], 1.0)

    def test_unknown_projection_domains_fail_closed(self) -> None:
        for domain in (None, "CLOSED_CONVEX_CONE"):
            with self.subTest(domain=domain):
                result = contracts.projection_glrt_domain_contract(domain)
                self.assertEqual(result.state, contracts.ContractState.REJECT)
                self.assertEqual(result.code, "INVALID_PROJECTION_DOMAIN")


if __name__ == "__main__":
    unittest.main()
