"""Tests for the Type VIII (SL(2,ℝ) discrete-series) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import type_i_constants, type_viii_constants
from bass.los.families.type_viii import (
    CONTINUOUS_SERIES_TAG,
    DISCRETE_SERIES_TAGS,
    KERNEL,
    continuous_principal_series_norm,
    continuous_series_l2_residual,
    noncompact_disc_norm_residual,
    noncompact_disc_seed_amplitude,
    principal_series_plancherel_weight,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_sl2r", "trivial", "scalar"), "m0"),
        (("mu_sl2r", "discrete_positive", "tensor_plus"), "m+2"),
        (("mu_sl2r", "discrete_negative", "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


@pytest.mark.parametrize(
    "component,storage",
    [("scalar", "m0"), ("tensor_plus", "m+2"), ("tensor_minus", "m-2")],
)
def test_continuous_series_translator_routes_by_component(component, storage):
    # S7 upgrade: continuous series is now a live branch.
    label = ("mu_sl2r", CONTINUOUS_SERIES_TAG, component)
    assert translate_native_to_storage(label) == storage


def test_continuous_series_rejects_unknown_component():
    with pytest.raises(ValueError, match="continuous-series component"):
        translate_native_to_storage(("mu_sl2r", CONTINUOUS_SERIES_TAG, "banana"))


def test_plancherel_weight_matches_closed_form():
    import math

    for nu in [0.5, 1.0, 1.5, 3.0]:
        assert principal_series_plancherel_weight(nu) == nu * math.tanh(math.pi * nu)


def test_plancherel_weight_rejects_non_positive():
    with pytest.raises(ValueError, match="nu must be > 0"):
        principal_series_plancherel_weight(0.0)


def test_continuous_principal_series_norm_is_positive():
    disc_radius = math.tanh(1.5)
    norm = continuous_principal_series_norm(1.5, disc_radius=disc_radius, n_samples=64)
    assert norm > 0.0


def test_continuous_series_l2_residual_within_precision():
    disc_radius = math.tanh(1.5)
    for nu in [0.5, 1.5, 3.0]:
        r = continuous_series_l2_residual(nu, disc_radius=disc_radius, n_samples=64)
        assert r < 1.0e-10


def test_continuous_principal_series_norm_rejects_nu_le_zero():
    with pytest.raises(ValueError, match="nu must be > 0"):
        continuous_principal_series_norm(0.0, disc_radius=0.9, n_samples=32)


def test_translator_rejects_unknown_series():
    with pytest.raises(ValueError, match="series_tag"):
        translate_native_to_storage(("mu_sl2r", "banana", "scalar"))


def test_translator_rejects_wrong_prefix():
    with pytest.raises(ValueError, match="mu_sl2r"):
        translate_native_to_storage(("mu_hyp", "trivial", "scalar"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+3")


def test_discrete_series_tags_fixed_set():
    assert DISCRETE_SERIES_TAGS == ("trivial", "discrete_positive", "discrete_negative")


def test_noncompact_disc_seed_amplitude_positive():
    amp = noncompact_disc_seed_amplitude(0.5)
    assert amp > 0.0


def test_disc_norm_residual_under_quadrature_precision():
    assert noncompact_disc_norm_residual(math.tanh(1.5), n_samples=128) < 1.0e-10


ETA = np.linspace(40.0, 420.0, 65)
K = np.array([0.05, 0.08, 0.12])
ELL_MAX = 6


def _vis(eta: float) -> float:
    return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))


def _src(eta: float, k: float) -> dict[str, float]:
    env = float(np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2))
    return {
        "temperature": env * (1.0 + 0.1 * k),
        "temperature_anisotropy": 0.2 * env,
        "polarization": 0.35 * env,
        "b_mode": 0.0,
    }


@pytest.fixture(autouse=True)
def _clean_dispatch():
    snapshot = dict(_TRANSPORT_DISPATCH)
    _TRANSPORT_DISPATCH.clear()
    yield
    _TRANSPORT_DISPATCH.clear()
    _TRANSPORT_DISPATCH.update(snapshot)


def test_kernel_rejects_non_type_viii():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_exposes_continuous_series_branch():
    bundle = KERNEL.build_transport_bundle(
        structure=type_viii_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["continuous_series_status"] == "active_via_mpmath_hyp2f1"
    assert md["continuous_series_tag"] == CONTINUOUS_SERIES_TAG
    assert md["plancherel_weight_formula"] == "nu * tanh(pi * nu)"
    assert list(md["continuous_series_nu_probes"]) == list(KERNEL.default_continuous_nu_probes)
    assert md["discrete_series_tags"] == list(DISCRETE_SERIES_TAGS)
    assert math.isclose(md["disc_radius_x_eq_tanh_xi"], math.tanh(1.5))
    for shortcut in (
        "no_compact_su2_reuse",
        "no_wigner_d_assumption_without_explicit_approximation_tag",
    ):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_pass_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_viii_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["branch_tag"] == 0.0
    assert r["seed_regularity"] < 1.0e-10
    assert r["noncompact_truncation"] < KERNEL.tolerance_noncompact_truncation
    assert r["continuous_series_l2_residual"] < KERNEL.tolerance_continuous_series_l2
    assert r["plancherel_weight_consistency"] < KERNEL.tolerance_plancherel_weight_consistency


def test_residual_pack_passes():
    bundle = KERNEL.build_transport_bundle(
        structure=type_viii_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "VIII"


def test_registered_type_viii_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_viii_constants(),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_viii"
