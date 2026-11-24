"""R108 S6 (B03 preparation, no data fit): LoS templates through the R105/R106 Commander estimator.

The R105/R106 Commander statistic (scripts/r105/commander_transfer.py, schema
r105.commander.galactic.real_l2_masked_fit.v1) is a least-squares fit, on the common
Int/Pol masks at Nside 2048, of monopole+dipole+5 real ell=2 harmonics (T) and 5 complex
spin-2 ell=2 harmonics (E+iB), with the ell=2 Commander beam x pixel window folded into
the design.  The fit is linear in the map, so for a band-limited template (ell <= 256)

    rhs_c = sum_p conj(X_c(p)) M(p) m(p) = (Npix / 4 pi) sum_lm a_lm conj(k^c_lm)

with k^c the plain pixel-sum harmonic coefficients of the masked design column M X_c
(healpy map2alm with iter=0, and map2alm_spin, which does not iterate).  ``kernel``
computes k^c for ell <= 256 and the two normal matrices once (with and without the
mask), and validates the kernel prediction against a direct Nside-2048 masked fit of a
random band-limited field.  ``project`` then takes every S1 family template (LoS alm,
384 cells, Nside 128, lmax 256), applies the Commander INT/POL beam and the Nside-2048
pixel window to all ell, and evaluates the 15 coefficients for a basis of orientations
(Wigner-D rotation of the alm, healpy ZYZ Euler angles: 48 axis directions = HEALPix
Nside 2 centres x 8 rolls), with the mask (cut sky) and without it (full-sky ell = 2
projection), so the mask leakage of each template is explicit.

Units: templates are native quarter-intensity increments at epsilon = 2e-4 converted to
micro-kelvin (T_CMB = 2.72548 K, Delta T / T = native T channel; Q, U likewise).  No
observed coefficients are read or scored here (SQ-CMB-NULL is not qualified).

Usage:
  PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=4 python -m scripts.r108.s6_b03_templates kernel
  PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m scripts.r108.s6_b03_templates project
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits

from scripts.r102.commander_pair_check import DEFAULT_MASK_INT, DEFAULT_MASK_POL, DEFAULT_OBS
from scripts.r105.commander_transfer import design, real_quadrupoles
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

WORK = Path.home() / "Downloads/htt_r108/s6"
LMAX = 256
NS = 2048
CHUNK = 1 << 20
T_CMB_UK = 2.72548e6


def _beam_and_mask():
    with fits.open(DEFAULT_OBS, memmap=True) as h:
        if h[2].header.get("METHOD") != "COMMANDER" or h[1].header["NSIDE"] != NS:
            raise ValueError("expected the PR3 Commander observation with its beam HDU")
        beam = {k: np.array(h[2].data[k], dtype=np.float64) for k in ("INT_BEAM", "POL_BEAM")}
    masks = []
    for path, col in ((DEFAULT_MASK_INT, "TMASK"), (DEFAULT_MASK_POL, "PMASK")):
        with fits.open(path, memmap=True) as h:
            t = h[1]
            if t.header["NSIDE"] != NS or t.header.get("COORDSYS") != "GALACTIC":
                raise ValueError("unexpected mask geometry")
            m = np.asarray(t.data.field(col)).ravel()
            if t.header["ORDERING"] == "NESTED":
                m = m[hp.ring2nest(NS, np.arange(hp.nside2npix(NS)))]
            masks.append((m > 0.5).astype(np.float64))
    return beam, masks


def _response(beam):
    win = np.array([p[2] for p in hp.pixwin(NS, pol=True, lmax=2)])
    return np.array([beam["INT_BEAM"][2], beam["POL_BEAM"][2]]) * win


def _columns(start: int, stop: int, response):
    """Scalar (9 real) and spin-2 (5 complex) design columns on RING pixels [start, stop); same algebra as design()."""
    x, y, z = hp.pix2vec(NS, np.arange(start, stop))
    st = np.sqrt(np.clip(1.0 - z * z, 0.0, None))
    phi = np.arctan2(y, x)
    cp, sp = np.cos(phi), np.sin(phi)
    q = real_quadrupoles(x, y, z)
    scalar = np.column_stack([np.ones_like(z), x, y, z, response[0] * q])
    spin = (-2 * response[1] / np.sqrt(24)) * real_quadrupoles(z * cp - 1j * sp, z * sp + 1j * cp, -st)
    return scalar, spin


def _full_column(kind: int, c: int, response) -> np.ndarray:
    npix = hp.nside2npix(NS)
    out = np.empty(npix, dtype=np.float64 if kind == 0 else np.complex128)
    for s in range(0, npix, CHUNK):
        e = min(s + CHUNK, npix)
        out[s:e] = _columns(s, e, response)[kind][:, c]
    return out


def kernel(args) -> None:
    t0 = time.perf_counter()
    WORK.mkdir(parents=True, exist_ok=True)
    beam, (m_t, m_p) = _beam_and_mask()
    response = _response(beam)
    npix = hp.nside2npix(NS)
    # identity of the column algebra with scripts.r105 design() on a pixel subset
    sub = np.arange(0, npix, 9973)
    ref_s, ref_p = design(*hp.pix2ang(NS, sub), response)
    col_err = 0.0
    for s in range(0, sub.size, 4096):
        idx = sub[s:s + 4096]
        for j, p in enumerate(idx):
            sc, sp = _columns(int(p), int(p) + 1, response)
            col_err = max(col_err, float(np.max(np.abs(sc[0] - ref_s[s + j]))), float(np.max(np.abs(sp[0] - ref_p[s + j]))))
    if col_err > 1e-12:
        raise ValueError(f"design columns differ from scripts.r105 design(): {col_err}")
    grams = {k: np.zeros((9, 9)) for k in ("masked_T", "fullsky_T")}
    grams.update({k: np.zeros((5, 5), complex) for k in ("masked_P", "fullsky_P")})
    for s in range(0, npix, CHUNK):
        e = min(s + CHUNK, npix)
        S, P = _columns(s, e, response)
        grams["fullsky_T"] += S.T @ S
        grams["masked_T"] += S.T @ (S * m_t[s:e, None])
        grams["fullsky_P"] += P.conj().T @ P
        grams["masked_P"] += P.conj().T @ (P * m_p[s:e, None])
    out = {"masked_kT": [], "fullsky_kT": [], "masked_kP": [], "fullsky_kP": []}
    for c in range(9):
        col = _full_column(0, c, response)
        out["masked_kT"].append(hp.map2alm(col * m_t, lmax=LMAX, iter=0))
        out["fullsky_kT"].append(hp.map2alm(col, lmax=LMAX, iter=0))
    for c in range(5):
        col = _full_column(1, c, response)
        for label, m in (("masked_kP", m_p), ("fullsky_kP", None)):
            f = col * m if m is not None else col
            out[label].append(np.stack(hp.map2alm_spin([f.real.copy(), f.imag.copy()], 2, lmax=LMAX)))
        del col
    out = {k: np.array(v) for k, v in out.items()}
    np.savez_compressed(WORK / "kernel.npz", lmax=LMAX, nside=NS, response=response,
                        beam_int=beam["INT_BEAM"][:LMAX + 1], beam_pol=beam["POL_BEAM"][:LMAX + 1], **out, **grams)
    # validation: random band-limited field, direct masked fit versus kernel prediction
    rng_seed = 108
    np.random.seed(rng_seed)
    cl = 1.0 / (np.arange(LMAX + 1) + 1.0) ** 2
    alms = hp.synalm([cl, cl, cl, 0 * cl, 0 * cl, 0 * cl], lmax=LMAX, new=True)
    tqu = hp.alm2map(alms, NS, lmax=LMAX, pol=True)
    rhs_t, rhs_p = np.zeros(9), np.zeros(5, complex)
    for s in range(0, npix, CHUNK):
        e = min(s + CHUNK, npix)
        S, P = _columns(s, e, response)
        rhs_t += S.T @ (m_t[s:e] * tqu[0][s:e])
        rhs_p += P.conj().T @ (m_p[s:e] * (tqu[1][s:e] + 1j * tqu[2][s:e]))
    del tqu
    cp = np.linalg.solve(grams["masked_P"], rhs_p)
    direct = np.stack([np.linalg.solve(grams["masked_T"], rhs_t)[4:], cp.real, cp.imag])
    pred = coefficients(alms, out["masked_kT"], out["masked_kP"], grams["masked_T"], grams["masked_P"], npix)
    err = float(np.max(np.abs(pred - direct)) / np.max(np.abs(direct)))
    write_json(WORK / "KERNEL_RECEIPT.json", {
        "schema": "htt.r108.s6_kernel.1", "lmax": LMAX, "nside": NS, "kernel_npz": str(WORK / "kernel.npz"),
        "kernel_sha256": sha256_file(WORK / "kernel.npz"), "column_identity_max_abs": col_err,
        "validation_seed": rng_seed, "validation_random_field_max_rel": err,
        "validation_direct": direct.tolist(), "validation_kernel": pred.tolist(), "response_TP": response.tolist(),
        "kept_fraction_TP": [float(m_t.mean()), float(m_p.mean())],
        "inputs": {Path(p).name: {"bytes": Path(p).stat().st_size, "sha256": sha256_file(p)}
                   for p in (DEFAULT_OBS, DEFAULT_MASK_INT, DEFAULT_MASK_POL)},
        "estimator_code_sha256": sha256_file(REPO / "scripts/r105/commander_transfer.py"),
        "seconds": time.perf_counter() - t0, "git": git_state()})
    if err > 1e-8:
        raise SystemExit(f"kernel validation failed: {err:.3e}")


def _inner_scalar(a, k):
    """sum over all m of a_lm conj(k_lm) for two real-field healpy alm arrays."""
    m = hp.Alm.getlm(hp.Alm.getlmax(a.size))[1]
    return float(np.sum(np.where(m == 0, 1.0, 2.0) * (a * np.conj(k)).real))


def _inner_spin(e, b, g, c):
    """sum over all m of (E + iB)_lm conj(G + iC)_lm for real-field E, B, G, C alm."""
    m = hp.Alm.getlm(hp.Alm.getlmax(e.size))[1]
    pos = (e + 1j * b) * np.conj(g + 1j * c)
    neg = (np.conj(e) + 1j * np.conj(b)) * (g - 1j * c)
    return complex(np.sum(np.where(m == 0, pos, pos + neg)))


def coefficients(alms, kT, kP, gT, gP, npix) -> np.ndarray:
    """R105 15 coefficients (rows T, E, B; real basis m0, sqrt2 Re/Im Y21, Y22) of a band-limited template."""
    t, e, b = alms[0], alms[1], alms[2]
    scale = npix / (4.0 * np.pi)
    rhs_t = scale * np.array([_inner_scalar(t, kT[c]) for c in range(kT.shape[0])])
    rhs_p = scale * np.array([_inner_spin(e, b, kP[c, 0], kP[c, 1]) for c in range(kP.shape[0])])
    cp = np.linalg.solve(gP, rhs_p)
    return np.stack([np.linalg.solve(gT, rhs_t)[4:], cp.real, cp.imag])


def orientations() -> np.ndarray:
    th, ph = hp.pix2ang(2, np.arange(hp.nside2npix(2)))
    return np.array([(p, t, psi) for t, p in zip(th, ph) for psi in np.arange(8) * (np.pi / 4)])


def project(args) -> None:
    t0 = time.perf_counter()
    k = dict(np.load(WORK / "kernel.npz"))
    npix = hp.nside2npix(NS)
    pw = hp.pixwin(NS, pol=True, lmax=LMAX)
    bl_t, bl_p = k["beam_int"] * pw[0], k["beam_pol"] * pw[1]
    eul = orientations()
    runs = json.loads((OUT_DIR / "SOLVER" / "S1_ATLAS.json").read_text())["runs"]
    out, rows = {}, []
    for r in runs:
        if r["n_cells"] != 384 or "ns128_st0.02" not in r["products"]:
            continue
        prod = r["products"]["ns128_st0.02"]
        if sha256_file(prod["npz"]) != prod["npz_sha256"]:
            raise ValueError(f"template {prod['npz']} changed since the atlas was summarised")
        a = np.load(prod["npz"])
        alms = [T_CMB_UK * hp.almxfl(np.asarray(a[ch], dtype=np.complex128), bl)
                for ch, bl in (("T", bl_t), ("E", bl_p), ("B", bl_p))]
        cut = np.empty((eul.shape[0], 3, 5))
        full = np.empty((eul.shape[0], 3, 5))
        for i, (phi, theta, psi) in enumerate(eul):
            rot = [x.copy() for x in alms]
            for x in rot:
                hp.rotate_alm(x, psi=psi, theta=theta, phi=phi)
            cut[i] = coefficients(rot, k["masked_kT"], k["masked_kP"], k["masked_T"], k["masked_P"], npix)
            full[i] = coefficients(rot, k["fullsky_kT"], k["fullsky_kP"], k["fullsky_T"], k["fullsky_P"], npix)
        out[r["tag"]] = np.stack([cut, full])
        leak = np.linalg.norm(cut - full, axis=2) / np.maximum(np.linalg.norm(full, axis=2), 1e-300)
        rows.append({"tag": r["tag"], "family": r["family"], "handedness": r["handedness"],
                     "template_npz": prod["npz"], "template_sha256": prod["npz_sha256"],
                     "fullsky_rms_uK_TEB": np.sqrt(np.mean(full ** 2, axis=(0, 2))).tolist(),
                     "cut_rms_uK_TEB": np.sqrt(np.mean(cut ** 2, axis=(0, 2))).tolist(),
                     "mask_leakage_rel_median_TEB": np.median(leak, axis=0).tolist(),
                     "mask_leakage_rel_max_TEB": leak.max(axis=0).tolist()})
    np.savez_compressed(WORK / "orientation_basis.npz", euler_phi_theta_psi=eul, **out)
    receipt = json.loads((WORK / "KERNEL_RECEIPT.json").read_text())
    write_json(OUT_DIR / "SOLVER" / "S6_B03_TEMPLATES.json", {
        "schema": "htt.r108.s6_b03_templates.1", "kernel": receipt,
        "orientation_basis_npz": str(WORK / "orientation_basis.npz"),
        "orientation_basis_sha256": sha256_file(WORK / "orientation_basis.npz"),
        "n_orientations": int(eul.shape[0]), "euler_convention": "healpy rotate_alm ZYZ (phi, theta, psi)",
        "units": "micro-kelvin at epsilon = 2e-4 (template linear in epsilon)", "rows": rows,
        "seconds": time.perf_counter() - t0, "git": git_state(),
        "claim": "template projection only; no observed coefficient is read or scored (SQ-CMB-NULL not qualified)"})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("kernel")
    sub.add_parser("project")
    a = ap.parse_args()
    kernel(a) if a.cmd == "kernel" else project(a)


if __name__ == "__main__":
    main()
