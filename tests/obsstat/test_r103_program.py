import hashlib
import itertools
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from scripts.r103 import program
from scripts.r103.p1_joint_patterns import pattern_bounds
from scripts.r103.radio_selection import analyze, extra_covariance_budget


class TestR103Program(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = program.build()
        cls.nodes = {r['id']: r for r in cls.report['nodes']}
        cls.phy = cls.report['cross_route_results']

    def test_graph_states_and_overlay_edges(self):
        self.assertEqual(len(self.nodes), 60)
        self.assertEqual(len(self.report['edges']), 129)
        self.assertEqual(len(self.report['seven_research_axes']), 7)
        self.assertEqual(len(self.report['seven_cross_routes']), 7)
        self.assertEqual(self.report['papers'], list('P' + str(i) for i in range(1, 7)))
        self.assertIn('SQ-CF4', self.nodes['H02']['hard_dependencies'])
        self.assertEqual(self.nodes['SQ-CF4']['canonical_state'], 'ready_scoped')
        self.assertEqual(self.report['source_qualification']['source_qualification'], 'BLOCKED_INPUT')
        for row in self.nodes.values():
            self.assertTrue(row['canonical_acceptance'] and row['local_action'])
            self.assertFalse(row['new_scientific_acceptance'])

    def test_missing_or_regenerated_bytes_are_distinguished(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = root / program.CURRENT / 'example.json'
            result.parent.mkdir(parents=True)
            raw = b'{"error":0.0}\n'
            proofs = {result.name: (hashlib.sha256(raw).hexdigest(), 'numerical', ['B02'], 'fixture')}
            get_state = lambda: program.review_results(root, proofs)[result.name]['state']
            self.assertEqual(get_state(), 'missing')
            result.write_bytes(raw)
            self.assertEqual(get_state(), 'reviewed')
            result.write_bytes(b'{}')
            self.assertEqual(get_state(), 'different_bytes')
            with self.assertRaises(ValueError):
                program.verified_json(root, result.relative_to(root), proofs[result.name][0])

    def test_geometric_optima_from_original_spectra(self):
        dag = json.loads((program.ROOT / program.DAG).read_bytes())
        src = {n['id']: n['observable_evidence'] for n in dag['nodes'] if 'observable_evidence' in n}
        r1 = self.phy['PHY-01']
        self.assertAlmostEqual(r1['fixed_zero_flux_shape_optimal_leakage'],
                               src['PHY-01']['explicit_mask_mean_direct_check'], places=14)
        self.assertLessEqual(r1['shape_efficiency'], 1.)
        for name, press in src['PHY-02']['R66_same_sky_finiteband_photon_pressure'].items():
            # The isotropic component only shifts eigenvalues. Use these actual
            # pressure eigenvalues to independently project onto the boost cone.
            ev = np.array(press['P_eigenvalues'])
            vals = np.sort(ev - ev.mean())
            vals /= np.linalg.norm(vals)
            direction = np.array([-1., -1., 2.]) / np.sqrt(6.)
            amp = max(direction @ vals, 0.)
            residual = np.linalg.norm(vals - amp*direction)
            self.assertAlmostEqual(residual, self.phy['PHY-03'][name]['best_amplitude_axis_relative_residual'],
                                   delta=4e-11)
            radius = self.phy['PHY-02'][name]['max_normalized_photon_flux']
            self.assertAlmostEqual(min(np.linalg.eigvalsh(np.diag(ev) -
                                   np.diag([0., 0., radius**2]))), 0., places=14)

    def test_closure_null_and_radial_bounds(self):
        self.assertLess(self.phy['PHY-05']['shear_jacobian_left_null_residual'], 1e-13)
        self.assertGreater(self.phy['PHY-06']['minimax_cap_absolute_error_lower_bound'], 0.028)
        for shell, row in self.phy['PHY-07'].items():
            # A two-radius distribution with weights a/(a+b), b/(a+b)
            # (a,b the reciprocal-distance endpoints) attains the cosine bound.
            lo, hi = map(float, shell.split('-'))
            u = 1 / np.array([lo, hi])
            weight = np.array([lo, hi]) / (lo+hi)
            x = np.sqrt(weight)
            y = x * u
            mat = np.column_stack([x/np.linalg.norm(x), y/np.linalg.norm(y)])
            self.assertAlmostEqual(np.linalg.cond(mat), row['normalized_design_condition_lower_bound'], places=12)
            self.assertGreaterEqual(row['source_measured_condition'], np.linalg.cond(mat) - 1e-10)

    def test_radio_covariance_budget_attainability_and_minimality(self):
        c = np.array([[2., 0.6], [0.6, 0.5]])
        d = np.array([1., 2.])
        exact = extra_covariance_budget(d, c, 2.)
        self.assertAlmostEqual(exact['achieved_wald'], 2.)
        e = exact['extra_spectral_variance']
        for angle in np.linspace(0., np.pi, 67):
            v = np.array([np.cos(angle), np.sin(angle)])
            smaller = c + 0.999*e*np.outer(v, v)
            self.assertGreater(d @ np.linalg.solve(smaller, d), 2.)
        self.assertEqual(extra_covariance_budget(d*0, c, 2.)['extra_sd'], 0.)
        with self.assertRaises(ValueError):
            extra_covariance_budget(d, np.diag([1., -0.1]), 2.)
        observed = analyze(program.ROOT)['fits']['dipole_stf']
        self.assertEqual(observed['shared_objects'], 241892)
        self.assertAlmostEqual(observed['working_contours']['0.95']['wald_working'], 30.989468960483375)

    def test_p1_multiplicity_bounds_against_complete_enumeration(self):
        # Enumerate all triples of bit patterns, independently of integer programming.
        possibilities = {}
        for triple in itertools.combinations_with_replacement(range(16), 3):
            counts = [x.bit_count() for x in triple]
            margins = tuple(sum((x >> bit) & 1 for x in triple) for bit in range(4))
            key = (margins, sum(k > 0 for k in counts), counts.count(4))
            possibilities.setdefault(key, set()).add(tuple(sum(j >= k for j in counts) for k in (2, 3)))
        key = max(possibilities, key=lambda s: len(possibilities[s]))
        got = pattern_bounds(*key, 3)
        for k in (2, 3):
            outcomes = [pair[k-2] for pair in possibilities[key]]
            self.assertEqual(got[str(k)]['counts_min_max'], [min(outcomes), max(outcomes)])
        # At 0.05 for the original P1 source, the first margin vanishes:
        # n2+2*n3=sum(margins)-union=137, 0<=n3<=11. Each extreme is attained.
        actual = pattern_bounds([0, 136, 1225, 11], 1235, 0, 2048)
        self.assertEqual(actual['2']['counts_min_max'], [126, 137])
        self.assertEqual(actual['3']['counts_min_max'], [0, 11])
        with self.assertRaises(ValueError):
            pattern_bounds([0, 0, 0, 0], 3, 0, 4)
