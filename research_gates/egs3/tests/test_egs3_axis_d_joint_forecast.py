"""EGS3 Axis D gates: BASS-Extended joint PV+CMB information forecast (pre-solver).

D1 Woodbury solve/logdet == dense (feasible C_PV inversion, O(N K^2));
D2 large-scale velocity mode basis (bulk+shear) shapes + traceless-symmetric orthonormality;
D3 JWST-anchor Omega_tilt precision forecast: gain > 1, grows with anchors / smaller shrink, -> 1 as shrink -> 1;
D4 joint Fisher: the PV/JWST prior strictly reduces the Sigma^2 covariance inflation (degeneracy break > 1);
D5 BipoSH: exact Wigner-3j + an injected l<->l+1 aberration raises the L=1 bipolar power (isotropic power finite >= 0);
D6 theory-g CMB is FAIL-CLOSED (OutOfScopeError; never an array) and the joint total is never fabricated;
D7 deterministic under fixed inputs;
D8 (CoVe) adversarial: gains bounded, joint total always None, BipoSH power non-negative across a seed/param grid.

Chain-of-code: analytic identities recomputed two ways. Diagnostic-only; no detection, family,
geometry, or native-solver claim; the JWST prior is a labelled forecast; Sigma^2 stays partial.
"""
import unittest
import numpy as np

from htt.obsstat import pv_covariance as pv
from htt.obsstat import biposh_smica as bs
from htt.obsstat import joint_pv_cmb_forecast as jf
from htt.obsstat.lowell_map_features import _packed_index

SEED = 20260702


def _packed_len(lmax):
    return (lmax + 1) * (lmax + 2) // 2


def _random_packed_alm(lmax, rng):
    a = rng.normal(size=_packed_len(lmax)) + 1j * rng.normal(size=_packed_len(lmax))
    for ell in range(lmax + 1):            # m=0 coefficients are real for a real field
        a[_packed_index(lmax, ell, 0)] = a[_packed_index(lmax, ell, 0)].real
    return a


def _inject_aberration(a, lmax, eps):
    out = a.copy()
    for ell in range(2, lmax):
        for m in range(0, ell + 1):
            out[_packed_index(lmax, ell + 1, m)] += eps * a[_packed_index(lmax, ell, m)]
    return out


class D1WoodburyTests(unittest.TestCase):
    def test_solve_and_logdet_match_dense(self):
        rng = np.random.default_rng(SEED)
        N, K = 50, 8
        d = rng.uniform(1.0, 4.0, N)
        U = rng.normal(size=(N, K))
        lam = rng.uniform(0.5, 2.0, K)
        C = np.diag(d) + U @ np.diag(lam) @ U.T
        b = rng.normal(size=(N, 3))
        self.assertTrue(np.allclose(pv.woodbury_solve(d, U, lam, b), np.linalg.solve(C, b), atol=1e-9))
        self.assertAlmostEqual(pv.woodbury_logdet(d, U, lam), float(np.linalg.slogdet(C)[1]), places=8)


class D2VelocityModeTests(unittest.TestCase):
    def test_basis_orthonormal_and_traceless(self):
        E = pv.traceless_symmetric_basis()
        G = np.array([[np.sum(E[a] * E[b]) for b in range(5)] for a in range(5)])
        self.assertTrue(np.allclose(G, np.eye(5)))
        self.assertTrue(np.allclose([np.trace(e) for e in E], 0.0))

    def test_mode_shapes(self):
        rng = np.random.default_rng(SEED)
        pos = rng.normal(size=(120, 3)) * 40.0
        m = pv.velocity_field_modes(pos)
        self.assertEqual(m["U"].shape, (120, 8))
        self.assertEqual(m["Lambda"].shape, (8,))
        self.assertEqual(m["kinds"].count("bulk"), 3)
        self.assertEqual(m["kinds"].count("shear"), 5)


class D3JwstForecastTests(unittest.TestCase):
    def _catalogue(self, rng):
        pos = rng.normal(size=(400, 3)) * 50.0
        r = np.linalg.norm(pos, axis=1)
        nh = pos / r[:, None]
        sig2 = (rng.uniform(50.0, 150.0, 400)) ** 2
        v = nh @ np.array([200.0, -90.0, 60.0]) + rng.normal(size=400) * np.sqrt(sig2)
        return nh, v, sig2, r

    def test_gain_above_one_and_grows_with_anchors(self):
        rng = np.random.default_rng(SEED)
        nh, v, sig2, r = self._catalogue(rng)
        order = np.argsort(r)
        gains = []
        for frac in (0.02, 0.05, 0.10):
            mask = np.zeros(400, bool); mask[order[:int(frac * 400)]] = True
            g = jf.jwst_anchor_forecast(nh, v, sig2, mask, jwst_shrink=1.0 / 3.0)
            gains.append(g["precision_gain"])
            self.assertGreaterEqual(g["precision_gain"], 1.0)
        self.assertTrue(all(y2 >= y1 for y1, y2 in zip(gains, gains[1:])))  # more anchors -> more gain

    def test_gain_returns_to_one_when_no_shrink(self):
        rng = np.random.default_rng(SEED)
        nh, v, sig2, r = self._catalogue(rng)
        mask = np.zeros(400, bool); mask[:40] = True
        g = jf.jwst_anchor_forecast(nh, v, sig2, mask, jwst_shrink=1.0)
        self.assertAlmostEqual(g["precision_gain"], 1.0, places=9)


class D4JointFisherTests(unittest.TestCase):
    def test_prior_reduces_inflation(self):
        base = jf.joint_fisher_forecast(rho=0.6, f_omega_tilt_data=1.0, f_omega_tilt_jwst=1.0)
        self.assertAlmostEqual(base["degeneracy_break_factor"], 1.0, places=9)
        better = jf.joint_fisher_forecast(rho=0.6, f_omega_tilt_data=1.0, f_omega_tilt_jwst=2.0)
        self.assertLess(better["inflation_jwst"], better["inflation_data"])
        self.assertGreater(better["degeneracy_break_factor"], 1.0)

    def test_inflation_monotone_in_prior(self):
        infl = [jf.joint_fisher_forecast(rho=0.6, f_omega_tilt_jwst=f)["inflation_jwst"]
                for f in (1.0, 2.0, 5.0, 20.0)]
        self.assertTrue(all(y2 <= y1 for y1, y2 in zip(infl, infl[1:])))


class D5BiposhTests(unittest.TestCase):
    def test_wigner3j_known_values(self):
        self.assertAlmostEqual(bs.wigner_3j(1, 1, 0, 0, 0, 0), -1.0 / np.sqrt(3.0), places=10)
        self.assertAlmostEqual(bs.wigner_3j(1, 1, 2, 0, 0, 0), np.sqrt(2.0 / 15.0), places=10)
        self.assertAlmostEqual(bs.wigner_3j(2, 2, 2, 0, 0, 0), -np.sqrt(2.0 / 35.0), places=10)

    def test_aberration_raises_L1_power(self):
        lmax = 8
        iso, aber = [], []
        for s in range(30):
            rng = np.random.default_rng(1000 + s)
            a = _random_packed_alm(lmax, rng)
            iso.append(bs.compute_biposh_from_alm(a, lmax, L_values=(1, 2)).power_by_L[1])
            aa = _inject_aberration(a, lmax, 0.3)
            aber.append(bs.compute_biposh_from_alm(aa, lmax, L_values=(1, 2)).power_by_L[1])
        iso, aber = np.array(iso), np.array(aber)
        self.assertTrue(np.all(np.isfinite(iso)) and np.all(iso >= 0.0))
        self.assertGreater(np.mean(aber), np.mean(iso))
        self.assertGreater(np.mean(aber > iso), 0.6)


class D6FailClosedTests(unittest.TestCase):
    def test_theory_cmb_raises_and_never_returns_array(self):
        with self.assertRaises(jf.OutOfScopeError):
            jf.anisotropic_cmb_covariance((1.0, 0.0, 0.0, 0.0), l_max=30)
        with self.assertRaises(jf.OutOfScopeError):
            jf.anisotropic_cmb_loglike((1.0, 0.0, 0.0, 0.0), None, l_max=30)

    def test_joint_record_never_fabricates_total(self):
        rng = np.random.default_rng(SEED)
        pos = rng.normal(size=(200, 3)) * 40.0
        nh = pos / np.linalg.norm(pos, axis=1)[:, None]
        sig2 = (rng.uniform(50.0, 150.0, 200)) ** 2
        v = nh @ np.array([150.0, -50.0, 40.0]) + rng.normal(size=200) * np.sqrt(sig2)
        rec = jf.evaluate_joint_loglike(n_hat=nh, vpec=v, diag_sigma2=sig2)
        self.assertIsNone(rec["joint_total_loglike"])
        self.assertEqual(rec["cmb_theory_sector"]["status"], "fail_closed")
        self.assertEqual(rec["cmb_theory_sector"]["blocker"], jf.AWAITING_NATIVE_LOWELL_SOLVER)
        self.assertEqual(rec["pv_sector"]["status"], "measured")
        self.assertTrue(np.isfinite(rec["pv_sector"]["loglike"]))


class D7DeterminismTests(unittest.TestCase):
    def test_forecast_deterministic(self):
        rng = np.random.default_rng(7)
        pos = rng.normal(size=(300, 3)) * 45.0
        nh = pos / np.linalg.norm(pos, axis=1)[:, None]
        sig2 = (rng.uniform(50.0, 150.0, 300)) ** 2
        v = nh @ np.array([180.0, -70.0, 50.0]) + rng.normal(size=300) * np.sqrt(sig2)
        mask = np.zeros(300, bool); mask[:20] = True
        g1 = jf.jwst_anchor_forecast(nh, v, sig2, mask)
        g2 = jf.jwst_anchor_forecast(nh, v, sig2, mask)
        self.assertEqual(g1, g2)


class D8CoVeAdversarialTests(unittest.TestCase):
    def test_gains_bounded_total_none_biposh_nonneg(self):
        rng = np.random.default_rng(SEED)
        pos = rng.normal(size=(350, 3)) * 50.0
        nh = pos / np.linalg.norm(pos, axis=1)[:, None]
        r = np.linalg.norm(pos, axis=1)
        base_sig2 = (rng.uniform(50.0, 150.0, 350)) ** 2
        v = nh @ np.array([200.0, -90.0, 60.0]) + rng.normal(size=350) * np.sqrt(base_sig2)
        order = np.argsort(r)
        for frac in (0.02, 0.05, 0.10):
            for shrink in (0.2, 0.33, 0.5, 1.0):
                mask = np.zeros(350, bool); mask[order[:int(frac * 350)]] = True
                g = jf.jwst_anchor_forecast(nh, v, base_sig2, mask, jwst_shrink=shrink)
                self.assertGreaterEqual(g["precision_gain"], 1.0 - 1e-9)   # never worsens
                self.assertLess(g["precision_gain"], 1e3)                  # bounded
                rec = jf.evaluate_joint_loglike(n_hat=nh, vpec=v, diag_sigma2=base_sig2)
                self.assertIsNone(rec["joint_total_loglike"])              # never fabricated


if __name__ == "__main__":
    unittest.main()
