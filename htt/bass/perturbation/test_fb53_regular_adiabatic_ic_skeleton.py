from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.ic import zero_IC
from bass.perturbation.regular_adiabatic_ic import (
    CAMB_REGULAR_ADIABATIC_EXTRA_SIZE,
    infer_regular_adiabatic_seed_L_max,
    make_camb_regular_adiabatic_seed,
    regular_adiabatic_seed_total_size,
    seed_observables,
    slice_regular_adiabatic_extras,
)


@pytest.fixture(scope="module")
def camb_ic_reference():
    camb = pytest.importorskip("camb")
    pars = camb.CAMBparams()
    pars.set_cosmology(
        H0=67.36,
        ombh2=0.02237,
        omch2=0.12,
        mnu=0.06,
        omk=0.0,
        tau=0.0544,
    )
    pars.InitPower.set_params(As=2.1e-9, ns=0.9649)
    pars.set_for_lmax(30, lens_potential_accuracy=0)
    data = camb.get_results(pars)

    out = {
        "eta_density": 0.1,
        "eta_velocity": 0.2,
        "density_values": {},
        "velocity_values": {},
    }
    for k in (1.0e-3, 2.0e-3, 1.0e-2):
        density_arr = data.get_time_evolution(
            [k],
            [out["eta_density"]],
            [
                "a",
                "delta_photon",
                "delta_baryon",
                "delta_cdm",
                "delta_neutrino",
            ],
        )[0, 0]
        out["density_values"][k] = {
            "a": float(density_arr[0]),
            "delta_gamma": float(density_arr[1]),
            "delta_b": float(density_arr[2]),
            "delta_c": float(density_arr[3]),
            "delta_nu": float(density_arr[4]),
        }

        velocity_arr = data.get_time_evolution(
            [k],
            [out["eta_velocity"]],
            [
                "a",
                "v_neutrino",
            ],
        )[0, 0]
        out["velocity_values"][k] = {
            "a": float(velocity_arr[0]),
            "theta_nu": float(velocity_arr[1]),
        }
    return out


@pytest.mark.parametrize("L_max", range(2, 22))
def test_fb53_seed_size_roundtrip(L_max: int) -> None:
    total = regular_adiabatic_seed_total_size(L_max)
    assert total > CAMB_REGULAR_ADIABATIC_EXTRA_SIZE
    assert infer_regular_adiabatic_seed_L_max(total) == L_max
    extras = slice_regular_adiabatic_extras(L_max)
    assert extras.stop - extras.start == CAMB_REGULAR_ADIABATIC_EXTRA_SIZE


@pytest.mark.parametrize("L_max", (2, 4, 6, 8))
def test_fb53_k_zero_reduces_to_zero_ic_prefix(L_max: int) -> None:
    a_initial = 1.0e-6
    seed = make_camb_regular_adiabatic_seed(
        k_comoving=0.0,
        eta_initial=0.2,
        a_initial=a_initial,
        L_max=L_max,
    )
    background = zero_IC(L_max=L_max, a_initial=a_initial)
    prefix = seed[: background.size]
    extras = seed[background.size :]
    assert np.array_equal(prefix, background)
    assert np.array_equal(extras, np.zeros_like(extras))


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"k_comoving": -1.0e-3, "eta_initial": 0.2, "a_initial": 1.0e-6, "L_max": 4}, "k_comoving"),
        ({"k_comoving": 1.0e-3, "eta_initial": 0.0, "a_initial": 1.0e-6, "L_max": 4}, "eta_initial"),
        ({"k_comoving": 1.0e-3, "eta_initial": 0.2, "a_initial": 0.0, "L_max": 4}, "a_initial"),
        ({"k_comoving": 1.0e-3, "eta_initial": 0.2, "a_initial": 1.0e-6, "L_max": 1}, "L_max"),
    ),
)
def test_fb53_invalid_seed_inputs_raise(
    kwargs: dict[str, float | int],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        make_camb_regular_adiabatic_seed(**kwargs)


@pytest.mark.parametrize("k_comoving", (1.0e-3, 2.0e-3, 1.0e-2))
@pytest.mark.parametrize(
    "observable",
    ("delta_gamma", "delta_b", "delta_c", "delta_nu", "theta_nu"),
)
def test_fb53_regular_seed_matches_camb_superhorizon_fixture(
    camb_ic_reference,
    k_comoving: float,
    observable: str,
) -> None:
    if observable == "theta_nu":
        eta_initial = float(camb_ic_reference["eta_velocity"])
        ref = camb_ic_reference["velocity_values"][k_comoving]
    else:
        eta_initial = float(camb_ic_reference["eta_density"])
        ref = camb_ic_reference["density_values"][k_comoving]
    seed = make_camb_regular_adiabatic_seed(
        k_comoving=k_comoving,
        eta_initial=eta_initial,
        a_initial=float(ref["a"]),
        L_max=6,
    )
    obs = seed_observables(seed, L_max=6)
    assert obs[observable] == pytest.approx(ref[observable], rel=1.0e-4, abs=1.0e-18)
