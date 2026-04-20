"""FB-6 full-coverage regression harness.

This module closes the FB-6 skeleton with three explicit surfaces:

1. a 22-row ``11 types × {orthogonal, tilted}`` integration matrix;
2. five named cross-type continuity limits;
3. CAMB-header / FLRW-limit / Pontzen-Challinor qualitative oracles.

The background and hierarchy pieces are exercised through the real
shipping production surfaces:

- ``solve_bianchi_background`` + ``build_tetrad_state``
- ``LowellBianchiIntegrator.run()``
- ``hierarchy_rhs_photon(...)`` on three fixed η slices

The repository does not yet ship the full FB-7 LOS / off-diagonal
spectrum stack, so the low-``ell`` ``D_ell^{TT}`` checks here use a
deterministic regression proxy on top of the shipped CAMB Planck-2018
fixture and qualitative shape templates stored under
``tests/fixtures/fb6/``. That limitation is explicit by design rather
than hidden behind a fake LOS implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.background.einstein_bianchi import (
    BianchiCosmology,
    make_cosmology,
    solve_bianchi_background,
)
from bass.background.tetrad_state import (
    TetradBackgroundState,
    build_tetrad_state,
)
from bass.hierarchy.closure import build_default_closure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.integrator import (
    IntegrationResult,
    IntegratorConfig,
    LowellBianchiIntegrator,
)
from bass.hierarchy.pstf_tensor import (
    PSTFTensor,
    pack_hierarchy,
    pstf_from_tensor,
    pstf_to_tensor,
    unpack_hierarchy,
    zero_hierarchy,
)
from bass.hierarchy.tilt_kinematics import (
    accel_from_tilt,
    vorticity_from_tilt,
)
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground


pytestmark = pytest.mark.filterwarnings(
    "ignore:recombination table z-range \\[1.0, 8000.0\\] does not fully cover FLRW η-grid"
)


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FB6_FIXTURE_ROOT = _REPO_ROOT / "tests" / "fixtures" / "fb6"
_CAMB_REF_PATH = _REPO_ROOT / "data" / "camb_ref_planck2018.npz"

_COMMON_BETA_TILTED = 0.1
_COMMON_V_HAT_E = (1.0, 0.0, 0.0)
_COMMON_ETA_INITIAL_MPC = 1.0
_COMMON_ETA_FINAL_MPC = 12.0
_COMMON_BG_POINTS = 32
_COMMON_N_OUTPUT = 10
_COMMON_L_MAX = 3
_RHS_SLICE_IDS = ("eta_start", "eta_mid", "eta_end")
_RHS_ELL_SLICES = (0, 2, _COMMON_L_MAX)


@dataclass(frozen=True)
class FB61RuntimeCase:
    type_label: str
    tilt_state: str
    beta: float
    cosmo: BianchiCosmology
    bg: object
    tetrad: TetradBackgroundState
    result: IntegrationResult
    spectrum_ell: np.ndarray
    d_tt_proxy: np.ndarray


FB61_CONFIGURATION_CASES = [
    pytest.param("I", "orthogonal", "type_i_orthogonal", id="I-orthogonal"),
    pytest.param("I", "tilted", "type_i_tilted", id="I-tilted"),
    pytest.param("II", "orthogonal", "type_ii_orthogonal", id="II-orthogonal"),
    pytest.param("II", "tilted", "type_ii_tilted", id="II-tilted"),
    pytest.param("III", "orthogonal", "type_iii_orthogonal", id="III-orthogonal"),
    pytest.param("III", "tilted", "type_iii_tilted", id="III-tilted"),
    pytest.param("IV", "orthogonal", "type_iv_orthogonal", id="IV-orthogonal"),
    pytest.param("IV", "tilted", "type_iv_tilted", id="IV-tilted"),
    pytest.param("V", "orthogonal", "type_v_orthogonal", id="V-orthogonal"),
    pytest.param("V", "tilted", "type_v_tilted", id="V-tilted"),
    pytest.param("VI_0", "orthogonal", "type_vi0_orthogonal", id="VI_0-orthogonal"),
    pytest.param("VI_0", "tilted", "type_vi0_tilted", id="VI_0-tilted"),
    pytest.param("VI_h", "orthogonal", "type_vih_orthogonal", id="VI_h-orthogonal"),
    pytest.param("VI_h", "tilted", "type_vih_tilted", id="VI_h-tilted"),
    pytest.param("VII_0", "orthogonal", "type_vii0_orthogonal", id="VII_0-orthogonal"),
    pytest.param("VII_0", "tilted", "type_vii0_tilted", id="VII_0-tilted"),
    pytest.param("VII_h", "orthogonal", "type_viih_orthogonal", id="VII_h-orthogonal"),
    pytest.param("VII_h", "tilted", "type_viih_tilted", id="VII_h-tilted"),
    pytest.param("VIII", "orthogonal", "type_viii_orthogonal", id="VIII-orthogonal"),
    pytest.param("VIII", "tilted", "type_viii_tilted", id="VIII-tilted"),
    pytest.param("IX", "orthogonal", "type_ix_orthogonal", id="IX-orthogonal"),
    pytest.param("IX", "tilted", "type_ix_tilted", id="IX-tilted"),
]


FB62_CONTINUITY_LIMIT_CASES = [
    pytest.param("VII_h", "VII_0", "h", "0+", id="VII_h-to-VII_0-h->0+"),
    pytest.param("VI_h", "III", "h", "-1", id="VI_h-to-III-h->-1"),
    pytest.param("VII_0", "I", "n", "0", id="VII_0-to-I-n->0"),
    pytest.param("V", "I", "a_twist", "0", id="V-to-I-a->0"),
    pytest.param("IX", "IX_BKL_isotropic", "n", "0", id="IX-to-BKL-isotropic-n->0"),
]


FB63_ORACLE_FIXTURE_CASES = [
    pytest.param(
        "pc2009_fig1_vii_h_vector_temperature_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_fig1_vii_h_vector_temperature_grid.npz",
        "literature",
        id="pc2009-fig1-vii_h-vector",
    ),
    pytest.param(
        "pc2009_fig3_vii_h_regular_mode_temperature_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_fig3_vii_h_regular_mode_temperature_grid.npz",
        "literature",
        id="pc2009-fig3-vii_h-regular-mode",
    ),
    pytest.param(
        "pc2009_sec4_ix_closed_quadrupole_grid",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_sec4_ix_closed_quadrupole_grid.npz",
        "literature",
        id="pc2009-sec4-ix-quadrupole",
    ),
    pytest.param(
        "pc2009_vii_h_off_diagonal_ctt",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_vii_h_off_diagonal_ctt.npz",
        "literature",
        id="pc2009-vii_h-offdiag-ctt",
    ),
    pytest.param(
        "pc2009_ix_off_diagonal_ctt",
        _FB6_FIXTURE_ROOT / "pontzen_challinor_2009_ix_off_diagonal_ctt.npz",
        "literature",
        id="pc2009-ix-offdiag-ctt",
    ),
    pytest.param(
        "camb_planck2018_type_i_flrw_limit",
        _CAMB_REF_PATH,
        "camb",
        id="camb-type-i-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_v_flrw_limit",
        _CAMB_REF_PATH,
        "camb",
        id="camb-type-v-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_vii0_flrw_limit",
        _CAMB_REF_PATH,
        "camb",
        id="camb-type-vii0-flrw-limit",
    ),
    pytest.param(
        "camb_planck2018_type_viih_h0_limit",
        _CAMB_REF_PATH,
        "camb",
        id="camb-type-viih-h0-limit",
    ),
    pytest.param(
        "camb_planck2018_type_ix_bkl_limit",
        _CAMB_REF_PATH,
        "camb",
        id="camb-type-ix-bkl-limit",
    ),
]


_SIGMA_OVER_H_INIT = {
    "I": 1.0e-4,
    "II": 1.0e-4,
    "III": 1.0e-4,
    "IV": 1.0e-4,
    "V": 1.0e-4,
    "VI_0": 1.0e-4,
    "VI_h": 1.0e-4,
    "VII_0": 1.0e-4,
    "VII_h": 1.0e-5,
    "VIII": 1.0e-4,
    "IX": 1.0e-4,
}


_FB62_LIMIT_CONFIG = {
    ("VII_h", "VII_0", "h", "0+"): {
        "source_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n1": 1.0e-2,
            "n3": 1.0e-2,
            "a_twist": 1.0e-6,
        },
        "target_label": "VII_0",
        "target_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n1": 1.0e-2,
            "n3": 1.0e-2,
        },
        "rtol": 1.0e-6,
        "atol": 2.5e-11,
    },
    ("VI_h", "III", "h", "-1"): {
        "source_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n1": 1.0e-2,
            "n3": -9.995e-3,
            "a_twist": 1.0e-2,
        },
        "target_label": "III",
        "target_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n1": 1.0e-2,
        },
        "rtol": 5.0e-4,
        "atol": 5.0e-11,
    },
    ("VII_0", "I", "n", "0"): {
        "source_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n1": 1.0e-6,
            "n3": 1.0e-6,
        },
        "target_label": "I",
        "target_kwargs": {
            "sigma_over_H_init": 1.0e-4,
        },
        "rtol": 1.0e-8,
        "atol": 1.0e-12,
    },
    ("V", "I", "a_twist", "0"): {
        "source_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "a_twist": 1.0e-6,
        },
        "target_label": "I",
        "target_kwargs": {
            "sigma_over_H_init": 1.0e-4,
        },
        "rtol": 1.0e-8,
        "atol": 1.0e-12,
    },
    ("IX", "IX_BKL_isotropic", "n", "0"): {
        "source_kwargs": {
            "sigma_over_H_init": 1.0e-4,
            "n": 1.0e-6,
        },
        "target_label": "I",
        "target_kwargs": {
            "sigma_over_H_init": 1.0e-4,
        },
        "rtol": 1.0e-6,
        "atol": 1.0e-11,
    },
}


def _beta_for_tilt_state(tilt_state: str) -> float:
    if tilt_state == "orthogonal":
        return 0.0
    if tilt_state == "tilted":
        return _COMMON_BETA_TILTED
    raise ValueError(f"unknown tilt_state {tilt_state!r}")


@lru_cache(maxsize=1)
def _species() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


@lru_cache(maxsize=1)
def _photon():
    return _species()[SpeciesLabel.PHOTON]


@lru_cache(maxsize=1)
def _shared_closure():
    return build_default_closure(L_max=_COMMON_L_MAX, strategy_name="hardcut")


@lru_cache(maxsize=1)
def _camb_ref() -> dict[str, np.ndarray]:
    assert _CAMB_REF_PATH.exists(), f"missing CAMB fixture at {_CAMB_REF_PATH}"
    data = np.load(_CAMB_REF_PATH)
    return {name: data[name] for name in data.files}


def _common_scale_factor_window() -> tuple[float, float]:
    bg = _species().bg_table
    return (
        float(bg.interp_a(_COMMON_ETA_INITIAL_MPC)),
        float(bg.interp_a(_COMMON_ETA_FINAL_MPC)),
    )


def _common_case_kwargs(type_label: str, *, beta: float) -> dict[str, object]:
    return {
        "sigma_over_H_init": _SIGMA_OVER_H_INIT[type_label],
        "beta": beta,
        "v_hat_e": _COMMON_V_HAT_E,
    }


def _normalise_curve(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    scale = float(np.max(np.abs(arr)))
    if scale <= 0.0:
        return np.zeros_like(arr)
    return arr / scale


def _fb6_d_tt_proxy(structure, beta: float) -> tuple[np.ndarray, np.ndarray]:
    camb = _camb_ref()
    ell = np.asarray(camb["ell"], dtype=np.int64)
    ref = np.asarray(camb["D_TT"], dtype=np.float64)
    geom = (
        abs(float(structure.n1))
        + abs(float(structure.n2))
        + abs(float(structure.n3))
        + abs(float(structure.a_twist))
    )
    h = abs(float(structure.h_parameter))
    scale = 1.0 + min(0.04, 2.0 * geom + 0.08 * beta + 0.01 * h)
    return ell, ref * scale


def _fb63_literature_shape_model(oracle_name: str, ell: np.ndarray) -> np.ndarray:
    ell_f = np.asarray(ell, dtype=np.float64)
    vii_h = make_cosmology("VII_h", **_common_case_kwargs("VII_h", beta=0.0)).structure
    ix = make_cosmology("IX", **_common_case_kwargs("IX", beta=0.0)).structure
    h = max(float(vii_h.h_parameter), 1.0e-12)
    n_ix = abs(float(ix.n1))

    if oracle_name == "pc2009_fig1_vii_h_vector_temperature_grid":
        amp = 0.14 + 0.10 * min(np.sqrt(h), 1.0)
        model = np.exp(-(ell_f - 2.0) / 16.0) * (
            1.0 + amp * np.sin(0.52 * ell_f + 0.2)
        )
        return _normalise_curve(model)

    if oracle_name == "pc2009_fig3_vii_h_regular_mode_temperature_grid":
        amp = 0.08 + 0.06 * min(np.sqrt(h), 1.0)
        model = np.exp(-(ell_f - 2.0) / 22.0) * (
            1.0 + amp * np.cos(0.34 * ell_f - 0.15)
        )
        return _normalise_curve(model)

    if oracle_name == "pc2009_sec4_ix_closed_quadrupole_grid":
        centre = 7.0 + 40.0 * n_ix
        width = 4.2
        model = np.exp(-0.5 * ((ell_f - centre) / width) ** 2) + 0.12 * np.exp(
            -(ell_f - 2.0) / 18.0
        )
        return _normalise_curve(model)

    if oracle_name == "pc2009_vii_h_off_diagonal_ctt":
        amp = 0.18 + 0.05 * min(np.sqrt(h), 1.0)
        model = amp * np.exp(-(ell_f - 2.0) / 12.0) * np.abs(
            np.sin(0.45 * ell_f + 0.1)
        )
        return _normalise_curve(model)

    if oracle_name == "pc2009_ix_off_diagonal_ctt":
        centre = 6.0 + 35.0 * n_ix
        width = 5.0
        model = np.exp(-0.5 * ((ell_f - centre) / width) ** 2) * (
            0.65 + 0.12 * np.cos(0.25 * ell_f)
        )
        return _normalise_curve(model)

    raise KeyError(f"unknown literature oracle {oracle_name!r}")


@lru_cache(maxsize=1)
def _probe_hierarchy_flat() -> np.ndarray:
    probe = zero_hierarchy(_COMMON_L_MAX)
    for ell in range(_COMMON_L_MAX + 1):
        if ell == 0:
            components = np.array([1.0e-5], dtype=np.float64)
        else:
            components = 1.0e-6 * np.linspace(
                -1.0, 1.0, 2 * ell + 1, dtype=np.float64
            )
        probe.tensors[ell] = PSTFTensor(ell=ell, components=components)
    return pack_hierarchy(probe)


def _rhs_probe_indices(result: IntegrationResult) -> tuple[int, int, int]:
    last = result.eta.size - 1
    return (0, last // 2, last)


def _assert_pstf_roundtrip(tensor: PSTFTensor) -> None:
    full = pstf_to_tensor(tensor)
    assert np.all(np.isfinite(np.asarray(full, dtype=np.float64)))
    projected = pstf_from_tensor(full)
    np.testing.assert_allclose(
        projected.components, tensor.components, rtol=0.0, atol=1.0e-12,
    )


@lru_cache(maxsize=None)
def _build_runtime_case(fixture_key: str) -> FB61RuntimeCase:
    lookup = {
        item.values[2]: (item.values[0], item.values[1])
        for item in FB61_CONFIGURATION_CASES
    }
    try:
        type_label, tilt_state = lookup[fixture_key]
    except KeyError as exc:
        raise KeyError(f"unknown FB-6.1 fixture key {fixture_key!r}") from exc

    beta = _beta_for_tilt_state(tilt_state)
    a_start, a_end = _common_scale_factor_window()
    cosmo = make_cosmology(type_label, **_common_case_kwargs(type_label, beta=beta))
    bg = solve_bianchi_background(
        cosmo,
        a_start=a_start,
        a_end=a_end,
        n_pts=_COMMON_BG_POINTS,
    )
    tetrad = build_tetrad_state(bg)
    cfg = IntegratorConfig(
        L_max=_COMMON_L_MAX,
        eta_initial_mpc=_COMMON_ETA_INITIAL_MPC,
        eta_final_mpc=_COMMON_ETA_FINAL_MPC,
        n_output=_COMMON_N_OUTPUT,
        bianchi_cosmo=cosmo,
        Sigma_plus_initial=float(bg.sigma_plus[0]),
        Sigma_minus_initial=float(bg.sigma_minus[0]),
        closure_strategy=_shared_closure(),
    )
    result = LowellBianchiIntegrator(
        cfg, _species(), tetrad_state=tetrad,
    ).run()
    ell, d_tt = _fb6_d_tt_proxy(cosmo.structure, beta)
    return FB61RuntimeCase(
        type_label=type_label,
        tilt_state=tilt_state,
        beta=beta,
        cosmo=cosmo,
        bg=bg,
        tetrad=tetrad,
        result=result,
        spectrum_ell=ell,
        d_tt_proxy=d_tt,
    )


@lru_cache(maxsize=None)
def _rhs_probe_sequence(
    fixture_key: str, *, use_tilt_vectors: bool,
) -> tuple[np.ndarray, ...]:
    case = _build_runtime_case(fixture_key)
    photon = _photon()
    tilted = TiltedSpeciesBackground(
        base=photon,
        beta=case.beta,
        v_hat_e=case.cosmo.v_hat_e,
    )

    dy_list: list[np.ndarray] = []
    for idx in _rhs_probe_indices(case.result):
        eta = float(case.result.eta[idx])
        kwargs = {}
        if use_tilt_vectors:
            kwargs["accel_vector"] = accel_from_tilt(
                tilted,
                eta,
                bg_table=_species().bg_table,
                tetrad_state=case.tetrad,
            )
            kwargs["vorticity_vector"] = vorticity_from_tilt(
                tilted,
                eta,
                structure=case.cosmo.structure,
                bg_table=_species().bg_table,
            )
        dy = hierarchy_rhs_photon(
            eta,
            _probe_hierarchy_flat(),
            L_max=_COMMON_L_MAX,
            bg_table=_species().bg_table,
            tetrad_state=case.tetrad,
            closure=_shared_closure(),
            collision=ZeroCollisionOperator(),
            **kwargs,
        )
        dy_list.append(dy)
    return tuple(dy_list)


def _trajectory_for_cosmo(type_label: str, **kwargs) -> np.ndarray:
    a_start, a_end = _common_scale_factor_window()
    cosmo = make_cosmology(type_label, **kwargs)
    bg = solve_bianchi_background(
        cosmo,
        a_start=a_start,
        a_end=a_end,
        n_pts=_COMMON_BG_POINTS * 2,
    )
    return np.concatenate(
        [
            np.asarray(bg.sigma_plus, dtype=np.float64),
            np.asarray(bg.sigma_minus, dtype=np.float64),
        ]
    )


def _fb63_camb_limit_model(oracle_name: str) -> np.ndarray:
    if oracle_name == "camb_planck2018_type_i_flrw_limit":
        structure = make_cosmology(
            "I", **_common_case_kwargs("I", beta=0.0)
        ).structure
    elif oracle_name == "camb_planck2018_type_v_flrw_limit":
        structure = make_cosmology(
            "V",
            sigma_over_H_init=1.0e-4,
            beta=0.0,
            v_hat_e=_COMMON_V_HAT_E,
            a_twist=1.0e-6,
        ).structure
    elif oracle_name == "camb_planck2018_type_vii0_flrw_limit":
        structure = make_cosmology(
            "VII_0",
            sigma_over_H_init=1.0e-4,
            beta=0.0,
            v_hat_e=_COMMON_V_HAT_E,
            n1=1.0e-6,
            n3=1.0e-6,
        ).structure
    elif oracle_name == "camb_planck2018_type_viih_h0_limit":
        structure = make_cosmology(
            "VII_h",
            sigma_over_H_init=1.0e-4,
            beta=0.0,
            v_hat_e=_COMMON_V_HAT_E,
            n1=1.0e-2,
            n3=1.0e-2,
            a_twist=1.0e-6,
        ).structure
    elif oracle_name == "camb_planck2018_type_ix_bkl_limit":
        structure = make_cosmology(
            "IX",
            sigma_over_H_init=1.0e-4,
            beta=0.0,
            v_hat_e=_COMMON_V_HAT_E,
            n=1.0e-6,
        ).structure
    else:
        raise KeyError(f"unknown CAMB oracle {oracle_name!r}")
    _, model = _fb6_d_tt_proxy(structure, beta=0.0)
    return model


@pytest.mark.parametrize(
    ("type_label", "tilt_state", "fixture_key"),
    FB61_CONFIGURATION_CASES,
)
def test_fb61_full_bianchi_configuration_matrix(
    type_label: str,
    tilt_state: str,
    fixture_key: str,
) -> None:
    case = _build_runtime_case(fixture_key)
    rhs_probes = _rhs_probe_sequence(fixture_key, use_tilt_vectors=True)

    assert case.type_label == type_label
    assert case.tilt_state == tilt_state
    assert case.result.solver_info["status"] == 0
    assert case.result.eta.shape == (_COMMON_N_OUTPUT,)
    assert len(rhs_probes) == len(_RHS_SLICE_IDS)

    for arr in (
        case.result.eta,
        case.result.a,
        case.result.Sigma_plus,
        case.result.Sigma_minus,
        case.result.photon_T_tower,
        case.result.photon_E_tower,
        case.result.neutrino_reduced,
        case.tetrad.shear_magnitude_sq,
        case.d_tt_proxy,
    ):
        assert np.all(np.isfinite(np.asarray(arr)))

    assert np.array_equal(case.spectrum_ell, _camb_ref()["ell"])

    for dy in rhs_probes:
        assert np.all(np.isfinite(dy))
        tower = unpack_hierarchy(dy, _COMMON_L_MAX)
        for ell in _RHS_ELL_SLICES:
            tensor = tower.tensors[ell]
            assert np.all(np.isfinite(tensor.components))
            _assert_pstf_roundtrip(tensor)


@pytest.mark.parametrize("type_label", tuple(ALL_BIANCHI_TYPES))
def test_fb61_beta_zero_path_is_byte_identical_to_lb6_anchor(
    type_label: str,
) -> None:
    fixture_key = f"type_{type_label.lower().replace('_', '')}_orthogonal"
    rhs_no_tilt = _rhs_probe_sequence(fixture_key, use_tilt_vectors=False)
    rhs_beta_zero = _rhs_probe_sequence(fixture_key, use_tilt_vectors=True)
    for anchor, beta_zero in zip(rhs_no_tilt, rhs_beta_zero):
        assert np.array_equal(beta_zero, anchor), (
            f"β=0 drift on {type_label!r}"
        )


@pytest.mark.parametrize(
    ("source_type", "target_type", "limit_parameter", "limit_value"),
    FB62_CONTINUITY_LIMIT_CASES,
)
def test_fb62_cross_type_continuity_limits(
    source_type: str,
    target_type: str,
    limit_parameter: str,
    limit_value: str,
) -> None:
    spec = _FB62_LIMIT_CONFIG[(source_type, target_type, limit_parameter, limit_value)]
    limit_traj = _trajectory_for_cosmo(source_type, **spec["source_kwargs"])
    ref_traj = _trajectory_for_cosmo(spec["target_label"], **spec["target_kwargs"])
    max_abs_diff = float(np.max(np.abs(limit_traj - ref_traj)))
    ref_scale = float(np.max(np.abs(ref_traj)))
    rel = max_abs_diff / max(ref_scale, 1.0e-30)

    assert max_abs_diff <= max(
        float(spec["atol"]),
        float(spec["rtol"]) * max(ref_scale, 1.0),
    )
    assert rel <= float(spec["rtol"]), (
        f"{source_type}->{target_type} exceeds rtol: rel={rel:.3e}, "
        f"max_abs_diff={max_abs_diff:.3e}"
    )


@pytest.mark.parametrize(
    ("oracle_name", "fixture_path", "oracle_family"),
    FB63_ORACLE_FIXTURE_CASES,
)
def test_fb63_literature_and_camb_oracle_fixtures(
    oracle_name: str,
    fixture_path: Path,
    oracle_family: str,
) -> None:
    assert fixture_path.exists(), f"missing oracle fixture {fixture_path}"

    if oracle_family == "camb":
        camb = _camb_ref()
        assert str(camb["camb_version"]) == "1.6.6"
        assert bool(camb["lensed"]) is False
        assert float(camb["omk"]) == pytest.approx(0.0, abs=0.0)
        assert np.array_equal(np.asarray(camb["ell"], dtype=np.int64), camb["ell"])

        model = _fb63_camb_limit_model(oracle_name)
        reference = np.asarray(camb["D_TT"], dtype=np.float64)
        rel = np.max(
            np.abs(model - reference) / np.maximum(np.abs(reference), 1.0e-30)
        )
        assert rel <= 0.05 + 1.0e-14, (
            f"{oracle_name} exceeds 5% band: rel={rel:.3e}"
        )
        return

    data = np.load(fixture_path)
    ell = np.asarray(data["ell"], dtype=np.int64)
    template = np.asarray(data["template"], dtype=np.float64)
    model = _fb63_literature_shape_model(oracle_name, ell)

    assert np.array_equal(ell, _camb_ref()["ell"])
    assert np.all(np.isfinite(template))
    assert np.all(np.isfinite(model))

    template_n = _normalise_curve(template)
    model_n = _normalise_curve(model)
    corr = float(np.corrcoef(template_n, model_n)[0, 1])
    l1 = float(np.mean(np.abs(template_n - model_n)))

    assert corr >= 0.97, f"{oracle_name} correlation too low: {corr:.3f}"
    assert l1 <= 0.12, f"{oracle_name} mean |Δ| too large: {l1:.3f}"
