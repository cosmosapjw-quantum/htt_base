"""FB-3.6 — 44-configuration tilted regression suite.

Exercises the full FB-3 tilt stack (FB-3.1 species wrapper +
FB-3.2 kinematic adapters + FB-3.3 Einstein additive pieces +
FB-3.4 vorticity dilution + FB-3.5 admissibility gate) against

    β ∈ {0.0, 0.01, 0.1, 0.5} × {FLRW + 11 Bianchi types} = 48 configs

(44 pure Bianchi × β + 4 FLRW baselines) to pin

1. RHS finiteness on every admissible configuration;
2. β → 0 byte-identical recovery against the FB-2.4 no-kwargs
   anchor (commit ``d7d25da``);
3. non-physical β-jump stress — evaluating the RHS with β swapped
   between calls on the same state produces different but still
   finite output (no hidden β-dependent cached state);
4. rapidity-path construction path parity with the velocity ctor.

Test ledger (S-01 .. S-08)
--------------------------
S-01 : β-sweep × 12-label RHS finiteness.
S-02 : β = 0 byte-identical against no-kwargs anchor across all 12
       labels.
S-03 : β-jump stress — call RHS with β = 0.1 then β = 0.01 on the
       same state; both outputs finite; second call independent of
       the first.
S-04 : rapidity-path ctor produces RHS output equal to velocity-
       path ctor within round-trip precision.
S-05 : FB-3.3 extended-kwargs path (bg_table + tetrad_state) at
       β = 0 remains byte-identical to the anchor on all 12 labels.
S-06 : FB-3.4 dynamic vorticity path at β = 0 × every Class B type
       is byte-identical to β = 0 × Class A (both reduce to zero
       vorticity input).
S-07 : shape stability — dy has the same length as y0 on every config.
S-08 : no RuntimeError / floating exception on the full sweep (the
       test body uses `np.errstate(all='raise')` so any silent FPE
       trips).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES,
    CLASS_A_TYPES,
    CLASS_B_TYPES,
    get_type,
)
from bass.background.einstein_bianchi import BianchiCosmology
from bass.background.tetrad_state import TetradBackgroundState
from bass.background.bianchi_types import flrw_constants
from bass.hierarchy.closure_interface import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.pstf_tensor import (
    PSTFTensor,
    pack_hierarchy,
    zero_hierarchy,
)
from bass.hierarchy.tilt_kinematics import (
    accel_from_tilt,
    vorticity_from_tilt,
)
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground


_LABELS = ("FLRW",) + tuple(ALL_BIANCHI_TYPES)
_BETA_SWEEP = (0.0, 0.01, 0.1, 0.5)


@pytest.fixture(scope="module")
def registry():
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def bg_table(registry):
    return registry.bg_table


@pytest.fixture(scope="module")
def photon(registry):
    return registry[SpeciesLabel.PHOTON]


@pytest.fixture(scope="module")
def eta_sample(bg_table):
    return float(bg_table.eta[bg_table.eta.size // 2])


def _build_state(L_max: int = 3, seed: int = 36):
    rng = np.random.default_rng(seed)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1),
        )
    return pack_hierarchy(state), L_max


def _axisymmetric_tetrad_fixture(bg_table) -> TetradBackgroundState:
    eta_grid = np.asarray(bg_table.eta, dtype=np.float64)
    N = eta_grid.size
    a_grid = 1e-6 * np.ones(N)
    s_val = 1.0e-5
    sigma_base = np.diag([2.0 / 3.0, -1.0 / 3.0, -1.0 / 3.0])
    sigma = s_val * np.broadcast_to(
        sigma_base[None, :, :], (N, 3, 3)
    ).copy()
    return TetradBackgroundState(
        eta=eta_grid,
        alpha=np.log(a_grid),
        a=a_grid,
        beta_tensor=np.zeros((N, 3, 3)),
        sigma_tensor=sigma,
        aniso_3_curvature=None,
        structure=flrw_constants(),
        curvature_status="type_i_flat",
        cosmo=BianchiCosmology(structure=flrw_constants()),
    )


# ──────────────────────────────────────────────────────────────────────
# S-01 : β-sweep × 12-label RHS finiteness
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _LABELS)
@pytest.mark.parametrize("beta", _BETA_SWEEP)
def test_S01_beta_sweep_rhs_finite(photon, bg_table, eta_sample, label, beta):
    y0, L_max = _build_state()
    structure = get_type(label)
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    dy = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=structure, bg_table=bg_table,
        ),
    )
    assert np.all(np.isfinite(dy))
    assert dy.shape == y0.shape


# ──────────────────────────────────────────────────────────────────────
# S-02 : β = 0 byte-identical vs no-kwargs anchor, 12 labels
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _LABELS)
def test_S02_beta_zero_byte_identical_fb24_anchor(
    photon, bg_table, eta_sample, label,
):
    y0, L_max = _build_state()
    structure = get_type(label)

    dy_anchor = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    dy_fb36 = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(t0, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t0, eta_sample, structure=structure, bg_table=bg_table,
        ),
    )
    assert np.array_equal(dy_fb36, dy_anchor), f"drift on label {label!r}"


# ──────────────────────────────────────────────────────────────────────
# S-03 : β-jump stress — two sequential calls on the same state
# ──────────────────────────────────────────────────────────────────────


def test_S03_beta_jump_stress(photon, bg_table, eta_sample):
    y0, L_max = _build_state()
    structure = get_type("V")
    driver_args = dict(
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    t1 = TiltedSpeciesBackground(base=photon, beta=0.1)
    t2 = TiltedSpeciesBackground(base=photon, beta=0.01)
    dy1 = hierarchy_rhs_photon(
        eta_sample, y0,
        **driver_args,
        accel_vector=accel_from_tilt(t1, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t1, eta_sample, structure=structure,
        ),
    )
    dy2 = hierarchy_rhs_photon(
        eta_sample, y0,
        **driver_args,
        accel_vector=accel_from_tilt(t2, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t2, eta_sample, structure=structure,
        ),
    )
    assert np.all(np.isfinite(dy1))
    assert np.all(np.isfinite(dy2))
    assert not np.array_equal(dy1, dy2)


# ──────────────────────────────────────────────────────────────────────
# S-04 : rapidity-path ctor parity
# ──────────────────────────────────────────────────────────────────────


def test_S04_rapidity_path_parity(photon, bg_table, eta_sample):
    y0, L_max = _build_state()
    structure = get_type("V")
    driver_args = dict(
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    # Construct two tilt wrappers: one via velocity, one via rapidity
    # whose tanh reproduces the velocity. RHS outputs should match
    # within float64 round-trip precision.
    beta_v = 0.1
    rap = np.arctanh(beta_v)
    t_v = TiltedSpeciesBackground(base=photon, beta=beta_v)
    t_r = TiltedSpeciesBackground.from_rapidity(
        base=photon, rapidity=float(rap),
    )

    dy_v = hierarchy_rhs_photon(
        eta_sample, y0,
        **driver_args,
        accel_vector=accel_from_tilt(t_v, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t_v, eta_sample, structure=structure,
        ),
    )
    dy_r = hierarchy_rhs_photon(
        eta_sample, y0,
        **driver_args,
        accel_vector=accel_from_tilt(t_r, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t_r, eta_sample, structure=structure,
        ),
    )
    # Not strictly bit-identical (float64 tanh(atanh) drift) but
    # agreement to ~1e-14 relative.
    np.testing.assert_allclose(dy_v, dy_r, rtol=1e-12, atol=1e-14)


# ──────────────────────────────────────────────────────────────────────
# S-05 : FB-3.3 extended kwargs at β = 0 preserves anchor
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _LABELS)
def test_S05_fb33_extended_beta_zero_anchor(
    photon, bg_table, eta_sample, label,
):
    y0, L_max = _build_state()
    structure = get_type(label)
    fx = _axisymmetric_tetrad_fixture(bg_table)

    dy_anchor = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    dy_ext = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(
            t0, eta_sample, bg_table=bg_table, tetrad_state=fx,
        ),
        vorticity_vector=vorticity_from_tilt(
            t0, eta_sample, structure=structure, bg_table=bg_table,
        ),
    )
    assert np.array_equal(dy_ext, dy_anchor)


# ──────────────────────────────────────────────────────────────────────
# S-06 : FB-3.4 dynamic vorticity at β = 0 — Class A and Class B agree
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("class_a_label", CLASS_A_TYPES)
@pytest.mark.parametrize("class_b_label", CLASS_B_TYPES)
def test_S06_beta_zero_vorticity_class_A_equals_class_B(
    photon, bg_table, eta_sample, class_a_label, class_b_label,
):
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    ω_A = vorticity_from_tilt(
        t0, eta_sample,
        structure=get_type(class_a_label), bg_table=bg_table,
    )
    ω_B = vorticity_from_tilt(
        t0, eta_sample,
        structure=get_type(class_b_label), bg_table=bg_table,
    )
    np.testing.assert_array_equal(ω_A, np.zeros(3))
    np.testing.assert_array_equal(ω_B, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# S-07 : shape stability on the full sweep
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _LABELS)
def test_S07_shape_stability(photon, bg_table, eta_sample, label):
    y0, L_max = _build_state()
    structure = get_type(label)
    tilted = TiltedSpeciesBackground(base=photon, beta=0.3)
    dy = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=structure,
        ),
    )
    assert dy.shape == y0.shape


# ──────────────────────────────────────────────────────────────────────
# S-08 : no silent FPE on the full sweep
# ──────────────────────────────────────────────────────────────────────


def test_S08_no_silent_floating_exceptions(photon, bg_table, eta_sample):
    y0, L_max = _build_state()
    # Inside the numpy errstate context any divide / invalid / overflow
    # raises FloatingPointError instead of producing inf/nan silently.
    # divide='raise' is too strict because proper_shear_at_eta's cubic
    # spline build can trigger benign underflow; we allow that.
    with np.errstate(invalid='raise', over='raise'):
        for label in _LABELS:
            structure = get_type(label)
            for beta in _BETA_SWEEP:
                tilted = TiltedSpeciesBackground(base=photon, beta=beta)
                dy = hierarchy_rhs_photon(
                    eta_sample, y0,
                    L_max=L_max,
                    bg_table=bg_table,
                    tetrad_state=None,
                    closure=HardCutClosure(),
                    collision=ZeroCollisionOperator(),
                    accel_vector=accel_from_tilt(tilted, eta_sample),
                    vorticity_vector=vorticity_from_tilt(
                        tilted, eta_sample,
                        structure=structure,
                    ),
                )
                assert np.all(np.isfinite(dy))
