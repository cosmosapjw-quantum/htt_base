"""L6 theory slice: Thomas-Wigner rotation for ordered composition of two boosts (exact), compared to the leading-order formula.
Angle of the Wigner rotation for boosts b1 then b2 (units c=1): computed exactly from the 4x4 Lorentz-matrix product (polar decomposition rotation part)
and compared with 0.5*|b1 x b2| (small-beta leading order). No data used. Usage: python3 L6_wigner_rotation_bound.py --out out.json
"""
import argparse, json, numpy as np
def boost(b):
    b = np.asarray(b, float); g2 = 1 / (1 - b @ b); g = np.sqrt(g2); L = np.eye(4)
    L[0, 0] = g; L[0, 1:] = L[1:, 0] = -g * b
    bb = np.outer(b, b) / max(b @ b, 1e-300); L[1:, 1:] = np.eye(3) + (g - 1) * bb
    return L
def wigner_angle(b1, b2):
    L = boost(b2) @ boost(b1); v = -L[1:, 0] / L[0, 0]; B = boost(v)       # pure boost with the composite velocity
    R = np.linalg.inv(B) @ L; Rr = R[1:, 1:]; ax = 0.5 * np.array([Rr[2, 1] - Rr[1, 2], Rr[0, 2] - Rr[2, 0], Rr[1, 0] - Rr[0, 1]])
    return float(np.arcsin(np.clip(np.linalg.norm(ax), 0, 1)))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args(); rng = np.random.default_rng(20261112); rows = []
    for b in (1.2e-3, 3e-3, 1e-2, 0.1):
        for phi in (np.pi / 6, np.pi / 2, 2 * np.pi / 3):
            b1 = np.array([b, 0, 0]); b2 = np.array([b * np.cos(phi), b * np.sin(phi), 0])
            ex = wigner_angle(b1, b2); lo = 0.5 * np.linalg.norm(np.cross(b1, b2)); rows.append({"beta": b, "angle_between_rad": float(phi), "exact_rad": ex, "leading_order_rad": float(lo), "rel_diff": float(ex / lo - 1)})
    res = {"scope": "exact Thomas-Wigner rotation vs leading order; theory only", "rows": rows,
           "max_angle_rad_beta_1.2e-3_pair": max(r["exact_rad"] for r in rows if r["beta"] == 1.2e-3), "method_note": "rotation angle from the antisymmetric part of R = B(v)^-1 L; composite velocity v = -L[1:,0]/L[0,0]"}
    json.dump(res, open(a.out, "w"), indent=1); [print(r) for r in rows]
if __name__ == "__main__": main()
