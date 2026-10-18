import json
import math
from pathlib import Path
from statistics import NormalDist
import unittest
import tempfile

import numpy as np
from calibration_frontier import compute, compatible_interval, critical_value, spectral_radius, validate_source, read_pinned_source, SOURCE_BLOB

SOURCE = Path(__file__).parent / "source" / "H02_ACTUAL_SELECTED_SOURCE_FISHER.json"


class CalibrationFrontierTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(SOURCE.read_text())

    def test_real_source_identity_and_missing_observation_state(self):
        result = compute(self.source)
        self.assertEqual(result["selected_groups"], 35970)
        self.assertEqual(len(result["rows"]), 64)
        self.assertIsNone(result["observed_common_parameter_interval"])
        self.assertIsNone(result["minimum_calibration_required_by_data"])
        self.source["source_sha256"] = "wrong"
        with self.assertRaises(ValueError):
            validate_source(self.source)

    def test_exact_file_identity_rejects_changed_eigenvalue(self):
        source, raw, blob = read_pinned_source(SOURCE)
        self.assertEqual(blob, SOURCE_BLOB)
        source["method_gram_eigen_minmax"]["TF"][0] *= 2
        # Keep the NPZ label unchanged: it is not proof of these JSON bytes.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.json"
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, "Git blob mismatch"):
                read_pinned_source(path)

    def test_gaussian_familywise_probability_budget(self):
        for comparisons in (4, 32):
            z = critical_value(.05, comparisons, "gaussian_marginals")
            union_tail = comparisons * 2 * (1 - NormalDist().cdf(z))
            self.assertAlmostEqual(union_tail, .05, places=13)
            # Dependence can be perfect; no product-of-probabilities step.
            self.assertGreaterEqual(1-union_tail, .95-1e-14)

    def test_variance_only_budget(self):
        for comparisons in (4, 32):
            k = critical_value(.05, comparisons, "variance_only")
            self.assertAlmostEqual(comparisons/k**2, .05)

    def test_spectral_bound_and_saturating_direction(self):
        # Rotated SPD Gram: exact c^T G^-1 c lies inside spectral limits.
        rng = np.random.default_rng(23)
        Q, _ = np.linalg.qr(rng.normal(size=(8,8)))
        eig = np.array([2.,3.,5.,7.,11.,13.,17.,19.])
        G = (Q*eig) @ Q.T
        for c in list(rng.normal(size=(30,8))) + [Q[:,0], Q[:,-1]]:
            c = c/np.linalg.norm(c)
            variance = c @ np.linalg.solve(G,c)
            self.assertGreaterEqual(variance, 1/eig[-1]-1e-14)
            self.assertLessEqual(variance, 1/eig[0]+1e-14)
        self.assertAlmostEqual(Q[:,0] @ np.linalg.solve(G,Q[:,0]), 1/eig[0])

    def test_exact_box_witness_and_empty_set(self):
        centers = dict(a=.01, b=.03, c=-.01, d=.02)
        q = dict.fromkeys(centers, .005)
        for delta in (0., .01, .015, .02):
            out = compatible_interval(centers,q,dict.fromkeys(centers,delta))
            if delta < .015:
                self.assertTrue(out["empty"])
            else:
                self.assertFalse(out["empty"])
                for theta in (out["lower"],out["upper"]):
                    for method, b in centers.items():
                        residual=b-theta
                        calibration=np.clip(residual,-delta,delta)
                        self.assertLessEqual(abs(residual-calibration),q[method]+1e-14)

    def test_real_geometry_frontier_monotonic_and_raw_basis(self):
        rows = compute(self.source)["rows"]
        row = next(r for r in rows if r["law"]=="gaussian_marginals" and r["predeclared_contrasts"]==1 and r["method"]=="TF" and r["assumed_calibration_delta_mag"]==0.)
        self.assertAlmostEqual(row["noise_radius_upper_mag"],.036338469615610144,places=13)
        for method in ("FP","TF","SN","OTHER"):
            selected=[r for r in rows if r["law"]=="gaussian_marginals" and r["predeclared_contrasts"]==1 and r["method"]==method]
            self.assertEqual([r["assumed_calibration_delta_mag"] for r in selected],[0.,.01,.02,.05])
            for r in selected:
                self.assertAlmostEqual(r["total_radius_upper_mag"]-r["noise_radius_upper_mag"],r["assumed_calibration_delta_mag"])

    def test_reject_invalid_inputs(self):
        for args in [(0.,4,"gaussian_marginals"),(.05,0,"gaussian_marginals"),(.05,4,"bad")]:
            with self.assertRaises(ValueError): critical_value(*args)
        with self.assertRaises(ValueError): spectral_radius(0)
        with self.assertRaises(ValueError): compute(self.source,deltas=(-.01,))
        with self.assertRaises(ValueError): compatible_interval({}, {}, {})
        with self.assertRaises(ValueError): compatible_interval({"a":1},{"b":1},{"a":1})
        with self.assertRaises(ValueError): compatible_interval({"a":math.nan},{"a":1},{"a":1})


if __name__ == "__main__":
    unittest.main()
