"""Tests for the Type III (class-B hyperbolic, h=-1) kernel."""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import (
    type_i_constants,
    type_iii_constants,
)
from bass.los.families.type_iii import (
    BRANCH_FLAG,
    KERNEL,
    TypeIIIKernel,
    hyperbolic_cutoff_residual,
    hyperbolic_seed_amplitude,
    hyperbolic_seed_norm_residual,
    translate_native_to_storage,
    translate_storage_to_native,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import (
    _TRANSPORT_DISPATCH,
    build_exact_transport,
    register_family_kernel,
)


# ----- Translator --------------------------------------------------------


def test_branch_flag_constant():
    assert BRANCH_FLAG == "VI_-1_special"


@pytest.mark.parametrize(
    "native,storage",
    [
        (("mu_hyp", BRANCH_FLAG, "scalar"), "m0"),
        (("mu_hyp", BRANCH_FLAG, "tensor_plus"), "m+2"),
        (("mu_hyp", BRANCH_FLAG, "tensor_minus"), "m-2"),
    ],
)
def test_translator_roundtrip(native, storage):
    assert translate_native_to_storage(native) == storage
    assert translate_storage_to_native(storage) == native


def test_translator_rejects_missing_branch_flag():
    with pytest.raises(ValueError, match="branch_flag"):
        translate_native_to_storage(("mu_hyp", "WRONG", "scalar"))


def test_translator_rejects_non_hyp_prefix():
    with pytest.raises(ValueError, match="mu_hyp"):
        translate_native_to_storage(("mu_nil", BRANCH_FLAG, "scalar"))


def test_translator_rejects_malformed():
    with pytest.raises(ValueError, match="mu_hyp"):
        translate_native_to_storage(("mu_hyp", BRANCH_FLAG))


def test_translator_rejects_outside_pstf():
    with pytest.raises(ValueError, match="PSTF storage window"):
        translate_native_to_storage(("mu_hyp", BRANCH_FLAG, "tensor_zero"))


def test_translator_rejects_unknown_storage():
    with pytest.raises(ValueError, match="unknown"):
        translate_storage_to_native("m+1")


# ----- Hyperbolic seed ---------------------------------------------------


def test_seed_amplitude_positive():
    assert hyperbolic_seed_amplitude(xi_max=1.5) > 0.0


def test_seed_amplitude_rejects_non_positive_cutoff():
    with pytest.raises(ValueError, match="xi_max must be > 0"):
        hyperbolic_seed_amplitude(xi_max=0.0)


def test_seed_unit_norm_under_quadrature():
    assert hyperbolic_seed_norm_residual(xi_max=1.5, n_samples=128) < 1.0e-10


def test_cutoff_residual_bounded():
    """P_2(cosh xi) is not rapidly decaying; the bounded-edge metric
    should be finite but not vanish for small xi_max."""
    r = hyperbolic_cutoff_residual(xi_max=1.5)
    assert 0.0 < r < 2.0


# ----- Transport bundle --------------------------------------------------


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


def test_kernel_rejects_non_type_iii():
    with pytest.raises(ValueError, match="structure.label"):
        KERNEL.build_transport_bundle(
            structure=type_i_constants(),
            eta_grid_mpc=ETA,
            k_grid_mpc=K,
            ell_max=ELL_MAX,
            visibility_fn=_vis,
            source_builder=_src,
        )


def test_bundle_metadata_preserves_branch_flag():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    md = bundle.metadata
    assert md["branch_flag"] == BRANCH_FLAG
    assert md["branch_flag_on_seed"] == BRANCH_FLAG
    assert md["chart"] == "class_b_hyperbolic_branch"
    # Type III is the h=-1 special case — verify via physics.
    assert math.isclose(md["h_parameter"], -1.0, rel_tol=1e-6)
    for shortcut in (
        "no_open_flrw_seed_import_without_branch_justification",
        "no_dropping_special_branch_flag",
    ):
        assert shortcut in md["forbidden_shortcut_tracked"]


def test_residuals_pass_for_default_cutoff():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    r = bundle.metadata["residual_values"]
    assert r["class_b_branch_consistency"] == 0.0
    assert r["seed_branch_label_consistency"] == 0.0
    assert r["hyperbolic_cutoff"] < KERNEL.tolerance_hyperbolic_cutoff


def test_residual_pack_passes_within_tolerance():
    bundle = KERNEL.build_transport_bundle(
        structure=type_iii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    pack = KERNEL.residual_pack_from_bundle(bundle)
    assert isinstance(pack, ResidualPack)
    assert pack.passed is True
    assert pack.family == "III"
    assert pack.branch == BRANCH_FLAG


def test_residual_pack_fails_when_branch_flag_mangled():
    # Subclass with mismatched branch attribute should flag the
    # seed_branch_label_consistency residual as infinite.
    class _WrongBranch(TypeIIIKernel):
        branch = "WRONG_BRANCH"

    kernel = _WrongBranch()
    # Directly inspect its residual computation.
    residuals = kernel._compute_residuals()
    assert residuals["seed_branch_label_consistency"] == math.inf


def test_registered_type_iii_routes_through_kernel():
    register_family_kernel(KERNEL)
    bundle = build_exact_transport(
        type_iii_constants(n1=1.0e-2),
        eta_grid_mpc=ETA,
        k_grid_mpc=K,
        ell_max=ELL_MAX,
        visibility_fn=_vis,
        source_builder=_src,
    )
    assert bundle.dispatch_route == "family_kernel_type_iii"
    assert bundle.family == "III"
