"""Fast synthetic tests for the R108 radio lane GLM/C1 helpers, the command logger and the TAP overflow check (< 30 s)."""
from __future__ import annotations

import math

import healpy as hp
import numpy as np
import pytest

from scripts.r108 import radio_cmdlog as L
from scripts.r108 import radio_racs_dipole as D
from scripts.r108 import radio_racs_fetch as F


def sky(nside=16):
    return np.column_stack(hp.pix2vec(nside, np.arange(hp.nside2npix(nside))))


def test_poisson_glm_recovers_injected_dipole():
    rng = np.random.default_rng(20261124)
    vec = sky(16)
    d = np.array([0.02, -0.015, 0.01])
    mu = 400.0 * np.exp(vec @ d)
    y = rng.poisson(mu).astype(float)
    beta, cov, pearson = D.poisson_glm(y, D.design(vec, False))
    z = (beta[1:4] - d) / np.sqrt(np.diag(cov[1:4, 1:4]))
    assert np.all(np.abs(z) < 4.5)
    assert 0.9 < pearson < 1.1


def test_binomial_glm_recovers_injected_logit_dipole():
    rng = np.random.default_rng([20261124, 1])
    vec = sky(16)
    g = np.array([0.1, 0.05, -0.08])
    eta = -2.0 + vec @ g
    n = rng.poisson(300, size=len(vec)).astype(float)
    k = rng.binomial(n.astype(int), 1 / (1 + np.exp(-eta))).astype(float)
    beta, cov, pearson, p0 = D.binomial_glm(k, n, D.design(vec, True))
    z = (beta[1:4] - g) / np.sqrt(np.diag(cov[1:4, 1:4]))
    assert np.all(np.abs(z) < 4.5)


def test_c1_summary_definitions():
    d = np.array([3e-3, -4e-3, 0.0])
    s = D.c1_summary(d, np.eye(3) * 1e-7, 1.0, d_kin=np.array([3e-3, -4e-3, 0.0]))
    assert s["C1_raw"] == pytest.approx(4 * math.pi / 9 * 25e-6)
    assert s["C1_debiased_poisson"] == pytest.approx(4 * math.pi / 9 * (25e-6 - 3e-7))
    assert s["C1_residual_raw"] == pytest.approx(0.0)
    lo, hi = s["C1_raw_one_realisation_interval_68"]
    assert lo < s["C1_raw"] < hi
    assert s["C1_transverse_raw"] == pytest.approx(2 * math.pi / 3 * 25e-6)
    assert s["C1_transverse_debiased_poisson"] == pytest.approx(2 * math.pi / 3 * (25e-6 - 2e-7))


def test_transverse_c1_unbiased_for_isotropic_dipole():
    # isotropic l=1 field: each component variance 3 C1/(4 pi) -> E[C1_transverse_raw] = C1
    rng = np.random.default_rng(11)
    c1 = 2e-3
    d = rng.normal(0, math.sqrt(3 * c1 / (4 * math.pi)), size=(20000, 3))
    est = [D.c1_summary(v, np.zeros((3, 3)), 1.0)["C1_transverse_raw"] for v in d[:4000]]
    assert abs(np.mean(est) / c1 - 1) < 0.05


def test_offdiag_fraction_matches_r106_definition():
    from scripts.r106.radio_null_mocks import offdiag_fraction_contrast
    rng = np.random.default_rng(7)
    j = rng.integers(0, 50, size=(4, 4, 30))
    j[1:, 0] = 0  # R65 structure: integrated >= peak bin
    a = D.offdiag_fraction(j)
    b = offdiag_fraction_contrast(j)
    assert a["df"] == pytest.approx(b["df"])


def test_cmdlog_time_line_parser():
    rec = L.parse_time_line("noise\npython3 -m x --y|rc=0|wall=12.5|maxrss_kB=1234\n")
    assert rec == dict(cmd="python3 -m x --y", rc=0, wall_s=12.5, maxrss_kB=1234)
    assert L.parse_time_line("nothing") is None


def test_tap_overflow_status(tmp_path):
    from astropy.io.votable.tree import Info, Resource, TableElement, VOTableFile
    from astropy.table import Table
    vot = VOTableFile()
    res = Resource()
    vot.resources.append(res)
    res.infos.append(Info(name="QUERY_STATUS", value="OVERFLOW"))
    res.tables.append(TableElement.from_table(vot, Table({"a": [1, 2]})))
    p = tmp_path / "t.vot"
    vot.to_xml(str(p))
    assert F.check_overflow(p) == "OVERFLOW"
    assert len(F.parse_votable(p)) == 2
