#!/usr/bin/env python3
"""generate_camb_reference.py — CAMB Planck 2018 reference C_ℓ.

Produces the authoritative reference spectra for the W10-02 FLRW V-gate
(docs/BASS_PY_FAST_TRACK_2026-04-18.md §5.B.1 and
BASS_PY_HTT_TSC_RESEARCH_PLAN.md §7.1 D18). External-code policy:
**CAMB is used here as a validation oracle only, never as a science
engine.** bass_py's own first-principles pipeline must match these
numbers to < 5% at ℓ ≤ 10 and < 10% at ℓ ≤ 30 to pass the V-gate.

Usage
-----
    venv/bin/python scripts/generate_camb_reference.py \\
        --ell-max 30 \\
        --out data/camb_ref_planck2018.npz

Cosmological parameters (Planck 2018 TT,TE,EE,lowE+lensing):
    H0       = 67.36 km/s/Mpc
    ombh2    = 0.02237
    omch2    = 0.12
    m_nu_eV  = 0.06
    omk      = 0.0
    tau      = 0.0544
    A_s      = 2.1e-9
    n_s      = 0.9649

These match the SSOT in ``bass_py/htt/htt/core/ssot.py`` (class ``C``)
to within the published 1σ and are the same values used by
``scripts/bench_camb_vs_bass.py``.

Output NPZ archive contents
---------------------------
    ell          (N,) int — ℓ values [2, ell_max]
    C_TT         (N,) float — C_ℓ^{TT} in μK²
    C_EE         (N,) float — C_ℓ^{EE} in μK²
    C_TE         (N,) float — C_ℓ^{TE} in μK²
    D_TT         (N,) float — D_ℓ^{TT} = ℓ(ℓ+1)C_ℓ/(2π) in μK²
    D_EE         (N,) float — D_ℓ^{EE} in μK²
    D_TE         (N,) float — D_ℓ^{TE} in μK²
    eta_star     float — conformal time at last scattering (Mpc)
    eta_0        float — conformal time today (Mpc)
    z_star       float — last-scattering redshift
    H0           float — Hubble parameter (km/s/Mpc)
    ombh2        float — Ω_b h²
    omch2        float — Ω_c h²
    A_s          float — primordial amplitude
    n_s          float — scalar spectral index
    camb_version str   — CAMB version used
    lens_potential_accuracy int — CAMB accuracy flag
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


# Planck 2018 TT,TE,EE,lowE+lensing best-fit baseline
PLANCK2018 = {
    'H0': 67.36,
    'ombh2': 0.02237,
    'omch2': 0.12,
    'mnu': 0.06,
    'omk': 0.0,
    'tau': 0.0544,
    'As': 2.1e-9,
    'ns': 0.9649,
}


def generate_reference(
    ell_max: int = 30,
    accuracy_boost: float = 2.0,
    lens_potential_accuracy: int = 0,
    want_lensing: bool = False,
) -> dict:
    """Compute CAMB scalar C_ℓ^{TT,EE,TE} up to ell_max.

    Parameters
    ----------
    ell_max : int
        Highest multipole to return. V-gate target is ℓ=2..30.
    accuracy_boost : float
        CAMB AccuracyBoost × lSampleBoost × lAccuracyBoost. Default 2.0
        produces ~0.1% ℓ-space accuracy at low ℓ, plenty of headroom
        for the 5% V-gate target.
    lens_potential_accuracy : int
        0 = unlensed (clean scalar comparison); 1 = lensed.
    want_lensing : bool
        If False, returns scalar-only spectra (pure Boltzmann product
        without lensing convolution). Recommended for V-gate clarity.

    Returns
    -------
    dict with the fields listed in the module docstring.
    """
    import camb  # late import so --help doesn't require camb

    pars = camb.CAMBparams()
    pars.set_cosmology(
        H0=PLANCK2018['H0'],
        ombh2=PLANCK2018['ombh2'],
        omch2=PLANCK2018['omch2'],
        mnu=PLANCK2018['mnu'],
        omk=PLANCK2018['omk'],
        tau=PLANCK2018['tau'],
    )
    pars.InitPower.set_params(
        As=PLANCK2018['As'],
        ns=PLANCK2018['ns'],
    )
    # Use an extra buffer above ell_max to avoid edge artefacts at ℓ_max.
    pars.set_for_lmax(
        max(ell_max + 200, 2500),
        lens_potential_accuracy=lens_potential_accuracy,
    )
    pars.WantTensors = False
    pars.DoLensing = want_lensing
    pars.set_accuracy(
        AccuracyBoost=accuracy_boost,
        lSampleBoost=accuracy_boost,
        lAccuracyBoost=accuracy_boost,
    )

    results = camb.get_results(pars)
    # D_ℓ convention: μK² with CMB temperature already squared in
    # (CAMB's raw_cl=False default = D_ℓ form).
    if want_lensing:
        cls_all = results.get_lensed_scalar_cls(
            ell_max + 200, CMB_unit='muK', raw_cl=False,
        )
    else:
        cls_all = results.get_unlensed_scalar_cls(
            ell_max + 200, CMB_unit='muK', raw_cl=False,
        )
    # CAMB column order: TT, EE, BB, TE
    D_TT_full = cls_all[:, 0]
    D_EE_full = cls_all[:, 1]
    D_TE_full = cls_all[:, 3]

    ell = np.arange(2, ell_max + 1, dtype=np.int64)
    # D_ℓ = ℓ(ℓ+1) C_ℓ / (2π) (already in D-form from CAMB).
    D_TT = D_TT_full[ell]
    D_EE = D_EE_full[ell]
    D_TE = D_TE_full[ell]
    # Inverse to get plain C_ℓ (μK² per ℓ)
    norm = ell * (ell + 1) / (2.0 * np.pi)
    C_TT = D_TT / norm
    C_EE = D_EE / norm
    C_TE = D_TE / norm

    # Derived geometry: η_*, η_0, z_*
    z_star = float(results.get_derived_params()['zstar'])
    # Conformal distance to CMB as eta_0 - eta_star
    chi_star = float(results.conformal_time(z_star))
    eta_0 = float(results.conformal_time(0.0))
    eta_star = eta_0 - chi_star

    return {
        'ell': ell,
        'C_TT': C_TT,
        'C_EE': C_EE,
        'C_TE': C_TE,
        'D_TT': D_TT,
        'D_EE': D_EE,
        'D_TE': D_TE,
        'eta_star': eta_star,
        'eta_0': eta_0,
        'z_star': z_star,
        'H0': PLANCK2018['H0'],
        'ombh2': PLANCK2018['ombh2'],
        'omch2': PLANCK2018['omch2'],
        'mnu': PLANCK2018['mnu'],
        'omk': PLANCK2018['omk'],
        'tau': PLANCK2018['tau'],
        'As': PLANCK2018['As'],
        'ns': PLANCK2018['ns'],
        'accuracy_boost': accuracy_boost,
        'lens_potential_accuracy': lens_potential_accuracy,
        'lensed': want_lensing,
        'camb_version': camb.__version__,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ell-max', type=int, default=30,
                    help='highest ℓ (default 30 — matches W10-02 V-gate)')
    ap.add_argument('--accuracy-boost', type=float, default=2.0,
                    help='CAMB accuracy multiplier (default 2.0)')
    ap.add_argument('--lensed', action='store_true',
                    help='include lensing in scalar C_ℓ (default off)')
    ap.add_argument('--out', type=Path,
                    default=Path('data/camb_ref_planck2018.npz'),
                    help='output NPZ path')
    ap.add_argument('--quiet', action='store_true',
                    help='suppress per-ℓ diagnostic print')
    args = ap.parse_args()

    print(f'Generating CAMB Planck 2018 reference for ℓ=2..{args.ell_max} '
          f'(accuracy_boost={args.accuracy_boost}, lensed={args.lensed})...')
    ref = generate_reference(
        ell_max=args.ell_max,
        accuracy_boost=args.accuracy_boost,
        want_lensing=args.lensed,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, **ref)
    print(f'Saved → {args.out}')
    print(f'  CAMB {ref["camb_version"]}, z_* = {ref["z_star"]:.3f}, '
          f'η_* = {ref["eta_star"]:.3f} Mpc, η_0 = {ref["eta_0"]:.3f} Mpc')

    if not args.quiet:
        print(f'\n  ℓ        D_ℓ^TT [μK²]   D_ℓ^EE [μK²]   D_ℓ^TE [μK²]')
        for i, ell in enumerate(ref['ell']):
            if ell in (2, 3, 5, 10, 20, args.ell_max):
                print(f'  {int(ell):4d}   {ref["D_TT"][i]:12.4f}   '
                      f'{ref["D_EE"][i]:12.6f}   {ref["D_TE"][i]:12.4f}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
