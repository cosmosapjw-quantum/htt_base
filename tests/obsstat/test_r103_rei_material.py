import csv
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from bass.recombination.rei_material_history import HELIUM_RATIO, SOURCES, ReiMaterialHistory
from bass.recombination.tilted_hyrec import TiltedHyrecHistory


class ReiMaterialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "abundances.csv.gz"
        self.z = np.array([20., 15., 12., 8., 6., 4.])

    def source(self, corrupt_he=False):
        labels = "a zbar time_s x_HI x_HII x_HeI x_HeII x_HeIII xe_per_H temperature_K nH_proper_cm3 ne_proper_cm3".split()
        with gzip.open(self.path, "wt") as out:
            csvout = csv.writer(out)
            csvout.writerow(labels)
            for j, z in enumerate(self.z):
                a = 1/(1+z)
                xe = .6 + HELIUM_RATIO * (.25 + 2 * .05)
                nh = 1e-7 / a**3
                csvout.writerow((a, z, 1e10*j, .4, .6, .7, .25, .5 if corrupt_he else .05, xe, 500., nh, nh*xe))
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch.dict(SOURCES, {digest: (6, "synthetic_test")}):
            return ReiMaterialHistory(self.path)

    def test_identity_and_helium_checks(self):
        self.source()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            ReiMaterialHistory(self.path)
        with self.assertRaisesRegex(ValueError, "nonconserving"):
            self.source(corrupt_he=True)

    def test_native_history_on_arbitrary_ordered_queries(self):
        source = self.source()
        run = TiltedHyrecHistory.from_rei_history(source, [6., 20., 4.])
        self.assertEqual(run.kappa[2], 0.)
        self.assertGreater(run.kappa[1], run.kappa[0])
        np.testing.assert_allclose(run.x_e, .6 + HELIUM_RATIO * .35)
        native = source.cells(source.N)
        np.testing.assert_allclose(run.kappa[1], native.delta_tau.sum(), atol=1e-13)
        self.assertIs(run.opacity_history(), source)
        with self.assertRaisesRegex(ValueError, "non-tilted"):
            run.opacity_history(beta=[.01, 0, 0], direction=[1, 0, 0])

    def test_partial_window_no_extrapolation_and_exact_cell_mass(self):
        source = self.source()
        run = source.evaluate([15, 12])
        self.assertEqual(run.kappa[1], 0.)
        cells = source.cells(run.N_grid)
        self.assertAlmostEqual(cells.visibility_mass.sum(), -np.expm1(-run.kappa[0]), places=13)
        for z in ([0, 12], [5, 21], [6, 6], [5, np.nan]):
            with self.assertRaises(ValueError):
                source.evaluate(z)


if __name__ == "__main__":
    unittest.main()
