"""COMMON-D tests — bulkflow_likelihood (INDEPENDENT_TRACKS_PLAN §3.1)."""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

from common.bulkflow_likelihood import (
    BulkFlowConfig,
    BulkFlowLikelihood,
    make_prior_transform,
    prior_transform,
    run_dynesty,
)
from common.bulkflow_estimator import wls_bulk_flow
from common.contracts import DynestyResult
from common.sky_geometry import lb_to_unitvec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _injected_likelihood(
    V_true: np.ndarray,
    *,
    n: int = 300,
    sigma_u: float = 40.0,
    seed: int = 0,
    sigma_star: float = 0.0,
) -> tuple[BulkFlowLikelihood, np.ndarray, np.ndarray]:
    """Build a BulkFlowLikelihood on an isotropic injected-dipole catalogue.

    Returns the likelihood plus ``(n_hat, u)`` for downstream checks.
    """
    rng = np.random.default_rng(seed)
    cos_b = rng.uniform(-1.0, 1.0, size=n)
    b_deg = np.rad2deg(np.arcsin(cos_b))
    l_deg = rng.uniform(0.0, 360.0, size=n)
    n_hat = lb_to_unitvec(l_deg, b_deg)
    u = n_hat @ V_true + rng.normal(0.0, sigma_u, size=n)
    sigma = np.full(n, sigma_u, dtype=float)
    like = BulkFlowLikelihood(
        n_hat=n_hat,
        u=u,
        sigma=sigma,
        w_native=np.ones(n),
        w_selection=np.ones(n),
        sigma_star_kmps=sigma_star,
    )
    return like, n_hat, u


# ---------------------------------------------------------------------------
# §1 — BulkFlowConfig invariants
# ---------------------------------------------------------------------------

class TestBulkFlowConfig:
    def test_defaults_are_valid(self):
        cfg = BulkFlowConfig()
        assert cfg.V_max_kmps == 2000.0
        assert cfg.sampler == "static"

    @pytest.mark.parametrize("field,bad", [
        ("V_max_kmps", 0.0),
        ("V_max_kmps", -10.0),
        ("sigma_star_kmps", -1.0),
        ("nlive", 0),
        ("dlogz", 0.0),
    ])
    def test_rejects_out_of_range_numerics(self, field, bad):
        kwargs = {field: bad}
        with pytest.raises(ValueError):
            BulkFlowConfig(**kwargs)

    def test_rejects_unknown_sampler(self):
        with pytest.raises(ValueError, match="sampler"):
            BulkFlowConfig(sampler="gibbs")


# ---------------------------------------------------------------------------
# §2 — prior_transform
# ---------------------------------------------------------------------------

class TestPriorTransform:
    def test_unit_cube_center_maps_to_zero(self):
        np.testing.assert_allclose(
            prior_transform(np.full(3, 0.5), V_max_kmps=1000.0), np.zeros(3)
        )

    def test_unit_cube_corner_maps_to_pm_Vmax(self):
        np.testing.assert_allclose(
            prior_transform(np.zeros(3), V_max_kmps=500.0), -500.0 * np.ones(3)
        )
        np.testing.assert_allclose(
            prior_transform(np.ones(3), V_max_kmps=500.0), +500.0 * np.ones(3)
        )

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError, match="shape"):
            prior_transform(np.array([0.5, 0.5]))

    def test_rejects_nonpositive_Vmax(self):
        with pytest.raises(ValueError, match="V_max"):
            prior_transform(np.full(3, 0.5), V_max_kmps=0.0)

    def test_make_prior_transform_bind(self):
        pt = make_prior_transform(1500.0)
        np.testing.assert_allclose(pt(np.full(3, 0.5)), np.zeros(3))
        np.testing.assert_allclose(pt(np.zeros(3)), -1500.0 * np.ones(3))


# ---------------------------------------------------------------------------
# §3 — Likelihood invariants and physics
# ---------------------------------------------------------------------------

class TestBulkFlowLikelihood:
    def test_construction_requires_unit_vectors(self):
        with pytest.raises(ValueError, match="unit vectors"):
            BulkFlowLikelihood(
                n_hat=np.array([[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]),
                u=np.zeros(2),
                sigma=np.ones(2),
                w_native=np.ones(2),
                w_selection=np.ones(2),
            )

    def test_construction_requires_positive_sigma(self):
        with pytest.raises(ValueError, match="sigma"):
            BulkFlowLikelihood(
                n_hat=np.eye(3)[:2],
                u=np.zeros(2),
                sigma=np.array([1.0, -1.0]),
                w_native=np.ones(2),
                w_selection=np.ones(2),
            )

    def test_requires_enough_active_sources(self):
        V_true = np.array([100.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=20)
        # Zero-out all but 3 selection weights — should raise.
        with pytest.raises(ValueError, match="active sources"):
            BulkFlowLikelihood(
                n_hat=like.n_hat,
                u=like.u,
                sigma=like.sigma,
                w_native=like.w_native,
                w_selection=np.concatenate([np.ones(3), np.zeros(17)]),
            )

    def test_zero_weighted_sources_are_dropped(self):
        V_true = np.array([120.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=200)
        # Drop half via selection weight.
        w_sel = like.w_selection.copy()
        w_sel[::2] = 0.0
        reduced = BulkFlowLikelihood(
            n_hat=like.n_hat,
            u=like.u,
            sigma=like.sigma,
            w_native=like.w_native,
            w_selection=w_sel,
        )
        assert reduced.n_active == 100

    def test_log_likelihood_maximised_near_truth(self):
        V_true = np.array([370.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=400, sigma_u=30.0, seed=42)
        # WLS point estimate should be close to truth (and to the posterior mode).
        fit = wls_bulk_flow(
            like.n_hat,
            like.u,
            sigma=like.sigma,
            w_native=like.w_native,
            w_selection=like.w_selection,
        )
        ll_truth = like(V_true)
        ll_zero = like(np.zeros(3))
        ll_fit = like(fit.V_hat)
        # Truth beats zero, and WLS mode is at least as good as truth.
        assert ll_truth > ll_zero
        assert ll_fit >= ll_truth - 1.0

    def test_log_likelihood_is_quadratic_in_V(self):
        """For a linear-Gaussian model the log-likelihood is a quadratic in
        :math:`\\mathbf V`; in particular symmetric perturbations about the
        WLS mode must shift the log-likelihood by the same amount."""
        V_true = np.array([0.0, 250.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=600, sigma_u=20.0, seed=3)
        fit = wls_bulk_flow(
            like.n_hat,
            like.u,
            sigma=like.sigma,
            w_native=like.w_native,
            w_selection=like.w_selection,
        )
        V0 = fit.V_hat
        delta = np.array([10.0, 0.0, 0.0])
        ll_plus = like(V0 + delta)
        ll_minus = like(V0 - delta)
        np.testing.assert_allclose(ll_plus, ll_minus, atol=1e-6)

    def test_sigma_star_adds_in_quadrature(self):
        """Increasing ``sigma_star`` at fixed data must lower the log-likelihood
        amplitude contribution (larger effective variance → flatter posterior)."""
        V_true = np.array([200.0, 0.0, 0.0])
        like_0, n_hat, u = _injected_likelihood(V_true, n=200, sigma_u=30.0, seed=5)
        like_s = BulkFlowLikelihood(
            n_hat=n_hat,
            u=u,
            sigma=np.full(u.size, 30.0),
            w_native=np.ones(u.size),
            w_selection=np.ones(u.size),
            sigma_star_kmps=40.0,
        )
        # At a far-from-truth V, the penalty is smaller with larger σ_eff.
        V_bad = np.array([1000.0, 0.0, 0.0])
        ll0 = like_0(V_bad)
        lls = like_s(V_bad)
        assert lls > ll0

    def test_log_likelihood_rejects_wrong_shape(self):
        V_true = np.array([100.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=60)
        with pytest.raises(ValueError, match="shape"):
            like(np.array([1.0, 2.0]))


# ---------------------------------------------------------------------------
# §4 — Dynesty adapter via injected stub
# ---------------------------------------------------------------------------

class _StubResults:
    def __init__(self, samples, logwt, logz, ncall):
        self.samples = samples
        self.logwt = logwt
        self.logz = np.asarray([logz])
        self.ncall = ncall


class _StubSampler:
    def __init__(self, *, loglikelihood, prior_transform, ndim, nlive, rstate):
        self.loglikelihood = loglikelihood
        self.prior_transform = prior_transform
        self.ndim = ndim
        self.nlive = nlive
        self.rstate = rstate

    def run_nested(self, dlogz, print_progress):
        rng = self.rstate
        n = 50
        u = rng.uniform(0.0, 1.0, size=(n, self.ndim))
        samples = np.array([self.prior_transform(row) for row in u])
        logl = np.array([self.loglikelihood(row) for row in samples])
        logwt = logl - logl.max()        # crude stub weights
        self.results = _StubResults(
            samples=samples,
            logwt=logwt,
            logz=float(logl.max()),
            ncall=n,
        )


def _stub_dynesty_module():
    return SimpleNamespace(NestedSampler=_StubSampler,
                           DynamicNestedSampler=_StubSampler)


class TestRunDynestyAdapter:
    def test_run_dynesty_returns_DynestyResult(self):
        V_true = np.array([300.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=200, seed=7)
        cfg = BulkFlowConfig(V_max_kmps=1500.0, nlive=50, seed=11)
        out = run_dynesty(
            like,
            make_prior_transform(cfg.V_max_kmps),
            cfg,
            dynesty_module=_stub_dynesty_module(),
        )
        assert isinstance(out, DynestyResult)
        assert out.samples.shape == (50, 3)
        assert out.logwt.shape == (50,)
        assert math.isfinite(out.logz)
        assert out.ncall == 50
        assert out.config["V_max_kmps"] == 1500.0

    def test_run_dynesty_raises_without_module_when_dynesty_absent(self):
        """When ``dynesty_module`` is not injected and real dynesty is not
        installed, :func:`run_dynesty` must surface a clear RuntimeError
        instead of an opaque ImportError far from the call site."""
        import importlib
        V_true = np.array([100.0, 0.0, 0.0])
        like, *_ = _injected_likelihood(V_true, n=50)
        cfg = BulkFlowConfig(nlive=25)
        try:
            importlib.import_module("dynesty")
        except ImportError:
            with pytest.raises(RuntimeError, match="dynesty"):
                run_dynesty(like, make_prior_transform(cfg.V_max_kmps), cfg)
        else:
            pytest.skip("dynesty installed — RuntimeError path not exercised")
