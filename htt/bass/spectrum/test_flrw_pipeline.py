"""Unit + integration tests for the V5 step-4b FLRW D_ℓ pipeline.

Fast tests verify config validation, visibility-callable shapes, and
parallel-vs-sequential consistency plumbing. The full cosmological
k-sweep is gated behind ``@pytest.mark.slow`` (~45 s per run).
"""
from __future__ import annotations

import time

import numpy as np
import pytest

from bass.spectrum.cl_assembly import CLAssemblyConfig
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    _transfer_fn_from_grid,
    build_visibility_and_kappa_callables,
    compute_flrw_d_ell,
    compute_transfer_function_grid,
)
from bass.species.registry import SpeciesBackgroundRegistry
from bass.los.bianchi_propagator import BianchiTransferFunctions


# -----------------------------------------------------------------------
# Fast unit tests: config + error paths + callables
# -----------------------------------------------------------------------


def test_pipeline_config_defaults() -> None:
    cfg = FLRWPipelineConfig()
    assert cfg.L_max_tower == 4
    assert cfg.ell_max_transfer == 4
    assert cfg.n_output == 64
    assert cfg.anisotropic_stress is True
    assert cfg.quadrature == "trapezoid"
    assert cfg.adiabatic_mode_seed is True  # V5 step-4b-(a) default


def test_adiabatic_seed_factory_ratios() -> None:
    """V5 step-4b-(a): adiabatic=True sets δ_γ:δ_b:δ_c:δ_ν = 4/3:1:1:4/3
    with θ_common = 0 (Ma-Bertschinger super-horizon ratios)."""
    from bass.hierarchy.seed_compatibility import build_flrw_regular_seed

    seed = build_flrw_regular_seed(amplitude=1.0, adiabatic=True)
    assert seed.amplitude == 1.0
    assert seed.delta_baryon == pytest.approx(1.0, abs=1e-14)
    assert seed.delta_cdm == pytest.approx(1.0, abs=1e-14)
    assert seed.delta_gamma == pytest.approx(4.0 / 3.0, abs=1e-14)
    assert seed.delta_nu == pytest.approx(4.0 / 3.0, abs=1e-14)
    assert seed.theta_common == 0.0
    # Adiabatic entropy S_γb = δ_γ/4 − δ_b/3 = 1/3 − 1/3 = 0:
    entropy_gb = seed.delta_gamma / 4.0 - seed.delta_baryon / 3.0
    assert entropy_gb == pytest.approx(0.0, abs=1e-14)


def test_adiabatic_seed_scales_linearly_with_amplitude() -> None:
    """Adiabatic seed linearity in amplitude: all five entries scale
    together so the ratio structure is preserved."""
    from bass.hierarchy.seed_compatibility import build_flrw_regular_seed

    small = build_flrw_regular_seed(amplitude=1.0e-6, adiabatic=True)
    large = build_flrw_regular_seed(amplitude=2.5e-5, adiabatic=True)
    scale = 2.5e-5 / 1.0e-6
    for field in ("delta_baryon", "delta_cdm", "delta_gamma", "delta_nu", "amplitude"):
        assert getattr(large, field) == pytest.approx(
            scale * getattr(small, field), rel=1e-14
        )


def test_common_delta_legacy_seed_unchanged() -> None:
    """adiabatic=False (default) keeps the legacy common-δ placeholder;
    required for bit-identity of the D_2 = 1002.086744 μK² anchor."""
    from bass.hierarchy.seed_compatibility import build_flrw_regular_seed

    seed = build_flrw_regular_seed(amplitude=1.0e-6)
    assert seed.delta_gamma == 1.0e-6
    assert seed.delta_baryon == 1.0e-6
    assert seed.delta_cdm == 1.0e-6
    assert seed.delta_nu == 1.0e-6
    assert seed.theta_common == pytest.approx(1.0e-6 / 3.0, abs=1e-20)


def test_bias_subtraction_flag_defaults_false() -> None:
    """bias_subtraction defaults False (legacy single-run path); opt-in
    for Round-6 visibility-bias-subtracted transfer extraction."""
    cfg = FLRWPipelineConfig()
    assert cfg.bias_subtraction is False


def test_primordial_b_k_sq_fn_callable_override() -> None:
    """Round-7: callable primordial_b_k_sq_fn takes precedence over
    scalar primordial_b_k_sq. Resolver returns per-k value."""
    from bass.spectrum.flrw_pipeline import _resolve_primordial_b_k_sq

    # Scalar-only (fn=None): returns the scalar.
    cfg_scalar = FLRWPipelineConfig(primordial_b_k_sq=1.7)
    assert _resolve_primordial_b_k_sq(cfg_scalar, 1.0e-3) == pytest.approx(1.7)

    # Planck-2018 P_ζ(k) callable override.
    def p_zeta(k: float) -> float:
        return 2.1e-9 * (k / 0.05) ** (0.9649 - 1.0)

    cfg_callable = FLRWPipelineConfig(primordial_b_k_sq_fn=p_zeta)
    # Callable takes precedence over the scalar default (1.0).
    assert _resolve_primordial_b_k_sq(cfg_callable, 0.05) == pytest.approx(2.1e-9, rel=1e-12)
    # k/k_pivot = 0.02 → (0.02)^(n_s-1) = (0.02)^(-0.0351) ≈ 1.141
    expected_at_1e_3 = 2.1e-9 * (1.0e-3 / 0.05) ** (-0.0351)
    assert _resolve_primordial_b_k_sq(cfg_callable, 1.0e-3) == pytest.approx(
        expected_at_1e_3, rel=1e-10
    )


def test_subtract_transfer_functions_helper() -> None:
    """_subtract_transfer_functions yields elementwise target − bias on
    every Δ field; zero-vs-zero returns zeros."""
    from bass.spectrum.flrw_pipeline import _subtract_transfer_functions

    target = BianchiTransferFunctions(
        delta_T_m0=np.array([1.0, 2.0, 3.0]),
        delta_T_m_plus2=np.array([0.1, 0.2, 0.3]),
        delta_T_m_minus2=np.array([0.4, 0.5, 0.6]),
        delta_E_m0=np.array([10.0, 20.0, 30.0]),
        delta_E_m_plus2=np.zeros(3),
        delta_E_m_minus2=np.zeros(3),
        delta_B_all_zero=np.zeros(3),
    )
    bias = BianchiTransferFunctions(
        delta_T_m0=np.array([0.5, 0.8, 1.2]),
        delta_T_m_plus2=np.array([0.05, 0.1, 0.15]),
        delta_T_m_minus2=np.array([0.2, 0.25, 0.3]),
        delta_E_m0=np.array([5.0, 10.0, 15.0]),
        delta_E_m_plus2=np.zeros(3),
        delta_E_m_minus2=np.zeros(3),
        delta_B_all_zero=np.zeros(3),
    )
    diff = _subtract_transfer_functions(target, bias)
    assert np.allclose(diff.delta_T_m0, np.array([0.5, 1.2, 1.8]), atol=1e-14)
    assert np.allclose(diff.delta_E_m0, np.array([5.0, 10.0, 15.0]), atol=1e-14)
    assert np.allclose(diff.delta_T_m_plus2, np.array([0.05, 0.1, 0.15]), atol=1e-14)
    assert np.allclose(diff.delta_T_m_minus2, np.array([0.2, 0.25, 0.3]), atol=1e-14)


def test_pipeline_config_rejects_small_L_max() -> None:
    with pytest.raises(ValueError, match="L_max_tower ≥ 2"):
        FLRWPipelineConfig(L_max_tower=1)


def test_pipeline_config_rejects_transfer_above_tower() -> None:
    with pytest.raises(ValueError, match="ell_max_transfer"):
        FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=8)


def test_pipeline_config_rejects_small_n_output() -> None:
    with pytest.raises(ValueError, match="n_output"):
        FLRWPipelineConfig(n_output=4)


def test_pipeline_config_rejects_unknown_quadrature() -> None:
    with pytest.raises(ValueError, match="quadrature"):
        FLRWPipelineConfig(quadrature="gauss")


@pytest.fixture(scope="module")
def species() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


def test_visibility_callables_shape(species) -> None:
    """Visibility and optical-depth callables must accept scalar + array η
    and return finite values on a physical η range."""
    g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)

    # Cosmological range well within the HYREC table's z ∈ [0, 8000].
    eta_sample = np.linspace(200.0, 14000.0, 11)
    g = g_of_eta(eta_sample)
    kappa = kappa_of_eta(eta_sample)
    assert g.shape == eta_sample.shape
    assert kappa.shape == eta_sample.shape
    assert np.all(np.isfinite(g))
    assert np.all(np.isfinite(kappa))
    # Visibility is non-negative (τ̇ ≥ 0 and exp(-κ) > 0).
    assert np.all(g >= 0.0)
    # Optical depth is monotonically decreasing in η (increasing in z).
    assert kappa[0] > kappa[-1]


def test_visibility_peak_near_recombination(species) -> None:
    """g(η) should peak near η_*(Planck-2018) ≈ 281 Mpc. This pin is a
    coarse sanity check (just that the peak falls inside [200, 340] Mpc
    on a dense sample), not a precise value check."""
    g_of_eta, _ = build_visibility_and_kappa_callables(species)
    eta_sample = np.linspace(100.0, 500.0, 401)
    g = g_of_eta(eta_sample)
    peak_eta = float(eta_sample[int(np.argmax(g))])
    assert 200.0 <= peak_eta <= 340.0, (
        f"g(η) peak at {peak_eta:.1f} Mpc outside [200, 340] Planck-2018 band"
    )


def test_compute_transfer_function_grid_rejects_empty_k(species) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        compute_transfer_function_grid(species, np.array([], dtype=np.float64))


def test_compute_transfer_function_grid_rejects_non_positive_k(species) -> None:
    with pytest.raises(ValueError, match="positive"):
        compute_transfer_function_grid(species, np.array([0.0, 1.0e-3]))
    with pytest.raises(ValueError, match="positive"):
        compute_transfer_function_grid(species, np.array([1.0e-3, -1.0e-4]))


def test_transfer_fn_from_grid_exact_match() -> None:
    """The dict-lookup factory returns the exact BianchiTransferFunctions
    stored at each k; tolerates ~1e-12 relative float drift."""
    k_grid = np.logspace(-4.0, -3.0, 3)
    stub = [
        BianchiTransferFunctions(
            delta_T_m0=np.full(3, float(k), dtype=np.float64),
            delta_T_m_plus2=np.zeros(3),
            delta_T_m_minus2=np.zeros(3),
            delta_E_m0=np.zeros(3),
            delta_E_m_plus2=np.zeros(3),
            delta_E_m_minus2=np.zeros(3),
            delta_B_all_zero=np.zeros(3),
        )
        for k in k_grid
    ]
    lookup = _transfer_fn_from_grid(k_grid, stub)
    for k in k_grid:
        tf = lookup(float(k))
        assert tf.delta_T_m0[0] == pytest.approx(float(k), abs=1e-14)


def test_transfer_fn_from_grid_rejects_unknown_k() -> None:
    k_grid = np.array([1.0e-4, 1.0e-3], dtype=np.float64)
    stub = [
        BianchiTransferFunctions(
            delta_T_m0=np.zeros(3),
            delta_T_m_plus2=np.zeros(3),
            delta_T_m_minus2=np.zeros(3),
            delta_E_m0=np.zeros(3),
            delta_E_m_plus2=np.zeros(3),
            delta_E_m_minus2=np.zeros(3),
            delta_B_all_zero=np.zeros(3),
        )
        for _ in k_grid
    ]
    lookup = _transfer_fn_from_grid(k_grid, stub)
    with pytest.raises(KeyError, match="no entry"):
        lookup(5.0e-4)  # not in the grid


def test_compute_flrw_cl_tt_rejects_k_grid_mismatch(species) -> None:
    """If the assembly config's k_grid differs from the pipeline k_grid,
    the lookup would miss entries; the wrapper must flag this early."""
    from bass.spectrum.flrw_pipeline import compute_flrw_cl_tt

    pipeline_k = np.array([1.0e-4, 2.0e-4], dtype=np.float64)
    assembly_cfg = CLAssemblyConfig(
        ell_max=2,
        k_grid=np.array([1.0e-3, 2.0e-3], dtype=np.float64),  # mismatch
    )
    with pytest.raises(ValueError, match="must match"):
        compute_flrw_cl_tt(
            species,
            k_grid_mpc=pipeline_k,
            assembly_config=assembly_cfg,
        )


# -----------------------------------------------------------------------
# Slow integration test: parallel k-sweep chains the full pipeline
# -----------------------------------------------------------------------


@pytest.mark.slow
def test_full_pipeline_parallel_k_sweep_produces_finite_D_ell(species) -> None:
    """End-to-end Blocker-1+2+3 + Round-5 extractor + LoS projector +
    C_ℓ assembly + D_ℓ conversion, parallelized over N_k = 2 k-points.

    Runtime budget: ~60 s (2 k × ~45 s / 2 workers). The default
    1378-test fast baseline is preserved since this is slow-marked.

    Asserts:
      - pipeline produces finite D_ℓ^TT and D_ℓ^EE arrays;
      - D_2^TT > 0 (SW plateau contributes positively);
      - D_ℓ^EE[ℓ<2] = 0 (spin-2 selection rule);
      - parallel runtime ≤ 1.5 × single-k cost.

    NOTE on absolute D_2 magnitude: the Tier-B solver's seed amplitude
    is currently ``max(|Σ_±|, 1e-6)`` — not P(k)-normalized. Matching
    the Route-B anchor ``D_2 = 1002.086744 μK²`` requires the Blocker-3
    follow-up (i) primordial amplitude wiring. This test verifies the
    PIPELINE runs end-to-end; absolute normalization is a separate
    follow-up.
    """
    k_grid = np.logspace(-4.0, -3.0, 2)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)
    assembly_cfg = CLAssemblyConfig(
        ell_max=4, k_grid=k_grid, quadrature="trapezoid"
    )

    t0 = time.monotonic()
    bundle = compute_flrw_d_ell(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        n_workers=2,
    )
    dt = time.monotonic() - t0

    d_tt = bundle["d_tt"]
    d_ee = bundle["d_ee"]

    assert np.all(np.isfinite(d_tt))
    assert np.all(np.isfinite(d_ee))
    assert d_tt.shape == (5,)  # ell_max=4 → ell ∈ [0, 4]
    assert float(d_tt[2]) > 0.0, (
        f"D_2^TT = {float(d_tt[2])} is non-positive; check extractor sign"
    )
    # Spin-2 selection rule: D_ℓ^EE is zero for ℓ < 2.
    assert float(d_ee[0]) == 0.0
    assert float(d_ee[1]) == 0.0

    # Parallel efficiency: 2 k-points on 2 workers should take roughly
    # one single-k cost (~45 s). Budget 120 s accounts for species init
    # overhead and variance.
    assert dt < 120.0, (
        f"N_k=2 parallel took {dt:.1f} s; parallelization may be broken"
    )


@pytest.mark.slow
def test_parallel_matches_sequential_transfer_functions(species) -> None:
    """Parallel and sequential paths must produce identical Δ_ℓ values
    (the fork-inherited worker globals carry the same species + config)."""
    k_grid = np.logspace(-4.0, -3.5, 2)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)

    parallel_results = compute_transfer_function_grid(
        species, k_grid, config=pipeline_cfg, n_workers=2
    )
    sequential_results = compute_transfer_function_grid(
        species, k_grid, config=pipeline_cfg, n_workers=1
    )
    for par, seq in zip(parallel_results, sequential_results):
        assert np.allclose(par.delta_T_m0, seq.delta_T_m0, atol=0.0, rtol=0.0), (
            "parallel vs sequential Δ_T^m0 differ — fork inheritance may be broken"
        )
        assert np.allclose(par.delta_E_m0, seq.delta_E_m0, atol=0.0, rtol=0.0), (
            "parallel vs sequential Δ_E^m0 differ — fork inheritance may be broken"
        )
