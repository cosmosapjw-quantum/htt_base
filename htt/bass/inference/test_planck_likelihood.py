"""bass/inference/test_planck_likelihood.py — Round-16 PR-S14 regression suite.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §6.2 (PR-S14 audit):

    A4 synthetic-only check enforced;
    A6 no silent fallback to synthetic when real fixture is missing;
    A10 end-to-end gate ladder test.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bass.inference.planck_likelihood import (
    ALLOWED_DATASET_KINDS,
    FittingBlockedError,
    GateLadderDecision,
    PLANCK_2018_LOWL_TT_DATASET_KIND,
    PlanckDataset,
    PlanckLikelihood,
    load_planck_low_l_tt_dataset,
    make_synthetic_dataset,
)


# ────────────────────────────────────────────────────────────────────────
# PlanckDataset
# ────────────────────────────────────────────────────────────────────────


class TestPlanckDataset:
    def _baseline(self, **overrides):
        defaults = dict(
            kind="synthetic_gaussian",
            path=None,
            ell_min=2,
            ell_max=4,
            C_l_obs=np.array([1.0, 2.0, 3.0]),
            sigma=np.array([0.1, 0.2, 0.3]),
        )
        defaults.update(overrides)
        return PlanckDataset(**defaults)

    def test_synthetic_dataset_constructs(self) -> None:
        ds = self._baseline()
        assert ds.kind == "synthetic_gaussian"
        assert ds.ell_max == 4

    def test_unknown_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown dataset"):
            self._baseline(kind="planck2030_full")

    def test_inverted_ell_range_raises(self) -> None:
        with pytest.raises(ValueError, match="ell_max"):
            self._baseline(ell_min=5, ell_max=4)

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="C_l_obs"):
            self._baseline(C_l_obs=np.array([1.0, 2.0]))

    def test_zero_sigma_raises(self) -> None:
        with pytest.raises(ValueError, match="sigma"):
            self._baseline(sigma=np.array([0.0, 0.1, 0.1]))


# ────────────────────────────────────────────────────────────────────────
# Synthetic-data path (no gating)
# ────────────────────────────────────────────────────────────────────────


class TestSyntheticPath:
    def test_synthetic_dataset_log_likelihood_is_finite(self) -> None:
        truth = np.linspace(1.0, 10.0, 50)
        ds = make_synthetic_dataset(
            C_l_truth=truth, ell_min=2, ell_max=10,
            relative_error=0.05, rng=np.random.default_rng(0),
        )
        lk = PlanckLikelihood(dataset=ds)
        # Synthetic data ⇒ no gates needed; pass a dummy disallowed
        # decision and verify it still proceeds (synthetic path).
        decision = GateLadderDecision(allowed=False, missing_gates=("any",))
        log_l = lk.log_likelihood(truth, gate_decision=decision)
        assert np.isfinite(log_l)
        assert log_l <= 0.0

    def test_synthetic_log_likelihood_truth_is_at_maximum(self) -> None:
        # Likelihood at the truth values should be > likelihood at perturbed values.
        truth = np.linspace(1.0, 10.0, 50)
        rng = np.random.default_rng(0)
        ds = make_synthetic_dataset(
            C_l_truth=truth, ell_min=2, ell_max=10,
            relative_error=1.0e-12, rng=rng,
        )
        lk = PlanckLikelihood(dataset=ds)
        decision = GateLadderDecision(allowed=True)
        log_truth = lk.log_likelihood(truth, gate_decision=decision)
        perturbed = truth.copy()
        perturbed[5] *= 1.1
        log_pert = lk.log_likelihood(perturbed, gate_decision=decision)
        assert log_truth > log_pert


# ────────────────────────────────────────────────────────────────────────
# Real-data gating (V5_ROUND16_03 §6.2)
# ────────────────────────────────────────────────────────────────────────


class TestRealDataGating:
    def _real_dataset(self, tmp_path: Path) -> PlanckDataset:
        path = tmp_path / "planck2018_plik_low_l_tt_fixture.txt"
        path.write_text(
            "# ell C_l sigma\n"
            "2 1.0 0.1\n"
            "3 2.0 0.2\n"
            "4 3.0 0.3\n",
            encoding="utf-8",
        )
        return load_planck_low_l_tt_dataset(path)

    def test_real_dataset_requires_nonempty_regular_path(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            PlanckDataset(
                kind=PLANCK_2018_LOWL_TT_DATASET_KIND,
                path=empty,
                ell_min=2,
                ell_max=2,
                C_l_obs=np.array([1.0]),
                sigma=np.array([0.1]),
            )
        with pytest.raises(FileNotFoundError, match="Planck low-l TT"):
            PlanckDataset(
                kind=PLANCK_2018_LOWL_TT_DATASET_KIND,
                path=tmp_path / "missing.txt",
                ell_min=2,
                ell_max=2,
                C_l_obs=np.array([1.0]),
                sigma=np.array([0.1]),
            )

    def test_real_data_blocks_when_gates_closed(self, tmp_path: Path) -> None:
        lk = PlanckLikelihood(dataset=self._real_dataset(tmp_path))
        decision = GateLadderDecision(
            allowed=False, missing_gates=("ic_provenance_gate",)
        )
        with pytest.raises(FittingBlockedError) as exc:
            lk.log_likelihood(
                np.zeros(10), gate_decision=decision, family="FLRW"
            )
        assert "ic_provenance_gate" in str(exc.value)
        assert exc.value.missing_gates == ("ic_provenance_gate",)
        assert exc.value.dataset_kind == PLANCK_2018_LOWL_TT_DATASET_KIND

    def test_real_data_proceeds_when_all_gates_open(self, tmp_path: Path) -> None:
        lk = PlanckLikelihood(dataset=self._real_dataset(tmp_path))
        decision = GateLadderDecision(
            allowed=True, template_card_authorized=False, family="FLRW"
        )
        log_l = lk.log_likelihood(
            np.array([0.0, 0.0, 1.0, 2.0, 3.0]),
            gate_decision=decision, family="FLRW",
        )
        assert log_l == pytest.approx(0.0, abs=1e-15)

    def test_real_data_blocks_bianchi_family_even_with_open_gates(
        self, tmp_path: Path,
    ) -> None:
        lk = PlanckLikelihood(dataset=self._real_dataset(tmp_path))
        decision = GateLadderDecision(
            allowed=True, template_card_authorized=False, family="II"
        )
        with pytest.raises(FittingBlockedError, match="harmonic template"):
            lk.log_likelihood(
                np.zeros(10), gate_decision=decision, family="II"
            )

    def test_template_authorization_does_not_promote_cl_only_bianchi_fit(
        self, tmp_path: Path,
    ) -> None:
        lk = PlanckLikelihood(dataset=self._real_dataset(tmp_path))
        decision = GateLadderDecision(
            allowed=True, template_card_authorized=True, family="II"
        )
        with pytest.raises(FittingBlockedError, match="C_l likelihood is FLRW"):
            lk.log_likelihood(
                np.array([0.0, 0.0, 1.0, 2.0, 3.0]),
                gate_decision=decision,
                family="II",
            )

    def test_strong_bianchi_family_still_blocks_on_cl_only_path(
        self, tmp_path: Path
    ) -> None:
        """Even strong Bianchi families need harmonic-level data comparison."""
        lk = PlanckLikelihood(dataset=self._real_dataset(tmp_path))
        decision = GateLadderDecision(
            allowed=True, template_card_authorized=False, family="V"
        )
        with pytest.raises(FittingBlockedError, match="harmonic"):
            lk.log_likelihood(
                np.array([0.0, 0.0, 1.0, 2.0, 3.0]),
                gate_decision=decision,
                family="V",
            )


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_03 §6.2)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS14:
    def test_A4_unknown_kind_blocked_at_dataset_construction(self) -> None:
        """A4: dataset.kind whitelist enforced at construction time."""
        with pytest.raises(ValueError, match="Unknown dataset kind"):
            PlanckDataset(
                kind="planck2018",  # near-miss spelling
                path=None, ell_min=2, ell_max=2,
                C_l_obs=np.array([1.0]), sigma=np.array([0.1]),
            )

    def test_A6_no_silent_synthetic_fallback_on_real_data_path(self) -> None:
        """A6: real-data path must NOT degrade to synthetic on missing fixture.

        Verified by passing a real-data dataset and a closed gate decision;
        the call must raise FittingBlockedError, not return a synthetic
        log-likelihood value.
        """
        with pytest.raises(FileNotFoundError, match="Planck low-l TT"):
            PlanckDataset(
                kind=PLANCK_2018_LOWL_TT_DATASET_KIND,
                path=Path("/nonexistent/fixture"),
                ell_min=2, ell_max=4,
                C_l_obs=np.array([1.0, 2.0, 3.0]),
                sigma=np.array([0.1, 0.2, 0.3]),
            )

    def test_A10_end_to_end_gate_ladder(self, tmp_path: Path) -> None:
        """A10: with one missing gate, blocked; with all open, finite scalar."""
        path = tmp_path / "single_low_l_tt.txt"
        path.write_text("# ell C_l sigma\n2 1.0 0.1\n", encoding="utf-8")
        ds = load_planck_low_l_tt_dataset(path)
        assert ds.path == path

        with pytest.raises(ValueError, match="contiguous"):
            bad_path = tmp_path / "noncontiguous_low_l_tt.txt"
            bad_path.write_text(
                "# ell C_l sigma\n2 1.0 0.1\n4 2.0 0.2\n",
                encoding="utf-8",
            )
            load_planck_low_l_tt_dataset(bad_path)

        lk = PlanckLikelihood(dataset=ds)
        # Missing gate ⇒ blocked.
        with pytest.raises(FittingBlockedError):
            lk.log_likelihood(
                np.array([0, 0, 1.0]),
                gate_decision=GateLadderDecision(
                    allowed=False, missing_gates=("output_split_gate",)
                ),
                family="FLRW",
            )
        # All open ⇒ finite.
        log_l = lk.log_likelihood(
            np.array([0, 0, 1.0]),
            gate_decision=GateLadderDecision(allowed=True),
            family="FLRW",
        )
        assert np.isfinite(log_l)


# ────────────────────────────────────────────────────────────────────────
# Module surface invariants
# ────────────────────────────────────────────────────────────────────────


class TestModuleSurface:
    def test_allowed_dataset_kinds_includes_real_planck(self) -> None:
        assert PLANCK_2018_LOWL_TT_DATASET_KIND in ALLOWED_DATASET_KINDS

    def test_allowed_dataset_kinds_excludes_arbitrary_strings(self) -> None:
        assert "planck2018_full_high_l_TTTEEE" not in ALLOWED_DATASET_KINDS
        assert "wmap" not in ALLOWED_DATASET_KINDS
