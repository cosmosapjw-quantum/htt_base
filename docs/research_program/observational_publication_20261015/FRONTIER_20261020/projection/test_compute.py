import unittest

import numpy as np

from compute import C_KM_S, MU_FACTOR, background, directions, optical_after_flow_nuisance, rank_and_angles


class ProjectionTests(unittest.TestCase):
    def test_background_ratio_is_radially_ordered(self):
        z = np.array([0.01, 0.04, 0.1])
        a, h, _ = background(z)
        self.assertTrue(np.all(np.diff(h / a) > 0))
        self.assertRaises(ValueError, background, np.array([0.0, 0.1]))

    def test_exact_frozen_flow_local_span_and_rank(self):
        rng = np.random.default_rng(47)
        z = np.linspace(0.004, 0.1, 60)
        n = directions(rng.uniform(0, 360, len(z)), np.rad2deg(np.arcsin(rng.uniform(-1, 1, len(z)))))
        a, h, chi = background(z)
        k = -MU_FACTOR * (1 + a) / C_KM_S
        optical_local = MU_FACTOR * a[:, None] * n
        calibration = n
        constant_flow = k[:, None] * n
        np.testing.assert_allclose(optical_local, -(C_KM_S * constant_flow + MU_FACTOR * calibration), rtol=1e-12, atol=1e-12)
        blocks = {"optical_local": optical_local, "optical_history": MU_FACTOR * h[:, None] * n,
                  "calibration": calibration, "flow_constant": constant_flow,
                  "flow_linear": (k * chi / np.median(chi))[:, None] * n}
        cov = np.eye(len(z)) + 0.01 * np.ones((len(z), len(z)))
        nuisance = np.column_stack([np.ones(len(z)), np.ones(len(z))])
        result = rank_and_angles(cov, nuisance, blocks)
        self.assertEqual(result["models"]["optical"]["rank"], 6)
        self.assertEqual(result["models"]["joint"]["rank"], 12)
        after = optical_after_flow_nuisance(cov, nuisance, blocks)
        self.assertEqual(after["remaining_optical_rank"], 3)
        with self.assertRaisesRegex(ValueError, "optical_local single-block rank below three"):
            rank_and_angles(np.eye(len(z)), optical_local, {"optical_local": optical_local, "optical_history": blocks["optical_history"]})

    def test_restricted_proper_motion_three_depth_rank(self):
        z = np.array([0.01, 0.05, 0.1])
        _, _, chi = background(z)
        # H0 units cancel after rescaling; strict chi concavity gives rank 3.
        radial = np.column_stack((-1.0 / chi - 1.0, z / chi - 1.0, np.ones(3)))
        self.assertEqual(np.linalg.matrix_rank(radial), 3)
        self.assertGreater(abs(np.linalg.det(radial)), 1e-8)


if __name__ == "__main__":
    unittest.main()
