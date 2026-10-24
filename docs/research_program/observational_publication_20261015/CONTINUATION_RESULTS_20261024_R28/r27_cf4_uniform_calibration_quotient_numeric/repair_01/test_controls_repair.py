#!/usr/bin/env python3
"""One deterministic compact control batch for the support quotient."""
from __future__ import annotations

import unittest

import numpy as np

import consume as qmod


def fixture():
    # Singleton groups of three and four, and one mixed row kept in the carrier.
    support = np.zeros((8, 7), bool)
    support[:3, 0] = True
    support[3:7, 6] = True
    support[7, [0, 6]] = True
    active = support.sum(axis=1) == 1
    c = np.zeros((8, 7))
    c[active] = support[active]
    n = np.ones((8, 1))  # Deliberate dependency: n = c_0 + c_6 on J.
    b = np.zeros((8, 5))
    for col, (i, j) in enumerate(((0, 1), (1, 2), (3, 4), (4, 5), (5, 6))):
        b[i, col], b[j, col] = 1, -1
    b[7] = (2, 3, 5, 7, 11)
    d = np.ones(8)
    uj = np.column_stack((n[active], c[active]))
    basis, nuisance = qmod.projector(7, uj, ["dependent_ones"] + [f"channel_{j}" for j in range(7)])
    return support, active, c, n, b, d, basis, nuisance


def operator_for(b, y, active, basis, d):
    rj, tj, v, null, p, bmin, cw, info = qmod.response_fit(b / np.sqrt(d)[:, None], y / np.sqrt(d), active, basis)
    k = np.zeros((5, len(active)))
    rank = info["rank"]
    if rank:
        s = np.asarray(info["signal_singular_values"])
        left = (rj @ v) / s[:rank]
        k[:, active] = (v / s[:rank]) @ (left.T / np.sqrt(d[active])[None, :])
    return k, v, null, p, bmin, cw, info


class QuotientControls(unittest.TestCase):
    def test_exact_support_decomposition(self):
        self.assertEqual(qmod.exact_decomposition_control()["status"], "EXACT_COEFFICIENTWISE_IDENTITY")

    def test_full_rank_uniform_invariance_and_cross_covariance(self):
        support, active, c, n, b, d, basis, nuisance = fixture()
        self.assertEqual(nuisance["rank"], 2)
        true_b = np.array([.21, -.31, .13, .07, -.19])
        a = c.copy()
        a[7, [0, 6]] = [.37, .63]
        eta = np.array([.4, 0, 0, 0, 0, 0, -.8])
        y = b @ true_b + a @ eta
        y[7] += 13.0  # Mixed-row perturbation has exactly zero leverage.
        k, v, null, p, bmin, cw, info = operator_for(b, y, active, basis, d)
        self.assertEqual(info["rank"], 5)
        self.assertLess(np.max(abs(bmin - true_b)), 1e-12)
        self.assertTrue(np.array_equal(k[:, 7], np.zeros(5)))
        self.assertLess(np.linalg.norm(k @ n), 1e-12)
        self.assertLess(np.linalg.norm(k @ c), 1e-12)
        self.assertLess(np.linalg.norm(k @ b - p), 1e-12)
        for w in (.01, .37, .93):
            a[7, [0, 6]] = [w, 1 - w]
            self.assertLess(np.linalg.norm(k @ a), 1e-12)
            self.assertLess(np.linalg.norm(k @ (a @ eta)), 1e-12)
        # A PSD joint covariance with nonzero epsilon/eta cross block.
        h_e = np.arange(1, 17, dtype=float).reshape(8, 2) / 37
        h_eta = np.array([[.7, -.2], [.2, .4], [.3, .5], [-.1, .2],
                          [.1, .3], [.2, -.3], [.8, .1]])
        gamma = h_eta @ h_eta.T
        cross = h_e @ h_eta.T
        self.assertGreater(np.linalg.norm(cross), 0)
        ka = k @ a
        raw = (np.linalg.norm(ka @ gamma @ ka.T),
               np.linalg.norm(k @ cross @ ka.T),
               np.linalg.norm(ka @ cross.T @ k.T))
        s_cal = np.linalg.norm(k) ** 2 * np.linalg.norm(a) ** 2 * np.linalg.norm(gamma)
        s_cross = np.linalg.norm(k) ** 2 * np.linalg.norm(cross) * np.linalg.norm(a)
        scales = (s_cal, s_cross, s_cross)
        for value, scale in zip(raw, scales):
            self.assertTrue(np.isfinite(value))
            self.assertTrue(np.isfinite(scale))
            self.assertGreater(scale, 0)
        ratios = tuple(value / max(scale, np.finfo(float).tiny)
                       for value, scale in zip(raw, scales))
        print({"raw_frobenius": tuple(format(x, ".17g") for x in raw),
               "denominator_frobenius_product": tuple(format(x, ".17g") for x in scales),
               "normalized": tuple(format(x, ".17g") for x in ratios),
               "K_hat_A_frobenius": format(np.linalg.norm(ka), ".17g"),
               "K_hat_A_normalized": format(
                   np.linalg.norm(ka) / max(np.linalg.norm(k) * np.linalg.norm(a),
                                            np.finfo(float).tiny), ".17g")}, flush=True)
        for ratio in ratios:
            self.assertTrue(np.isfinite(ratio))
            self.assertLessEqual(ratio, 1e-10)
        # Direct-channel shift is absorbed; simultaneous row/channel relabeling is equivariant.
        self.assertLess(np.linalg.norm(k @ (y + 2.3 * a[:, 6]) - true_b), 1e-12)
        row = np.array([6, 2, 7, 0, 4, 1, 5, 3])
        channels = np.array([6, 1, 2, 3, 4, 5, 0])
        support_p = support[row][:, channels]
        active_p = support_p.sum(axis=1) == 1
        c_p = np.zeros((8, 7))
        c_p[active_p] = support_p[active_p]
        basis_p, _ = qmod.projector(7, np.column_stack((n[row][active_p], c_p[active_p])),
                                    ["ones"] + [f"p{j}" for j in range(7)])
        kp, *_ = operator_for(b[row], y[row], active_p, basis_p, d[row])
        self.assertLess(np.linalg.norm(kp @ y[row] - true_b), 1e-12)

    def test_rank4_rank0_and_unstable(self):
        support, active, c, n, b, d, basis, _ = fixture()
        beta = np.array([.2, -.3, .1, .07, -.2])
        b4 = b.copy()
        b4[:, 4] = c[:, 0]
        k4, v4, null4, p4, bmin4, cw4, info4 = operator_for(b4, b4 @ beta, active, basis, d)
        self.assertEqual(info4["rank"], 4)
        self.assertEqual(null4.shape, (5, 1))
        self.assertLess(np.linalg.norm(k4 @ b4 - p4), 1e-12)
        self.assertLess(abs(null4[:, 0] @ bmin4), 1e-12)
        self.assertEqual(cw4.shape, (5, 5))
        b0 = np.tile(c[:, [0]], (1, 5))
        k0, v0, null0, p0, bmin0, cw0, info0 = operator_for(b0, b0 @ beta, active, basis, d)
        self.assertEqual(info0["rank"], 0)
        self.assertIsNone(bmin0)
        self.assertIsNone(cw0)
        self.assertEqual(null0.shape, (5, 5))
        self.assertTrue(np.array_equal(k0, np.zeros_like(k0)))
        weak = b.copy()
        weak[:, 4] *= 1e-9
        with self.assertRaisesRegex(qmod.Hold, "NUMERICAL_RANK_UNCERTAIN"):
            operator_for(weak, weak @ beta, active, basis, d)

    def test_stf_decode_rotation(self):
        # Exact same five-coordinate basis as the sealed source definition.
        s2 = np.sqrt(2.)
        s6 = np.sqrt(6.)
        tensors = np.zeros((5, 3, 3))
        tensors[0] = np.diag([1., -1., 0.]) / s2
        tensors[1] = np.diag([1., 1., -2.]) / s6
        for a, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 2):
            tensors[a, i, j] = tensors[a, j, i] = 1 / s2
        beta = np.array([.2, -.1, .3, .07, -.05])
        tensor = np.einsum("a,aij->ij", beta, tensors)
        self.assertLess(abs(np.trace(tensor)), 1e-15)
        self.assertLess(np.linalg.norm(tensor - tensor.T), 1e-15)
        self.assertLess(np.max(abs(np.einsum("aij,ij->a", tensors, tensor) - beta)), 1e-15)
        theta = .37
        rotation = np.array([[np.cos(theta), -np.sin(theta), 0],
                             [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
        rotated = rotation @ tensor @ rotation.T
        coeff = np.einsum("aij,ij->a", tensors, rotated)
        self.assertLess(np.linalg.norm(np.einsum("a,aij->ij", coeff, tensors) - rotated), 1e-15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
