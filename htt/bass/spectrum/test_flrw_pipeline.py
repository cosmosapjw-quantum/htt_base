"""Unit + integration tests for the V5 step-4b FLRW D_ℓ pipeline.

Fast tests verify config validation, visibility-callable shapes, and
parallel-vs-sequential consistency plumbing. The full cosmological
k-sweep is gated behind ``@pytest.mark.slow`` (~45 s per run).
"""
from __future__ import annotations

from types import SimpleNamespace
import time

import numpy as np
import pytest

from bass.spectrum.cl_assembly import CLAssemblyConfig
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig,
    _resolve_z_injection_for_k,
    _transfer_fn_from_grid,
    build_visibility_and_kappa_callables,
    compute_flrw_d_ell,
    compute_transfer_function_grid,
)
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.base import SpeciesLabel
from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.runtime import (
    DEFAULT_PRE_RECOMBINATION_MARGIN_MPC,
    PLANCK_2018_Z_STAR,
    cosmological_critical_etas,
)


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
    assert cfg.imex_explicit_update_limit == 0.05
    assert cfg.co_evolve_scalar_metric is False
    assert cfg.co_evolve_scalar_streaming is False
    assert cfg.flrw_source_frame == "legacy_newtonian_constraint"
    assert cfg.z_injection == pytest.approx(PLANCK_2018_Z_STAR)
    assert cfg.pre_recombination_margin_mpc == pytest.approx(
        DEFAULT_PRE_RECOMBINATION_MARGIN_MPC
    )
    assert cfg.superhorizon_x_max_at_start is None
    assert cfg.k_solver_batch_mode == "shared_background"
    assert cfg.intra_chunk_threads == 1
    assert cfg.k_chunk_size is None
    assert cfg.joint_imex_reference_check is True
    assert cfg.joint_imex_reference_rtol == pytest.approx(1.0e-9)
    assert cfg.joint_imex_reference_atol == pytest.approx(1.0e-9)
    assert cfg.joint_imex_schedule == "independent"
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


def test_los_unit_normalization_uses_resolved_primordial_amplitude(
    monkeypatch,
) -> None:
    """Unit transfer response must not be divided by the shear-seed floor.

    The slow Tier-B solve and LoS quadrature are replaced below; the real
    ``_los_and_wrap`` normalization boundary remains under test.  The
    callable is a sentinel: LoS must consume the explicit value already
    resolved by its caller, never re-evaluate config or use a trace amplitude.
    """
    from bass.spectrum import flrw_pipeline as fp

    monkeypatch.setattr(
        fp,
        "extract_flrw_sources_from_tier_b",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        fp,
        "build_los_grid",
        lambda **_kwargs: np.array([0.0, 1.0], dtype=np.float64),
    )
    monkeypatch.setattr(
        fp,
        "build_scalar_sources_pair",
        lambda *_args, **_kwargs: (object(), object()),
    )
    monkeypatch.setattr(
        fp,
        "project_scalar_transfer_pair",
        lambda *_args, **_kwargs: (
            np.array([2.0, 4.0, 6.0], dtype=np.float64),
            np.array([8.0, 10.0, 12.0], dtype=np.float64),
        ),
    )

    integration_result = SimpleNamespace(
        eta=np.array([0.0, 1.0], dtype=np.float64),
    )
    species = SimpleNamespace(bg_table=SimpleNamespace(eta_today=1.0))
    cfg = FLRWPipelineConfig(
        L_max_tower=2,
        ell_max_transfer=2,
        primordial_b_k_sq=7.0,
        primordial_b_k_sq_fn=lambda _k: (_ for _ in ()).throw(
            AssertionError("LoS must consume the parent-resolved amplitude")
        ),
    )

    transfer = fp._los_and_wrap(
        integration_result,
        species,
        1.0e-2,
        cfg,
        primordial_amplitude_for_norm=2.0,
        visibility_callables=(lambda eta: eta, lambda eta: eta),
    )

    np.testing.assert_array_equal(transfer.delta_T_m0, np.array([1.0, 2.0, 3.0]))
    np.testing.assert_array_equal(transfer.delta_E_m0, np.array([4.0, 5.0, 6.0]))


def test_single_k_reuses_integrator_primordial_amplitude_for_los(monkeypatch) -> None:
    """The per-k callable is resolved once and shared by solve and LoS."""
    from bass.spectrum import flrw_pipeline as fp

    calls: list[float] = []

    def resolve_once(k_mpc: float) -> float:
        calls.append(float(k_mpc))
        return 3.0

    captured: dict[str, float] = {}

    monkeypatch.setattr(fp, "_resolve_z_injection_for_k", lambda *_args: 1000.0)
    monkeypatch.setattr(
        fp,
        "build_cosmological_integrator_config",
        lambda *_args, **kwargs: SimpleNamespace(
            primordial_b_k_sq=float(kwargs["primordial_b_k_sq"])
        ),
    )
    monkeypatch.setattr(
        fp,
        "execute_tier_b_solver",
        lambda **_kwargs: SimpleNamespace(integration_result=object()),
    )

    sentinel = object()

    def fake_los(*_args, primordial_amplitude_for_norm, **_kwargs):
        captured["amplitude"] = float(primordial_amplitude_for_norm)
        return sentinel

    monkeypatch.setattr(fp, "_los_and_wrap", fake_los)

    result = fp.compute_transfer_function_at_k(
        object(),
        1.0e-3,
        config=FLRWPipelineConfig(primordial_b_k_sq_fn=resolve_once),
    )

    assert result is sentinel
    assert calls == [1.0e-3]
    assert captured["amplitude"] == 3.0


def test_parallel_grid_parent_resolves_callable_before_per_k_dispatch(
    monkeypatch,
) -> None:
    """Fork workers receive concrete amplitudes, not a stateful callable."""
    from bass.spectrum import flrw_pipeline as fp

    calls: list[float] = []

    def stateful_amplitude(k_mpc: float) -> float:
        calls.append(float(k_mpc))
        return float(len(calls))

    def fake_compute(_species, k_mpc, *, config, bianchi_type):
        del _species, bianchi_type
        return (
            float(config.primordial_b_k_sq_fn(float(k_mpc)))
            if config.primordial_b_k_sq_fn is not None
            else float(config.primordial_b_k_sq)
        )

    monkeypatch.setattr(fp, "compute_transfer_function_at_k", fake_compute)
    k_grid = np.array([1.0e-3, 2.0e-3], dtype=np.float64)

    results = fp.compute_transfer_function_grid(
        object(),
        k_grid,
        config=FLRWPipelineConfig(primordial_b_k_sq_fn=stateful_amplitude),
        n_workers=2,
        chunked=False,
    )

    assert calls == k_grid.tolist()
    assert results == [1.0, 2.0]


def test_parallel_chunk_grid_parent_resolves_callable_before_dispatch(
    monkeypatch,
) -> None:
    """Chunk partitioning cannot restart callable state in each worker."""
    from bass.spectrum import flrw_pipeline as fp

    calls: list[float] = []

    def stateful_amplitude(k_mpc: float) -> float:
        calls.append(float(k_mpc))
        return float(len(calls))

    def fake_shared_chunk(_species, run_specs, *, cfg, bianchi_type):
        del _species, cfg, bianchi_type
        return [float(amplitude) for _k, amplitude in run_specs]

    monkeypatch.setattr(fp, "_run_chunk_shared_bg_for_specs", fake_shared_chunk)
    k_grid = np.array([1.0e-3, 2.0e-3, 3.0e-3, 4.0e-3], dtype=np.float64)

    results = fp.compute_transfer_function_grid(
        object(),
        k_grid,
        config=FLRWPipelineConfig(primordial_b_k_sq_fn=stateful_amplitude),
        n_workers=2,
        chunked=True,
    )

    assert calls == k_grid.tolist()
    assert results == [1.0, 2.0, 3.0, 4.0]


def test_linear_probe_rejects_non_positive_probe_b_k_sq(species) -> None:
    """Round-8 linear-probe API validates its probe amplitude."""
    from bass.spectrum.flrw_pipeline import compute_linear_probe_transfer_function

    with pytest.raises(ValueError, match="probe_b_k_sq must be positive"):
        compute_linear_probe_transfer_function(species, 1.0e-3, probe_b_k_sq=0.0)
    with pytest.raises(ValueError, match="probe_b_k_sq must be positive"):
        compute_linear_probe_transfer_function(species, 1.0e-3, probe_b_k_sq=-1.0)


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


def test_scale_transfer_function_helper() -> None:
    """_scale_transfer_function multiplies every Δ field by a scalar."""
    from bass.spectrum.flrw_pipeline import _scale_transfer_function

    tf = BianchiTransferFunctions(
        delta_T_m0=np.array([1.0, 2.0, 3.0]),
        delta_T_m_plus2=np.array([0.1, 0.2, 0.3]),
        delta_T_m_minus2=np.array([0.4, 0.5, 0.6]),
        delta_E_m0=np.array([10.0, 20.0, 30.0]),
        delta_E_m_plus2=np.zeros(3),
        delta_E_m_minus2=np.zeros(3),
        delta_B_all_zero=np.zeros(3),
    )
    scaled = _scale_transfer_function(tf, 2.5)
    assert np.allclose(scaled.delta_T_m0, np.array([2.5, 5.0, 7.5]), atol=1e-14)
    assert np.allclose(scaled.delta_E_m0, np.array([25.0, 50.0, 75.0]), atol=1e-14)
    assert np.allclose(scaled.delta_T_m_plus2, np.array([0.25, 0.5, 0.75]), atol=1e-14)
    # Zero passthrough preserved.
    assert np.array_equal(scaled.delta_B_all_zero, np.zeros(3))


def test_max_transfer_reference_drift_helper() -> None:
    from bass.spectrum.flrw_pipeline import _max_transfer_reference_drift

    reference = BianchiTransferFunctions(
        delta_T_m0=np.array([1.0, 2.0]),
        delta_T_m_plus2=np.zeros(2),
        delta_T_m_minus2=np.zeros(2),
        delta_E_m0=np.array([3.0, 4.0]),
        delta_E_m_plus2=np.zeros(2),
        delta_E_m_minus2=np.zeros(2),
        delta_B_all_zero=np.zeros(2),
    )
    candidate = BianchiTransferFunctions(
        delta_T_m0=np.array([1.25, 2.0]),
        delta_T_m_plus2=np.zeros(2),
        delta_T_m_minus2=np.zeros(2),
        delta_E_m0=np.array([3.0, 4.5]),
        delta_E_m_plus2=np.zeros(2),
        delta_E_m_minus2=np.zeros(2),
        delta_B_all_zero=np.zeros(2),
    )

    max_abs, max_ref = _max_transfer_reference_drift([reference], [candidate])

    assert max_abs == pytest.approx(0.5)
    assert max_ref == pytest.approx(4.0)


def test_max_integration_history_reference_drift_helper() -> None:
    from bass.spectrum.flrw_pipeline import _max_integration_history_reference_drift

    reference = SimpleNamespace(
        photon_T_tower=np.array([[1.0, 2.0], [3.0, 4.0]]),
        photon_E_tower=np.zeros((2, 2)),
    )
    candidate = SimpleNamespace(
        photon_T_tower=np.array([[1.0, 2.5], [3.0, 4.0]]),
        photon_E_tower=np.zeros((2, 2)),
    )

    max_abs, max_ref, field = _max_integration_history_reference_drift(
        [reference],
        [candidate],
    )

    assert max_abs == pytest.approx(0.5)
    assert max_ref == pytest.approx(4.0)
    assert field == "photon_T_tower"


def test_bias_subtraction_uses_shared_chunk_when_workers_are_limiting(monkeypatch) -> None:
    """Bias and target solves for the same k should share one chunk when
    workers are the limiting resource. The fake runner keeps this as a
    fast dispatch/ordering test without invoking Tier-B."""
    from bass.spectrum import flrw_pipeline as fp

    calls: list[list[tuple[float, float]]] = []

    def fake_shared_chunk(_species, run_specs, *, cfg, bianchi_type):
        del _species, cfg, bianchi_type
        specs = [(float(k), float(b)) for k, b in run_specs]
        calls.append(specs)
        out = []
        for k_mpc, b_k_sq in specs:
            value = k_mpc + b_k_sq
            out.append(
                BianchiTransferFunctions(
                    delta_T_m0=np.array([value], dtype=np.float64),
                    delta_T_m_plus2=np.zeros(1),
                    delta_T_m_minus2=np.zeros(1),
                    delta_E_m0=np.array([2.0 * value], dtype=np.float64),
                    delta_E_m_plus2=np.zeros(1),
                    delta_E_m_minus2=np.zeros(1),
                    delta_B_all_zero=np.zeros(1),
                )
            )
        return out

    monkeypatch.setattr(fp, "_run_chunk_shared_bg_for_specs", fake_shared_chunk)

    cfg = FLRWPipelineConfig(
        bias_subtraction=True,
        primordial_b_k_sq=1.25,
        unit_amplitude_normalization=False,
    )
    k_grid = np.array([1.0e-4, 2.0e-4], dtype=np.float64)
    results = fp._compute_transfer_function_grid_bias_subtracted(
        object(),
        k_grid,
        cfg=cfg,
        bianchi_type="I",
        effective=1,
    )

    assert calls == [[
        (float(k_grid[0]), 0.0),
        (float(k_grid[0]), 1.25),
        (float(k_grid[1]), 0.0),
        (float(k_grid[1]), 1.25),
    ]]
    assert len(results) == 2
    for result in results:
        np.testing.assert_allclose(result.delta_T_m0, np.array([1.25]))
        np.testing.assert_allclose(result.delta_E_m0, np.array([2.5]))


def test_bias_subtraction_normalizes_after_differencing(monkeypatch) -> None:
    """A unit response divides the raw target-minus-bias by its amplitude."""
    from bass.spectrum import flrw_pipeline as fp

    def transfer(value: float) -> BianchiTransferFunctions:
        data = np.array([value], dtype=np.float64)
        zeros = np.zeros(1, dtype=np.float64)
        return BianchiTransferFunctions(
            delta_T_m0=data,
            delta_T_m_plus2=zeros.copy(),
            delta_T_m_minus2=zeros.copy(),
            delta_E_m0=2.0 * data,
            delta_E_m_plus2=zeros.copy(),
            delta_E_m_minus2=zeros.copy(),
            delta_B_all_zero=zeros.copy(),
        )

    monkeypatch.setattr(
        fp,
        "_worker_task_bias_pair_chunk",
        lambda _items: [(transfer(2.0), transfer(6.0))],
    )

    results = fp._compute_transfer_function_grid_bias_subtracted(
        object(),
        np.array([1.0e-3], dtype=np.float64),
        cfg=FLRWPipelineConfig(
            bias_subtraction=True,
            primordial_b_k_sq=2.0,
            unit_amplitude_normalization=True,
        ),
        bianchi_type="I",
        effective=1,
    )

    np.testing.assert_array_equal(results[0].delta_T_m0, np.array([2.0]))
    np.testing.assert_array_equal(results[0].delta_E_m0, np.array([4.0]))


def test_bias_worker_uses_concrete_parent_resolved_amplitude(monkeypatch) -> None:
    """A bias worker must not re-evaluate the parent's amplitude callable."""
    from bass.spectrum import flrw_pipeline as fp

    def fake_compute(_species, k_mpc, *, config, bianchi_type):
        del _species, bianchi_type
        amplitude = (
            float(config.primordial_b_k_sq_fn(float(k_mpc)))
            if config.primordial_b_k_sq_fn is not None
            else float(config.primordial_b_k_sq)
        )
        data = np.array([amplitude], dtype=np.float64)
        zeros = np.zeros(1, dtype=np.float64)
        return BianchiTransferFunctions(
            delta_T_m0=data,
            delta_T_m_plus2=zeros.copy(),
            delta_T_m_minus2=zeros.copy(),
            delta_E_m0=data.copy(),
            delta_E_m_plus2=zeros.copy(),
            delta_E_m_minus2=zeros.copy(),
            delta_B_all_zero=zeros.copy(),
        )

    monkeypatch.setattr(fp, "_WORKER_SPECIES", object())
    monkeypatch.setattr(
        fp,
        "_WORKER_CONFIG",
        FLRWPipelineConfig(
            primordial_b_k_sq=7.0,
            primordial_b_k_sq_fn=lambda _k: 99.0,
        ),
    )
    monkeypatch.setattr(fp, "compute_transfer_function_at_k", fake_compute)

    result = fp._worker_task_bias_pair((1.0e-3, 0.0))

    np.testing.assert_array_equal(result.delta_T_m0, np.array([0.0]))


def test_d_ell_linear_probe_rejects_invalid_inputs(species) -> None:
    """Round-9 wrapper validates k_grid + probe amplitude before any
    expensive solver dispatch (mirrors the single-k linear-probe API)."""
    from bass.spectrum.flrw_pipeline import compute_flrw_d_ell_linear_probe

    k_grid = np.array([1.0e-3, 1.0e-2])

    with pytest.raises(ValueError, match="k_grid_mpc must be non-empty"):
        compute_flrw_d_ell_linear_probe(species, k_grid_mpc=np.array([]))
    with pytest.raises(ValueError, match="must all be positive"):
        compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=np.array([1.0e-3, -1.0e-3])
        )
    with pytest.raises(ValueError, match="probe_b_k_sq must be positive"):
        compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=k_grid, probe_b_k_sq=0.0
        )
    with pytest.raises(ValueError, match="probe_b_k_sq must be positive"):
        compute_flrw_d_ell_linear_probe(
            species, k_grid_mpc=k_grid, probe_b_k_sq=-1.0
        )


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


def test_pipeline_config_rejects_invalid_early_start_controls() -> None:
    with pytest.raises(ValueError, match="z_injection"):
        FLRWPipelineConfig(z_injection=0.0)
    with pytest.raises(ValueError, match="z_injection"):
        FLRWPipelineConfig(z_injection=-1.0)
    with pytest.raises(ValueError, match="pre_recombination_margin_mpc"):
        FLRWPipelineConfig(pre_recombination_margin_mpc=-0.1)
    with pytest.raises(ValueError, match="superhorizon_x_max_at_start"):
        FLRWPipelineConfig(superhorizon_x_max_at_start=0.0)
    with pytest.raises(ValueError, match="superhorizon_x_max_at_start"):
        FLRWPipelineConfig(superhorizon_x_max_at_start=-0.1)


def test_superhorizon_start_resolver_moves_high_k_to_earlier_z(species) -> None:
    cfg = FLRWPipelineConfig(
        superhorizon_x_max_at_start=0.1,
        pre_recombination_margin_mpc=0.0,
    )

    z_low = _resolve_z_injection_for_k(species, cfg, 1.0e-4)
    z_high = _resolve_z_injection_for_k(species, cfg, 5.0e-2)

    assert z_low == pytest.approx(cfg.z_injection)
    assert z_high > z_low
    anchors = cosmological_critical_etas(
        species,
        z_injection=z_high,
        pre_recombination_margin_mpc=0.0,
    )
    assert 5.0e-2 * anchors["eta_initial_mpc"] <= 0.1 * (1.0 + 2.0e-3)


def test_pipeline_config_rejects_non_positive_max_step_factor() -> None:
    with pytest.raises(ValueError, match="max_step_factor"):
        FLRWPipelineConfig(max_step_factor=0)
    with pytest.raises(ValueError, match="max_step_factor"):
        FLRWPipelineConfig(max_step_factor=-10)


def test_pipeline_config_rejects_non_positive_imex_update_limit() -> None:
    with pytest.raises(ValueError, match="imex_explicit_update_limit"):
        FLRWPipelineConfig(imex_explicit_update_limit=0.0)
    with pytest.raises(ValueError, match="imex_explicit_update_limit"):
        FLRWPipelineConfig(imex_explicit_update_limit=-0.1)


def test_pipeline_config_rejects_invalid_flrw_source_frame() -> None:
    with pytest.raises(ValueError, match="flrw_source_frame"):
        FLRWPipelineConfig(flrw_source_frame="toy_metric_patch")


def test_pipeline_config_rejects_invalid_k_solver_batch_mode() -> None:
    with pytest.raises(ValueError, match="k_solver_batch_mode"):
        FLRWPipelineConfig(k_solver_batch_mode="vectorized_magic")


def test_pipeline_config_rejects_non_positive_intra_chunk_threads() -> None:
    with pytest.raises(ValueError, match="intra_chunk_threads"):
        FLRWPipelineConfig(intra_chunk_threads=0)
    with pytest.raises(ValueError, match="intra_chunk_threads"):
        FLRWPipelineConfig(intra_chunk_threads=-2)


def test_pipeline_config_rejects_non_positive_k_chunk_size() -> None:
    with pytest.raises(ValueError, match="k_chunk_size"):
        FLRWPipelineConfig(k_chunk_size=0)
    with pytest.raises(ValueError, match="k_chunk_size"):
        FLRWPipelineConfig(k_chunk_size=-3)


def test_pipeline_config_rejects_negative_joint_imex_reference_tolerances() -> None:
    with pytest.raises(ValueError, match="joint_imex_reference_rtol"):
        FLRWPipelineConfig(joint_imex_reference_rtol=-1.0e-9)
    with pytest.raises(ValueError, match="joint_imex_reference_atol"):
        FLRWPipelineConfig(joint_imex_reference_atol=-1.0e-9)


def test_pipeline_config_rejects_invalid_joint_imex_schedule() -> None:
    assert FLRWPipelineConfig(joint_imex_schedule="ragged").joint_imex_schedule == "ragged"
    assert (
        FLRWPipelineConfig(joint_imex_schedule="grouped").joint_imex_schedule
        == "grouped"
    )
    with pytest.raises(ValueError, match="joint_imex_schedule"):
        FLRWPipelineConfig(joint_imex_schedule="global_shared_magic")


def test_split_work_chunks_default_and_fixed_size() -> None:
    from bass.spectrum.flrw_pipeline import _split_work_chunks

    values = [0, 1, 2, 3, 4]

    assert _split_work_chunks(values, worker_count=2, chunk_size=None) == [
        [0, 1, 2],
        [3, 4],
    ]
    assert _split_work_chunks(values, worker_count=8, chunk_size=None) == [
        [0],
        [1],
        [2],
        [3],
        [4],
    ]
    assert _split_work_chunks(values, worker_count=2, chunk_size=2) == [
        [0, 1],
        [2, 3],
        [4],
    ]


def test_joint_imex_k_batch_advances_fake_integrators_shared_loop() -> None:
    """Fast scheduler test for the true batched k-solver.

    The fake integrators expose the same private methods the production
    VER2 integrator uses, but with a constant explicit RHS and identity
    implicit/source/residual steps. This verifies that the batch loop
    advances multiple k states through one shared-step schedule and
    reconstructs per-k results without invoking the expensive physics
    solver.
    """

    from bass.spectrum.flrw_pipeline import (
        _run_grouped_imex_k_batch,
        _run_independent_imex_k_batch,
        _run_joint_imex_k_batch,
        _run_ragged_imex_k_batch,
    )

    class _FakeVisibility:
        contract = SimpleNamespace(events=None)

    class _FakeIntegrator:
        _residual_local_dof = 0
        _residual_harmonic_dof = 0
        _residual_source_dof = 0

        def __init__(self, rate: float) -> None:
            self.rate = float(rate)
            self.config = SimpleNamespace(
                solver_method="IMEX_MIDPOINT_BDF",
                tilt_rapidity=0.0,
                eta_initial_mpc=1.0,
                eta_final_mpc=2.0,
                n_output=3,
                L_max=2,
                max_step_factor=2,
                imex_explicit_update_limit=10.0,
            )
            self.visibility_source = _FakeVisibility()
            self.initial_trial_h_values: list[float | None] = []

        def initial_state(self) -> np.ndarray:
            tower_size = (self.config.L_max + 1) ** 2
            return np.zeros(4 * tower_size + 9, dtype=np.float64)

        def _explicit_rhs(
            self,
            _eta: float,
            y: np.ndarray,
            *,
            out: np.ndarray | None = None,
        ) -> np.ndarray:
            if out is None:
                return np.full_like(y, self.rate, dtype=np.float64)
            out.fill(self.rate)
            return out

        def _imex_advance_one_substep(
            self,
            *,
            eta_current: float,
            eta_target: float,
            y_current: np.ndarray,
            tca_tracker: list[bool],
            tuning,
            cache,
            explicit_0=None,
            initial_trial_h=None,
        ):
            del tuning
            assert explicit_0 is not None
            self.initial_trial_h_values.append(initial_trial_h)
            np.testing.assert_allclose(
                explicit_0,
                np.full_like(y_current, self.rate, dtype=np.float64),
            )
            tca_tracker.append(False)
            return SimpleNamespace(
                eta_next=float(eta_target),
                y_next=np.asarray(
                    y_current + self.rate * (float(eta_target) - float(eta_current)),
                    dtype=np.float64,
                ),
                cache=cache,
                nfev=1,
                njev=0,
                nlu=0,
            )

        def _solve_segment_imex(
            self,
            *,
            eta_start: float,
            eta_stop: float,
            y0: np.ndarray,
            eta_eval: np.ndarray,
            tca_tracker: list[bool],
        ):
            del eta_stop
            eta_arr = np.asarray(eta_eval, dtype=np.float64)
            columns = [
                np.asarray(
                    y0 + self.rate * (float(eta) - float(eta_start)),
                    dtype=np.float64,
                )
                for eta in eta_arr
            ]
            tca_tracker.extend([False] * max(0, eta_arr.size - 1))
            return SimpleNamespace(
                t=eta_arr,
                y=np.column_stack(columns),
                nfev=int(max(0, eta_arr.size - 1)),
                njev=0,
                nlu=0,
                status=0,
                message="fake independent IMEX solve",
            )

        def _orthogonal_implicit_step(
            self,
            *,
            eta: float,
            stage: np.ndarray,
            dt: float,
            tca_tracker: list[bool],
        ) -> np.ndarray:
            del eta, dt
            tca_tracker.append(False)
            return np.asarray(stage, dtype=np.float64)

        def _orthogonal_covered_source_ros2_step(self, **kwargs):
            return np.asarray(kwargs["y_right"], dtype=np.float64), kwargs["affine_left"]

        def _orthogonal_residual_joint_ros2_step(self, **kwargs):
            return np.asarray(kwargs["y_right"], dtype=np.float64), kwargs["affine_left"]

        def _build_result(self, **kwargs):
            kwargs["solver_info"] = {}
            return SimpleNamespace(**kwargs)

        def build_layout_auxiliary_history_bundle(self, _result):
            return {"fake": True}

        def build_runtime_execution_trace(self, _result, *, reionization_amplitude: float):
            return {"reionization_amplitude": reionization_amplitude}

    results = _run_joint_imex_k_batch([_FakeIntegrator(2.0), _FakeIntegrator(3.0)])

    assert len(results) == 2
    np.testing.assert_allclose(results[0].eta, np.array([1.0, 1.5, 2.0]))
    np.testing.assert_allclose(results[0].photon_T_tower[-1, 0], 2.0)
    np.testing.assert_allclose(results[1].photon_T_tower[-1, 0], 3.0)
    assert results[0].solver_info["k_solver_batch_mode"] == "joint_imex"
    assert results[0].solver_info["k_solver_batch_size"] == 2

    independent_results = _run_independent_imex_k_batch(
        [_FakeIntegrator(2.0), _FakeIntegrator(3.0)]
    )
    np.testing.assert_allclose(independent_results[0].eta, np.array([1.0, 1.5, 2.0]))
    np.testing.assert_allclose(independent_results[0].photon_T_tower[-1, 0], 2.0)
    np.testing.assert_allclose(independent_results[1].photon_T_tower[-1, 0], 3.0)
    assert (
        independent_results[0].solver_info["k_solver_batch_schedule"]
        == "independent"
    )

    ragged_results = _run_ragged_imex_k_batch(
        [_FakeIntegrator(2.0), _FakeIntegrator(3.0)]
    )
    np.testing.assert_allclose(ragged_results[0].eta, np.array([1.0, 1.5, 2.0]))
    np.testing.assert_allclose(ragged_results[0].photon_T_tower[-1, 0], 2.0)
    np.testing.assert_allclose(ragged_results[1].photon_T_tower[-1, 0], 3.0)
    assert ragged_results[0].solver_info["k_solver_batch_schedule"] == "ragged"
    assert ragged_results[0].solver_info["k_solver_batch_ragged_substeps"] == 4

    grouped_integrators = [_FakeIntegrator(2.0), _FakeIntegrator(3.0)]
    grouped_results = _run_grouped_imex_k_batch(grouped_integrators)
    np.testing.assert_allclose(grouped_results[0].eta, np.array([1.0, 1.5, 2.0]))
    np.testing.assert_allclose(grouped_results[0].photon_T_tower[-1, 0], 2.0)
    np.testing.assert_allclose(grouped_results[1].photon_T_tower[-1, 0], 3.0)
    assert grouped_results[0].solver_info["k_solver_batch_schedule"] == "grouped"
    assert grouped_results[0].solver_info["k_solver_batch_grouped_substeps"] == 4
    assert grouped_results[0].solver_info["k_solver_batch_grouped_bucket_count"] == 2
    assert grouped_results[0].solver_info["k_solver_batch_grouped_max_bucket_size"] == 2
    for integrator in grouped_integrators:
        np.testing.assert_allclose(integrator.initial_trial_h_values, [0.5, 0.5])


def test_joint_imex_shared_step_failure_reports_failing_member() -> None:
    from bass.spectrum.flrw_pipeline import _run_joint_imex_k_batch

    class _FakeIntegrator:
        def __init__(self, *, fail: bool) -> None:
            self.fail = bool(fail)
            self.config = SimpleNamespace(
                solver_method="IMEX_MIDPOINT_BDF",
                tilt_rapidity=0.0,
                eta_initial_mpc=1.0,
                eta_final_mpc=2.0,
                n_output=3,
                L_max=2,
                max_step_factor=2,
                imex_explicit_update_limit=10.0,
            )

        def initial_state(self) -> np.ndarray:
            tower_size = (self.config.L_max + 1) ** 2
            return np.zeros(4 * tower_size + 9, dtype=np.float64)

        def _explicit_rhs(
            self,
            _eta: float,
            y: np.ndarray,
            *,
            out: np.ndarray | None = None,
        ) -> np.ndarray:
            if out is None:
                return np.ones_like(y, dtype=np.float64)
            out.fill(1.0)
            return out

        def _imex_advance_one_substep(
            self,
            *,
            eta_current: float,
            eta_target: float,
            y_current: np.ndarray,
            tca_tracker: list[bool],
            tuning,
            cache,
            explicit_0=None,
            initial_trial_h=None,
        ):
            del eta_current, tca_tracker, tuning, explicit_0, initial_trial_h
            if self.fail:
                raise RuntimeError("synthetic finite-substep failure")
            return SimpleNamespace(
                eta_next=float(eta_target),
                y_next=np.asarray(y_current, dtype=np.float64),
                cache=cache,
                nfev=1,
                njev=0,
                nlu=0,
            )

    with pytest.raises(RuntimeError) as excinfo:
        _run_joint_imex_k_batch(
            [_FakeIntegrator(fail=False), _FakeIntegrator(fail=True)]
        )
    message = str(excinfo.value)
    assert "accepted shared substep" in message
    assert "member=1" in message
    assert "synthetic finite-substep failure" in message
    assert "eta_current=" in message
    assert "last_trial_h=" in message
    assert "max_explicit_scale=" in message


def test_joint_imex_shared_step_nonfinite_explicit_rhs_fails_closed() -> None:
    from bass.spectrum.flrw_pipeline import (
        _run_grouped_imex_k_batch,
        _run_joint_imex_k_batch,
        _run_ragged_imex_k_batch,
    )

    class _FakeIntegrator:
        def __init__(self, *, nonfinite_rhs: bool) -> None:
            self.nonfinite_rhs = bool(nonfinite_rhs)
            self.config = SimpleNamespace(
                solver_method="IMEX_MIDPOINT_BDF",
                tilt_rapidity=0.0,
                eta_initial_mpc=1.0,
                eta_final_mpc=2.0,
                n_output=3,
                L_max=2,
                max_step_factor=2,
                imex_explicit_update_limit=10.0,
            )

        def initial_state(self) -> np.ndarray:
            tower_size = (self.config.L_max + 1) ** 2
            return np.zeros(4 * tower_size + 9, dtype=np.float64)

        def _explicit_rhs(
            self,
            _eta: float,
            y: np.ndarray,
            *,
            out: np.ndarray | None = None,
        ) -> np.ndarray:
            if self.nonfinite_rhs:
                if out is None:
                    return np.full_like(y, np.inf, dtype=np.float64)
                out.fill(np.inf)
                return out
            if out is None:
                return np.ones_like(y, dtype=np.float64)
            out.fill(1.0)
            return out

        def _imex_advance_one_substep(
            self,
            *,
            eta_current: float,
            eta_target: float,
            y_current: np.ndarray,
            tca_tracker: list[bool],
            tuning,
            cache,
            explicit_0=None,
            initial_trial_h=None,
        ):
            del eta_current, tca_tracker, tuning, explicit_0, initial_trial_h
            return SimpleNamespace(
                eta_next=float(eta_target),
                y_next=np.asarray(y_current, dtype=np.float64),
                cache=cache,
                nfev=1,
                njev=0,
                nlu=0,
            )

    with pytest.raises(RuntimeError) as excinfo:
        _run_joint_imex_k_batch(
            [
                _FakeIntegrator(nonfinite_rhs=False),
                _FakeIntegrator(nonfinite_rhs=True),
            ]
        )
    message = str(excinfo.value)
    assert "non-finite explicit RHS" in message
    assert "member=1" in message
    assert "eta_current=" in message
    assert "state_norm=" in message

    with pytest.raises(RuntimeError) as ragged_excinfo:
        _run_ragged_imex_k_batch(
            [
                _FakeIntegrator(nonfinite_rhs=False),
                _FakeIntegrator(nonfinite_rhs=True),
            ]
        )
    ragged_message = str(ragged_excinfo.value)
    assert "ragged IMEX" in ragged_message
    assert "non-finite explicit RHS" in ragged_message
    assert "member=1" in ragged_message

    with pytest.raises(RuntimeError) as grouped_excinfo:
        _run_grouped_imex_k_batch(
            [
                _FakeIntegrator(nonfinite_rhs=False),
                _FakeIntegrator(nonfinite_rhs=True),
            ]
        )
    grouped_message = str(grouped_excinfo.value)
    assert "grouped IMEX" in grouped_message
    assert "non-finite explicit RHS" in grouped_message
    assert "member=1" in grouped_message


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


def test_visibility_callables_use_early_kappa_extension(species) -> None:
    """Deep pre-recombination visibility must use the fully-ionized
    optical-depth extension, not a clipped z=z_max table value."""

    g_of_eta, kappa_of_eta = build_visibility_and_kappa_callables(species)
    baryon = species[SpeciesLabel.BARYON]
    z_max = float(baryon._recomb.table.z_max)  # noqa: SLF001
    eta_table_max = species.bg_table.eta_at_a(1.0 / (1.0 + z_max))
    eta_early = species.bg_table.eta_at_a(1.0 / (1.0 + 15000.0))

    kappa_table_max = float(kappa_of_eta(np.asarray(eta_table_max)))
    kappa_early = float(kappa_of_eta(np.asarray(eta_early)))
    g_early = float(g_of_eta(np.asarray(eta_early)))

    assert kappa_early > kappa_table_max
    assert np.isfinite(g_early)
    assert g_early >= 0.0


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
      - pipeline produces finite D_ℓ^TT, D_ℓ^EE, and D_ℓ^TE arrays;
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
    d_te = bundle["d_te"]

    assert np.all(np.isfinite(d_tt))
    assert np.all(np.isfinite(d_ee))
    assert np.all(np.isfinite(d_te))
    assert d_tt.shape == (5,)  # ell_max=4 → ell ∈ [0, 4]
    assert d_ee.shape == (5,)
    assert d_te.shape == (5,)
    assert float(d_tt[2]) > 0.0, (
        f"D_2^TT = {float(d_tt[2])} is non-positive; check extractor sign"
    )
    # Spin-2 selection rule: D_ℓ^EE is zero for ℓ < 2.
    assert float(d_ee[0]) == 0.0
    assert float(d_ee[1]) == 0.0
    assert float(d_te[0]) == 0.0
    assert float(d_te[1]) == 0.0

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


@pytest.mark.slow
def test_d_ell_linear_probe_end_to_end_finite(species) -> None:
    """V5 Round-9 R9-A: ``compute_flrw_d_ell_linear_probe`` chains the
    bias-subtracted linear probe across N_k k-points and assembles
    Planck-2018 D_ℓ.

    Runtime budget: ~50 s (2 k × 2 runs / 2 workers). Validates the
    end-to-end wiring; the absolute calibration of the response to
    Route-B (~1002 μK²) is the open R9-B/C convention audit. Spec:

      - finite D_ℓ^TT and D_ℓ^EE arrays
      - shape ``(ell_max+1,)``
      - α(k) finite for every k
      - calibration_factor=1.0 default applied (i.e., bundle records it)
    """
    from bass.spectrum.flrw_pipeline import compute_flrw_d_ell_linear_probe

    k_grid = np.logspace(-4.0, -3.0, 2)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)

    bundle = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        probe_b_k_sq=1.0,
        n_workers=2,
    )

    # Schema
    assert set(bundle.keys()) >= {
        "k_grid_mpc",
        "alpha_transfer_functions",
        "probe_b_k_sq",
        "calibration_factor",
        "cl_tt",
        "cl_ee",
        "cl_te",
        "d_tt",
        "d_ee",
        "d_te",
        "assembly_config",
    }
    assert bundle["probe_b_k_sq"] == 1.0
    assert bundle["calibration_factor"] == 1.0
    assert bundle["d_tt"].shape == (5,)
    assert bundle["d_ee"].shape == (5,)
    assert bundle["d_te"].shape == (5,)
    assert np.all(np.isfinite(bundle["d_tt"]))
    assert np.all(np.isfinite(bundle["d_ee"]))
    assert np.all(np.isfinite(bundle["d_te"]))
    # Spin-2 selection rule: D_ℓ^EE = 0 for ℓ < 2
    assert float(bundle["d_ee"][0]) == 0.0
    assert float(bundle["d_ee"][1]) == 0.0
    assert float(bundle["d_te"][0]) == 0.0
    assert float(bundle["d_te"][1]) == 0.0
    # α(k) returned for every k point, finite
    assert len(bundle["alpha_transfer_functions"]) == len(k_grid)
    for tf in bundle["alpha_transfer_functions"]:
        assert np.all(np.isfinite(tf.delta_T_m0))
        assert np.all(np.isfinite(tf.delta_E_m0))


@pytest.mark.slow
def test_d_ell_linear_probe_calibration_factor_scales_quadratically(species) -> None:
    """R9-C: applying ``calibration_factor`` scales D_ℓ by its square,
    since α appears squared in the C_ℓ assembly. This confirms the
    knob is wired correctly for downstream B_K² ↔ ζ² calibration."""
    from bass.spectrum.flrw_pipeline import compute_flrw_d_ell_linear_probe

    k_grid = np.logspace(-4.0, -3.0, 2)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4)

    bundle_unit = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        calibration_factor=1.0,
        n_workers=2,
    )
    bundle_scaled = compute_flrw_d_ell_linear_probe(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        calibration_factor=2.5,
        n_workers=2,
    )

    # D_ℓ ∝ |α|² → calibration_factor enters quadratically
    expected_ratio = 2.5 ** 2
    for ell in (2, 3, 4):
        observed = float(bundle_scaled["d_tt"][ell]) / float(
            bundle_unit["d_tt"][ell]
        )
        assert observed == pytest.approx(expected_ratio, rel=1.0e-10)
        if abs(float(bundle_unit["d_te"][ell])) > 1.0e-300:
            observed_te = float(bundle_scaled["d_te"][ell]) / float(
                bundle_unit["d_te"][ell]
            )
            assert observed_te == pytest.approx(expected_ratio, rel=1.0e-10)
