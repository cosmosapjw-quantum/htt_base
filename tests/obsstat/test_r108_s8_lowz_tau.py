"""R108 lane s8: independent checks of the post-REI (z <= 4) Thomson-depth integrator.

* units: tau_flrw against a hand-written integrand with astropy CODATA-2018 constants and astropy
  Mpc / km conversions (same quad tolerance), plus an independent 400-node Gauss-Legendre rule;
* the R107 TF8 donor-matched depths (THEORY_FOUNDATIONS.md TF8) are reproduced to their 7 quoted digits;
* tau is affine in the donor value x_e(4), which is the exact explanation used in S8_LOWZ_TAU.json
  for case depths that differ from the TF8 band;
* the AXBI_CHECKPOINT_V2 fraction parser and x_e formula of scripts/r108/s8_lowz_tau.py.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

from bass.recombination import rei_lowz_continuation as lowz
from bass.recombination.rei_lowz_continuation import DonorMatchedContinuation, FlrwBackground, tau_flrw

astropy = pytest.importorskip("astropy")
import astropy.units as u  # noqa: E402
from astropy.constants import codata2018 as c18  # noqa: E402

from scripts.r108 import s8_lowz_tau as s8  # noqa: E402

# R107 test constants (htt/bass/recombination/test_rei_lowz_continuation.py:20-22)
N_H0 = 1.898198450714027e-7
F_HE = 0.08130135170951498
BG = FlrwBackground(67.4, 0.315, 0.000092)
DONOR = 1.08339435


def _astropy_tau(xe, n_h0_cm3, h0_km_s_mpc, om, orad):
    h0 = (h0_km_s_mpc * u.km / u.s / u.Mpc).to_value(1 / u.s)
    ol = 1.0 - om - orad
    pref = (c18.c * c18.sigma_T * n_h0_cm3 * u.cm ** -3 / (h0 / u.s)).to_value(u.dimensionless_unscaled)

    def integrand(z):
        return (1 + z) ** 2 * float(xe(z)) / math.sqrt(orad * (1 + z) ** 4 + om * (1 + z) ** 3 + ol)
    val, _ = quad(integrand, 0.0, 4.0, epsabs=0.0, epsrel=1e-12, limit=400)
    xg, wg = np.polynomial.legendre.leggauss(400)
    gl = 2.0 * float(np.sum(wg * np.array([integrand(z) for z in 2.0 * (xg + 1.0)])))
    return pref * val, pref * gl


def test_module_constants_are_codata2018_and_iau_mpc():
    assert lowz.C_LIGHT == c18.c.value
    assert lowz.SIGMA_T == c18.sigma_T.value
    assert lowz.MPC_M == (1 * u.Mpc).to_value(u.m)


@pytest.mark.parametrize("z_heii", [3.0, 3.5, 3.9])
def test_tau_integrator_units_against_astropy(z_heii):
    c = DonorMatchedContinuation(DONOR, F_HE, z_heii=z_heii)
    tau = tau_flrw(0.0, 4.0, c.x_e, N_H0, BG)
    tau_q, tau_gl = _astropy_tau(c.x_e, N_H0, 67.4, 0.315, 0.000092)
    assert abs(tau_q / tau - 1.0) <= 1e-15
    assert abs(tau_gl / tau - 1.0) <= 2e-14


def test_tf8_donor_band_is_reproduced_to_its_quoted_digits():
    for z_heii, quoted in s8.TF8_QUOTED.items():
        tau = tau_flrw(0.0, 4.0, DonorMatchedContinuation(DONOR, F_HE, z_heii=z_heii).x_e, N_H0, BG)
        assert round(tau, 7) == quoted


@pytest.mark.parametrize("z_heii", [3.0, 3.5, 3.9])
def test_tau_is_affine_in_the_donor_value(z_heii):
    xs = (1.0, DONOR, 1.0 + 2.0 * F_HE)
    t = [tau_flrw(0.0, 4.0, DonorMatchedContinuation(x, F_HE, z_heii=z_heii).x_e, N_H0, BG) for x in xs]
    slope = (t[2] - t[0]) / (xs[2] - xs[0])
    assert abs(t[0] + slope * (xs[1] - xs[0]) - t[1]) <= 1e-15 * t[1]
    assert slope > 0.0


def test_checkpoint_fraction_parser_and_xe(tmp_path: Path):
    line1 = "2.0e-1 4.2e16 0.0 9.99997e-1 9.7e-1 2.5e-2 3.5e-12 1.25e-5 1e-11 4e-6 7.5e3"
    p = tmp_path / "ck.txt"
    p.write_text("AXBI_CHECKPOINT_V2\n" + line1 + "\n1 2 3 0 5 6\n0\n0\n0\n")
    fr = s8.parse_checkpoint_fractions(p)
    assert fr == {"a": 0.2, "x_HII": 0.999997, "x_HeII": 0.97, "x_HeIII": 0.025}
    assert s8.xe_per_h(fr, F_HE) == 0.999997 + F_HE * (0.97 + 2 * 0.025)
    bad = tmp_path / "bad.txt"
    bad.write_text("AXBI_CHECKPOINT_V1\n" + line1 + "\n\n\n\n\n")
    with pytest.raises(ValueError):
        s8.parse_checkpoint_fractions(bad)


ZERO_CK = Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi/research/axbi_goal_20261014/runs/flrw/32d11e733155/"
               "ZERO_continuation_001/checkpoint.txt")


@pytest.mark.skipif(not ZERO_CK.exists(), reason="rei_bianchi ZERO restart checkpoint not on this machine")
def test_zero_case_offset_from_the_band_is_the_rounding_of_the_donor_value():
    x4 = s8.xe_per_h(s8.parse_checkpoint_fractions(ZERO_CK), F_HE)
    assert 0.0 < x4 - DONOR < 5e-9  # TF8 quotes the donor to 9 significant digits
    for z_heii in (3.0, 3.5, 3.9):
        t_case = tau_flrw(0.0, 4.0, DonorMatchedContinuation(x4, F_HE, z_heii=z_heii).x_e, N_H0, BG)
        t_donor = tau_flrw(0.0, 4.0, DonorMatchedContinuation(DONOR, F_HE, z_heii=z_heii).x_e, N_H0, BG)
        t1 = tau_flrw(0.0, 4.0, DonorMatchedContinuation(1.0, F_HE, z_heii=z_heii).x_e, N_H0, BG)
        slope = (t_donor - t1) / (DONOR - 1.0)
        assert abs((t_case - t_donor) - slope * (x4 - DONOR)) <= 1e-16
