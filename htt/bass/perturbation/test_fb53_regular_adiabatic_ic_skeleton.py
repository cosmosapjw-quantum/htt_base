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


@pytest.mark.parametrize("k_comoving", (1.0e-4, 1.0e-3, 1.0e-2))
def test_fb53_zero_amplitude_seed_has_no_neutrino_perturbation(
    k_comoving: float,
) -> None:
    """Regular adiabatic mode at b_k_sq=0 yields identically-zero ν
    perturbations: at zero curvature amplitude there is no perturbation
    of any species (MB-95 §7 adiabatic seed; Lewis-Challinor 2002 §3).

    Round-9 R9-D bug fixed in Round-10: pre-fix, ``π_ν`` and ``G_3``
    omitted the ``B_K_sq`` amplitude factor and produced an unphysical
    ``x²``/``x³`` floor at b_k_sq=0. Six independent external auditors
    (CONFIRMED) traced this against MB-95 eq. 96-99. Post-fix the
    regular adiabatic mode vanishes at zero amplitude as required."""

    seed_zero = make_camb_regular_adiabatic_seed(
        k_comoving=k_comoving,
        eta_initial=261.0,
        a_initial=1.0e-3,
        L_max=6,
        b_k_sq=0.0,
    )
    obs_zero = seed_observables(seed_zero, L_max=6)

    # Every observable that scales with the curvature amplitude must
    # vanish at b_k_sq=0. Round-9 only tracked pi_nu and G_3 in the
    # xfail marker (the bug surface). Round-10 widens the assertion to
    # all 11 amplitude-dependent fields per audit #3 recommendation 1
    # (full b_k_sq=0 zero check).
    amplitude_dependent = (
        "delta_gamma", "delta_b", "delta_c", "delta_nu",
        "theta_gamma", "theta_b", "theta_c", "theta_nu",
        "pi_nu", "G_3", "Z", "eta_cov",
        "pi_gamma", "E_2",
    )
    for field in amplitude_dependent:
        assert obs_zero[field] == 0.0, (
            f"{field} = {obs_zero[field]!r} must vanish at b_k_sq=0 "
            f"for the regular adiabatic mode (MB-95 §7)"
        )


@pytest.mark.parametrize("k_comoving", (1.0e-4, 1.0e-3, 1.0e-2))
def test_fb53_packed_state_zero_at_zero_amplitude(k_comoving: float) -> None:
    """Audit #3 recommendation 2: the full packed seed vector at
    b_k_sq=0 must contain zeros in every amplitude-dependent slot.
    Catches future regressions that bypass seed_observables (e.g. a
    new field added to pack_regular_adiabatic_seed_from_formulae but
    forgotten to scale by B_K_sq)."""

    seed_zero = make_camb_regular_adiabatic_seed(
        k_comoving=k_comoving,
        eta_initial=261.0,
        a_initial=1.0e-3,
        L_max=6,
        b_k_sq=0.0,
    )
    # The single non-zero entry permitted is the scale factor a at the
    # background slot (slot 0 of pack_combined_state). Everything else
    # — photon_T, photon_E, neutrino_reduced, plus the 6 metric/matter
    # extras — must be zero.
    arr = np.asarray(seed_zero, dtype=np.float64)
    a_value = float(arr[0])
    assert a_value == pytest.approx(1.0e-3, rel=1e-14), (
        f"background a_initial slot was overwritten: {a_value}"
    )
    perturbation_slots = arr.copy()
    perturbation_slots[0] = 0.0
    max_abs = float(np.max(np.abs(perturbation_slots)))
    assert max_abs == 0.0, (
        f"packed seed at b_k_sq=0 contains non-zero perturbation "
        f"(max |entry| = {max_abs}); the regular adiabatic mode must "
        f"vanish identically at zero amplitude"
    )


@pytest.mark.parametrize("k_comoving", (1.0e-4, 1.0e-3, 1.0e-2))
def test_fb53_seed_scales_linearly_with_b_k_sq(k_comoving: float) -> None:
    """Audit #3 recommendation 5: probe a non-unit amplitude
    (b_k_sq=2) and verify every linear-in-amplitude observable
    scales by exactly 2× vs b_k_sq=1. This is the key regression
    that prevents future amplitude leaks: the bug went undetected
    for so long because no prior test exercised b_k_sq ≠ 1.

    Excluded fields (trivially zero):
      - ``Sigma_plus`` / ``Sigma_minus`` are FLRW background fields,
        identically zero regardless of amplitude.

    History: Round-10 fixed ``π_ν`` and ``G_3``; Round-11 fixed
    ``eta_cov``'s inner ``B_K_sq → 1.0`` (auditor #2 follow-up). With
    both fixes in place, all amplitude-dependent fields scale linearly.
    """

    obs_unit = seed_observables(
        make_camb_regular_adiabatic_seed(
            k_comoving=k_comoving,
            eta_initial=261.0,
            a_initial=1.0e-3,
            L_max=6,
            b_k_sq=1.0,
        ),
        L_max=6,
    )
    obs_double = seed_observables(
        make_camb_regular_adiabatic_seed(
            k_comoving=k_comoving,
            eta_initial=261.0,
            a_initial=1.0e-3,
            L_max=6,
            b_k_sq=2.0,
        ),
        L_max=6,
    )
    amplitude_linear = (
        "delta_gamma", "delta_b", "delta_c", "delta_nu",
        "theta_gamma", "theta_b", "theta_c", "theta_nu",
        "pi_nu", "G_3", "Z", "eta_cov",
        "pi_gamma", "E_2",
    )
    for field in amplitude_linear:
        unit_val = obs_unit[field]
        double_val = obs_double[field]
        if unit_val == 0.0:
            assert double_val == 0.0, (
                f"{field}: unit=0 but double={double_val!r}"
            )
            continue
        ratio = double_val / unit_val
        assert ratio == pytest.approx(2.0, rel=1.0e-12, abs=1.0e-18), (
            f"{field} did not scale linearly: "
            f"obs(b=1)={unit_val!r}, obs(b=2)={double_val!r}, "
            f"ratio={ratio!r} (expected 2.0)"
        )
