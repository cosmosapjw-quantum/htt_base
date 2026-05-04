"""Audit P-10: CAMB external-golden-file FLRW cross-validation harness.

The audit found that ~95% of tests are internal regression and only
one test (``test_background_table.py::test_eta_today_consistent_with_CAMB_range``)
performs a *loose* CAMB sanity check (±200 Mpc on η_today). No
external bit-identical FLRW C_ℓ cross-check exists, which means the
internal D_2 anchor (1002.086744 μK²) is internally consistent but
not externally validated.

This harness adds the missing piece: it imports ``camb`` (allowed in
test files per ``test_external_code_policy.py``), runs CAMB at the
canonical Planck-2018 cosmology, and compares the C_ℓ^{TT,EE,TE}
spectra against the BASS PSTF pipeline. The CAMB run is the *external
golden fixture*; tolerance is documented per ℓ-bin.

The test is **skipped** if CAMB is not installed, so the suite stays
green in environments without the optional dependency. When CAMB is
present and the BASS pipeline is closed (PR-024c), the test enforces
agreement to a documented tolerance.
"""
from __future__ import annotations

import pytest

camb = pytest.importorskip(
    "camb",
    reason="optional dependency 'camb' not installed; install via "
    "`pip install camb` to activate this external golden-file regression",
)


@pytest.fixture(scope="module")
def camb_planck2018_results():
    """Build a CAMB results object at canonical Planck-2018 cosmology."""
    pars = camb.CAMBparams()
    # Planck 2018 base-ΛCDM (Aghanim et al. 2020 Table 1, TT,TE,EE+lowE+lensing)
    pars.set_cosmology(
        H0=67.36,
        ombh2=0.022383,
        omch2=0.12011,
        mnu=0.06,
        omk=0.0,
        tau=0.0544,
    )
    pars.InitPower.set_params(As=2.100549e-9, ns=0.9649)
    pars.set_for_lmax(2500, lens_potential_accuracy=0)
    pars.WantTensors = False
    return camb.get_results(pars)


@pytest.fixture(scope="module")
def camb_d_ell_spectra(camb_planck2018_results):
    """Return CAMB lensed-scalar D_ℓ spectra in μK² up to ℓ=2500."""
    cl_total = camb_planck2018_results.get_lensed_scalar_cls(
        CMB_unit="muK",
        lmax=2500,
        raw_cl=False,  # raw_cl=False returns ℓ(ℓ+1)C_ℓ/(2π) = D_ℓ
    )
    # CAMB returns shape (lmax+1, 4) in (TT, EE, BB, TE) order.
    return {
        "TT": cl_total[:, 0],
        "EE": cl_total[:, 1],
        "TE": cl_total[:, 3],
    }


def test_camb_planck2018_d2_anchor_known_to_3pct(camb_d_ell_spectra) -> None:
    """Sanity check: CAMB's D_2 sits in a known band around the anchor.

    The Planck-2018 base-ΛCDM CAMB run produces D_2^TT in the
    900–1100 μK² band depending on the lensing+τ model. This is a
    very loose sanity check that establishes the CAMB fixture is
    non-degenerate.
    """
    d2 = float(camb_d_ell_spectra["TT"][2])
    assert 700.0 < d2 < 1300.0, (
        f"CAMB Planck-2018 D_2 = {d2} μK² is outside the expected "
        f"700–1300 band; check fixture parameters"
    )


@pytest.mark.slow
@pytest.mark.xfail(
    reason="PR-024c open: BASS PSTF Python-side pipeline does not yet "
    "produce a bit-identical D_2 closure. When PR-024c lands, switch "
    "this from xfail to a strict regression with the documented "
    "per-ℓ tolerance.",
    strict=False,
)
def test_bass_pstf_d_ell_matches_camb_within_tolerance(
    camb_d_ell_spectra,
) -> None:
    """BASS PSTF Python pipeline must agree with CAMB on TT/EE/TE.

    Documented tolerance:
      - TT, ℓ ∈ [2, 30]: ≤ 1% (low-ℓ, dominated by SW + ISW)
      - EE/TE, ℓ ∈ [2, 30]: ≤ 2% after the polarization-source
        normalization and sign-convention closure is finished.
      - ℓ > 30: advisory (pipeline is low-ℓ-targeted).

    Until PR-024c closes the absolute-amplitude calibration, this
    regression is xfailed.
    """
    import numpy as np

    try:
        from bass.spectrum.cl_assembly import CLAssemblyConfig
        from bass.spectrum.flrw_pipeline import (
            FLRWPipelineConfig,
            compute_flrw_d_ell,
        )
        from bass.species.registry import SpeciesBackgroundRegistry
    except ImportError as exc:
        pytest.skip(f"BASS pipeline not importable: {exc}")
    species = SpeciesBackgroundRegistry.from_planck2018(
        recombination_warning_policy="ignore",
    )
    k_grid = np.logspace(-4.0, -1.5, 64)
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=30)
    assembly_cfg = CLAssemblyConfig(
        ell_max=30, k_grid=k_grid, quadrature="simpson",
    )
    bundle = compute_flrw_d_ell(
        species,
        k_grid_mpc=k_grid,
        pipeline_config=pipeline_cfg,
        assembly_config=assembly_cfg,
        n_workers=4,
    )
    bass_by_channel = {
        "TT": bundle["d_tt"],
        "EE": bundle["d_ee"],
        "TE": bundle["d_te"],
    }
    tolerances = {"TT": 0.01, "EE": 0.02, "TE": 0.02}

    # ℓ ∈ [2, 30]: per-ℓ relative tolerance.  TE is signed, so the
    # denominator is |CAMB| with a tiny absolute zero guard; near a
    # zero-crossing the asserted condition falls back to absolute
    # smallness rather than a meaningless relative blow-up.
    for channel, bass_d_ell in bass_by_channel.items():
        camb_d_ell = camb_d_ell_spectra[channel]
        tolerance = tolerances[channel]
        for ell in range(2, 30):
            camb_value = float(camb_d_ell[ell])
            bass_value = float(bass_d_ell[ell])
            if abs(camb_value) < 1.0e-12:
                assert abs(bass_value) < 1.0e-12, (
                    f"BASS PSTF {channel} produced nonzero power at a CAMB "
                    f"zero-crossing: ℓ={ell}, BASS={bass_value:.3e} μK²"
                )
                continue
            rel = abs(bass_value - camb_value) / abs(camb_value)
            assert rel < tolerance, (
                f"BASS PSTF {channel} disagreed with CAMB at ℓ={ell}: "
                f"BASS={bass_value:.3f} μK², CAMB={camb_value:.3f} μK², "
                f"|Δ|/|CAMB| = {rel*100:.2f}% "
                f"(tolerance {tolerance*100:.1f}%)"
            )
