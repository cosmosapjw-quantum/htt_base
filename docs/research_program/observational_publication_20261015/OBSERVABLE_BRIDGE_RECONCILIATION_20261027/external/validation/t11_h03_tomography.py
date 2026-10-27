"""T-11: per-window apparent shear amplitude, noise floor, eigenframe and dipole alignment from the saved
H03 tomography (htt_base a55036ad, evidence/sources/H03_SOURCE_TOMOGRAPHY.json).

Usage: python3 -I t11_h03_tomography.py <path-to-H03_SOURCE_TOMOGRAPHY.json>

Callers: none (standalone archival of the V-1 step-8 check recorded in state/VALIDATION.md T-11).
Output: JSON on stdout with per-window rows; no files written. The producer stores the STF2 matrix directly
(`STF2_matrix_km_s_Mpc`) when present; otherwise the 5-vector is expanded in the orthonormal basis
T0 = diag(1,-1,0)/sqrt2, T1 = diag(1,1,-2)/sqrt6, Txy, Txz, Tyz (symmetric pairs / sqrt2). Frobenius norms are
basis independent; eigen-axes are reported for the largest POSITIVE eigenvalue (fix of the window-4 row noted by
the decision gate: the earlier table quoted the negative-eigenvalue axis for z_c = 0.08).
Linear-LCDM comparison numbers are the T-05b toy values (own inference), not literature.
"""
import json
import sys

import numpy as np

LIN_T05B = {0.025: 0.0297, 0.04: 0.0170, 0.06: 0.0110, 0.08: 0.0079}


def icrs_to_gal(v):
    ra_gp, dec_gp, l_ncp = np.radians(192.85948), np.radians(27.12825), np.radians(122.93192)
    ra = np.arctan2(v[1], v[0])
    dec = np.arcsin(v[2])
    sinb = np.sin(dec_gp) * np.sin(dec) + np.cos(dec_gp) * np.cos(dec) * np.cos(ra - ra_gp)
    b = np.arcsin(sinb)
    y = np.cos(dec) * np.sin(ra - ra_gp)
    x = np.cos(dec_gp) * np.sin(dec) - np.sin(dec_gp) * np.cos(dec) * np.cos(ra - ra_gp)
    l = (l_ncp - np.arctan2(y, x)) % (2 * np.pi)
    return float(np.degrees(l)), float(np.degrees(b))


def stf_matrix(window):
    if 'STF2_matrix_km_s_Mpc' in window:
        return np.array(window['STF2_matrix_km_s_Mpc'], dtype=float)
    s2, s6 = np.sqrt(2.0), np.sqrt(6.0)
    basis = [np.diag([1, -1, 0]) / s2, np.diag([1, 1, -2]) / s6,
             np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]]) / s2,
             np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]]) / s2,
             np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]]) / s2]
    q = np.array(window['theta9'][4:9], dtype=float)
    return sum(c * b for c, b in zip(q, basis))


def main(path):
    d = json.load(open(path))
    C = np.array(d['joint_covariance_36x36'], dtype=float)
    rows = []
    for i, w in enumerate(d['monopole_dipole_STF2_windows']):
        th = np.array(w['theta9'], dtype=float)
        H, D, q = th[0], th[1:4], th[4:9]
        Q = stf_matrix(w)
        blk_q = C[9 * i + 4: 9 * i + 9, 9 * i + 4: 9 * i + 9]
        blk_d = C[9 * i + 1: 9 * i + 4, 9 * i + 1: 9 * i + 4]
        norm_q = np.linalg.norm(Q)
        noise_floor = np.sqrt(np.trace(blk_q)) / H
        debiased = np.sqrt(max(norm_q**2 - np.trace(blk_q), 0.0)) / H
        ev, evec = np.linalg.eigh(Q / H)
        kpos = int(np.argmax(ev))
        axis_pos = evec[:, kpos]
        Dhat = D / np.linalg.norm(D)
        rows.append({
            'z_center': w['z_center'],
            'H_w': float(H),
            'dipole_over_H': float(np.linalg.norm(D) / H),
            'dipole_err_over_H': float(np.sqrt(np.trace(blk_d)) / H),
            'dipole_dir_gal_lb': icrs_to_gal(Dhat),
            'normQ_over_H_raw': float(norm_q / H),
            'normQ_over_H_debiased': float(debiased),
            'noise_floor_over_H': float(noise_floor),
            'linear_LCDM_rms_T05b': LIN_T05B.get(w['z_center']),
            'eigenvalues_Q_over_H': [float(x) for x in ev],
            'axis_largest_positive_eigenvalue_gal_lb': icrs_to_gal(axis_pos),
            'angle_D_to_positive_axis_deg': float(np.degrees(np.arccos(abs(Dhat @ axis_pos)))),
            'nQn_along_D_over_normQ': float(Dhat @ Q @ Dhat / norm_q),
            'stf_chi2_vs_zero_5dof': float(q @ np.linalg.solve(blk_q, q)),
            'norm5_vs_normF_consistency': float(abs(np.linalg.norm(q) - norm_q)),
        })
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
