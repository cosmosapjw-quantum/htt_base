"""EGS3 Axis H gates (REV-R191): external-data lanes (DESI / ACT / JWST).

H-EXT-1 DESI number-count dipole: the linear estimator RECOVERS an injected
        dipole on a full-sky mock; the real footprint value is window-dominated
        (fsky ~ 0.19) and terminates in BLOCKED_MISSING_DESI_RANDOMS;
H-EXT-2 ACT DR6 kappa: the released a_lm loads (lmax=4000) with an auto-
        bandpower readout; the low-multipole isotropy statistic terminates in
        BLOCKED_MISSING_ACT_LENSING_SIMS;
H-EXT-3 JWST: catalogue linkage only; downstream forecast absent and finding OPEN;
H-EXT-4 seal PASS + scope + forbidden-token guard; no substitute estimate
        beyond the labelled mock.
"""
import unittest

from htt.obsstat.egs3_external_lanes import (
    act_kappa_auto_bandpower,
    desi_number_count_dipole,
    external_lanes_seal,
    jwst_anchor_connection,
)

_SEAL = external_lanes_seal()


def _require(lane: dict, key: str):
    """Skip (not fail) when the real dataset is absent, e.g. in a data-less
    CI checkout -- the lane returns a BLOCKED_MISSING_* status without the
    computed keys. The lane is exercised wherever the workdir data is present."""
    if key not in lane:
        raise unittest.SkipTest(f"external data absent: {lane.get('status')}")


class HEXT1Desi(unittest.TestCase):
    def test_mock_verified(self):
        d = desi_number_count_dipole()
        _require(d, "mock_verification")
        mv = d["mock_verification"]
        self.assertTrue(mv["recovers_injected_dipole"])
        self.assertAlmostEqual(mv["recovered_amplitude"],
                               mv["injected_amplitude"], delta=3e-3)
        self.assertTrue(d["real_footprint"]["window_dominated"])
        self.assertLess(d["real_footprint"]["fsky"], 0.5)     # partial footprint
        self.assertIn(d["status"], ("BLOCKED_MISSING_DESI_RANDOMS",
                                    "MEASURED_WINDOW_CORRECTED"))

    def test_window_corrected_when_randoms_present(self):
        d = desi_number_count_dipole()
        _require(d, "window_corrected_measurement")   # skip if randoms absent
        m = d["window_corrected_measurement"]
        # the window correction must slash the raw footprint dipole toward the
        # cosmological scale (~7e-3), not leave it window-dominated (~2)
        self.assertLess(m["dipole_amplitude"], 0.05)
        self.assertGreater(m["window_suppression_factor"], 20)
        self.assertEqual(d["status"], "MEASURED_WINDOW_CORRECTED")
        # clustering/kinematic-mixing + mask caveats must be carried
        self.assertTrue(any("clustering" in c.lower() for c in m["caveats"]))

    def test_footprint_dipole_not_claimed_cosmological(self):
        d = desi_number_count_dipole()
        _require(d, "real_footprint")
        # the raw footprint dipole is orders of magnitude above the
        # cosmological reference scale -> must be flagged, not claimed
        self.assertGreater(d["real_footprint"]["raw_dipole_amplitude"],
                           10 * d["real_footprint"]["cosmological_reference_scale"])
        self.assertIn("window", d["scope_not_claimed"].lower())


class HEXT2Act(unittest.TestCase):
    def test_kappa_loads(self):
        a = act_kappa_auto_bandpower()
        _require(a, "lmax")
        self.assertEqual(a["lmax"], 4000)
        self.assertTrue(a["auto_bandpower_C_L_raw"])          # non-empty readout
        self.assertTrue(a["low_ell_mean_field_dominated"])
        self.assertIn(a["status"], ("BLOCKED_MISSING_ACT_LENSING_SIMS",
                                    "MEASURED_MEAN_FIELD_DEBIASED"))

    def test_isotropy_measured_when_sims_present(self):
        a = act_kappa_auto_bandpower()
        _require(a, "low_ell_isotropy_measurement")   # skip if sims absent
        m = a["low_ell_isotropy_measurement"]
        self.assertEqual(m["n_sims"], 400)
        self.assertEqual(m["ell_band"][0], 2)          # dipole ell=1 excluded
        self.assertTrue(0.0 <= m["p_value_data_vs_isotropic_sims"] <= 1.0)
        self.assertEqual(a["status"], "MEASURED_MEAN_FIELD_DEBIASED")
        self.assertTrue(any("dipole" in c.lower() for c in m["caveats"]))


class HEXT3Jwst(unittest.TestCase):
    def test_anchors_are_catalogue_linkage_only(self):
        j = jwst_anchor_connection()
        self.assertEqual(j["n_anchors"], 14)
        self.assertEqual(j["status"], "CATALOGUE_LINKAGE_ONLY")
        self.assertEqual(j["finding_status"], "OPEN")
        self.assertIn("N-DATA-CF4-DOWNSTREAM", j["finding_ids"])
        self.assertFalse(j["downstream_public_use"])
        self.assertIsNone(j["downstream_forecast"])


class HEXT4SealScope(unittest.TestCase):
    FORBIDDEN = ("posterior", "detection", "native solver", "family assignment")

    def test_seal_pass_and_scope(self):
        _require(_SEAL["desi_number_count_dipole"], "mock_verification")
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "EXT-LANES")
        self.assertIn("registered blockers", _SEAL["scope_not_claimed"])

    def test_docstring_guard(self):
        import htt.obsstat.egs3_external_lanes as mod
        doc = (mod.__doc__ or "").lower()
        for tok in self.FORBIDDEN:
            self.assertNotIn(tok, doc)


if __name__ == "__main__":
    unittest.main()
