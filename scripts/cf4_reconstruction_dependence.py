#!/usr/bin/env python3
"""K5 reconstruction-method dependence of the CF4 bulk flow (REV-R196).

Statistical results depend on how the peculiar-velocity field is reconstructed.
This lane quantifies that dependence with data ALREADY on disk. The CF4 group
catalogue carries three peculiar-velocity estimators for the SAME 38053 groups:

  Vpds  Davis-Scrimgeour 2014, direct (least model-dependent)
  Vpwf  Watkins-Feldman 2015, pure Wiener-filter
  Vpec  ramp Eq.11 (WF blend; == the frozen cf4_groups.npz column)

Running the IDENTICAL weighted-GLS bulk-flow estimator on each isolates the
reconstruction-method effect (same objects, same weights, only the velocity
reconstruction differs). Four full-field reconstructions extend the comparison:
the CF4++ 128^3 Wiener-filter field, the external Carrick 2015 2M++ field, and
(REV-R197, substituting the private Nusser 2026) two public 2MRS reconstructions
-- the Lilow-Ganeshaiah-Veena-Nusser 2024 neural network (arXiv:2404.02278) and
CORAS (Lilow-Nusser 2021, arXiv:2102.07291). The SPREAD across methods is the
reconstruction dependence.

A Zone-of-Avoidance sensitivity sweep (|b| cuts on the DIRECT Vpds) reports how
the bulk-flow magnitude and apex shift as near-Galactic-plane objects are
removed.

Diagnostic-only kinematic descriptor: model-independent bulk-flow amplitudes +
apexes and their method spread; no Bianchi family, geometry, observer-frame, or
inference claim. Outputs docs/generated/cf4_reconstruction_dependence_card.json.
Deterministic; --check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from htt.obsstat.bulkflow_mle import (  # noqa: E402
    estimate_bulk_flow, fit_sigma_star, velocity_error)
from htt.obsstat.affine_flow import fit_affine_flow      # noqa: E402

GROUPS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
VARIANTS = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"
FIELD = REPO / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
# Carrick 2015 2M++ velocity field (external, INDEPENDENT tracer+method); off-
# Dropbox NVMe or workdir, gitignored (present -> included, absent -> skipped).
CARRICK = Path(os.environ.get(
    "CARRICK_2MPP_NPY",
    "/mnt/sn850x2t/htt_base_e2e/carrick_2mpp/twompp_velocity.npy"))
CARRICK_ALT = REPO / "workdir/raw/carrick_2mpp/twompp_velocity.npy"
# public 2MRS reconstructions (REV-R197 substitutes the private Nusser 2026):
# Lilow-Ganeshaiah-Veena-Nusser 2024 neural-network (arXiv:2404.02278) and CORAS
# (Lilow-Nusser 2021, arXiv:2102.07291). Off-Dropbox NVMe or workdir, gitignored.
LILOW_NN_DIR = Path(os.environ.get(
    "LILOW_NN_DIR", "/mnt/sn850x2t/htt_base_e2e/lilow_nn_2mrs"))
LILOW_NN_ALT = REPO / "workdir/raw/lilow_nn_2mrs"
CORAS = Path(os.environ.get(
    "CORAS_NPY", "/mnt/sn850x2t/htt_base_e2e/coras_2mrs/coras_velocity_zCMB.npy"))
CORAS_ALT = REPO / "workdir/raw/coras_2mrs/coras_velocity_zCMB.npy"
OUT = REPO / "docs/generated/cf4_reconstruction_dependence_card.json"

BOX_MPC = 1000.0
BOX_CARRICK_HMPC = 400.0
BOX_LILOW_HMPC = 400.0                              # 128^3, spacing = box/n
FIELD_RADII_MPC = (150.0, 200.0)
CARRICK_RADII_HMPC = (100.0, 150.0)
RECON_RADII_HMPC = (50.0, 100.0, 150.0)            # LVN/CORAS valid r<200
ZOA_CUTS_DEG = (0.0, 5.0, 10.0, 15.0)
PV_VARIANTS = ("Vpds", "Vpwf", "Vpec")
VARIANT_DESC = {"Vpds": "Davis-Scrimgeour 2014 direct",
                "Vpwf": "Watkins-Feldman 2015 Wiener-filter",
                "Vpec": "ramp Eq.11 (WF blend; frozen column)"}


def _sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sg_to_galactic(u_sg):
    from astropy.coordinates import SkyCoord
    c = SkyCoord(sgx=u_sg[0], sgy=u_sg[1], sgz=u_sg[2],
                 representation_type="cartesian", frame="supergalactic")
    return float(c.galactic.l.deg), float(c.galactic.b.deg)


def _ang_sep_deg(lb1, lb2):
    (l1, b1), (l2, b2) = np.radians(lb1), np.radians(lb2)
    c = np.sin(b1) * np.sin(b2) + np.cos(b1) * np.cos(b2) * np.cos(l1 - l2)
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def _apex(vec):
    l, b = _sg_to_galactic(vec / np.linalg.norm(vec))
    return [round(l, 2), round(b, 2)]


def _gls_bulk(n_hat, vpec, sigma):
    ss = fit_sigma_star(n_hat, vpec, sigma)
    bf = estimate_bulk_flow(n_hat, vpec, sigma, sigma_star=ss)
    return bf, ss


def _spread(entries):
    amps = [e["amplitude_kms"] for e in entries]
    apexes = [e["apex_galactic_l_b_deg"] for e in entries]
    max_sep = max((_ang_sep_deg(apexes[i], apexes[j])
                   for i in range(len(apexes)) for j in range(i + 1, len(apexes))),
                  default=0.0)
    return {"amplitude_min_kms": round(min(amps), 2),
            "amplitude_max_kms": round(max(amps), 2),
            "amplitude_spread_kms": round(max(amps) - min(amps), 2),
            "max_pairwise_apex_separation_deg": round(max_sep, 2)}


def _galactic_cart_to_lb(vec):
    l = float(np.degrees(np.arctan2(vec[1], vec[0]))) % 360.0
    b = float(np.degrees(np.arcsin(vec[2] / np.linalg.norm(vec))))
    return [round(l, 2), round(b, 2)]


def _carrick_bulk():
    """Carrick 2015 2M++ velocity field affine bulk flow (Galactic Cartesian,
    257^3, 400 Mpc/h box). Independent tracer (2M++) + method (linear)."""
    path = CARRICK if CARRICK.is_file() else CARRICK_ALT
    if not path.is_file():
        return None
    v = np.load(path)                                # (3,257,257,257) km/s
    n = v.shape[1]
    centers = (np.arange(n) - (n - 1) / 2.0) * (BOX_CARRICK_HMPC / (n - 1))
    gx, gy, gz = np.meshgrid(centers, centers, centers, indexing="ij")
    pos = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
    vel = np.column_stack([v[0].ravel(), v[1].ravel(), v[2].ravel()])
    out = {}
    for R in CARRICK_RADII_HMPC:
        af = fit_affine_flow(pos, vel, radius=R)
        out[str(int(R))] = {"amplitude_kms": round(af.bulk_amplitude, 2),
                            "apex_galactic_l_b_deg": _galactic_cart_to_lb(af.bulk)}
    return out


def _lilow_nn_bulk():
    """Lilow-Ganeshaiah-Veena-Nusser 2024 neural-network 2MRS reconstruction
    (128^3, 400 h^-1 Mpc, Galactic Cartesian, CMB frame; valid r<200, NaN
    outside). Public substitute for the private Nusser 2026 reconstruction."""
    d = LILOW_NN_DIR if (LILOW_NN_DIR / "xVelocity.npy").is_file() else LILOW_NN_ALT
    if not (d / "xVelocity.npy").is_file():
        return None
    vx, vy, vz = (np.load(d / f"{a}Velocity.npy") for a in "xyz")
    n = vx.shape[0]
    centers = (np.arange(n) - (n - 1) / 2.0) * (BOX_LILOW_HMPC / n)
    gx, gy, gz = np.meshgrid(centers, centers, centers, indexing="ij")
    pos = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
    vel = np.column_stack([vx.ravel(), vy.ravel(), vz.ravel()]).astype(float)
    fin = np.isfinite(vel).all(axis=1)               # drop the NaN r>200 shell
    pos, vel = pos[fin], vel[fin]
    out = {}
    for R in RECON_RADII_HMPC:
        af = fit_affine_flow(pos, vel, radius=R)
        out[str(int(R))] = {"amplitude_kms": round(af.bulk_amplitude, 2),
                            "apex_galactic_l_b_deg": _galactic_cart_to_lb(af.bulk)}
    return out


def _coras_bulk():
    """CORAS (Lilow-Nusser 2021) Wiener-filter/constrained-realization 2MRS
    reconstruction (201^3, +/-200 Mpc/h, 2 Mpc/h, comoving Galactic, zCMB).
    Second public 2MRS reconstruction (a different method from the NN)."""
    path = CORAS if CORAS.is_file() else CORAS_ALT
    if not path.is_file():
        return None
    v = np.load(path)                                # (201,201,201,3) km/s
    n = v.shape[0]
    centers = 2.0 * (np.arange(n) - (n - 1) / 2.0)   # -200..+200 Mpc/h
    gx, gy, gz = np.meshgrid(centers, centers, centers, indexing="ij")
    pos = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
    vel = v.reshape(-1, 3).astype(float)
    out = {}
    for R in RECON_RADII_HMPC:
        af = fit_affine_flow(pos, vel, radius=R)
        out[str(int(R))] = {"amplitude_kms": round(af.bulk_amplitude, 2),
                            "apex_galactic_l_b_deg": _galactic_cart_to_lb(af.bulk)}
    return out


def _field_bulk():
    if not FIELD.is_file():
        return None
    v = np.asarray(np.load(FIELD)["v_mean_CF4pp"], float)     # (3,N,N,N)
    n = v.shape[1]
    delta = BOX_MPC / n
    centers = (np.arange(n) + 0.5) * delta - BOX_MPC / 2.0
    gx, gy, gz = np.meshgrid(centers, centers, centers, indexing="ij")
    pos = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
    vel = np.column_stack([v[0].ravel(), v[1].ravel(), v[2].ravel()])
    out = {}
    for R in FIELD_RADII_MPC:
        af = fit_affine_flow(pos, vel, radius=R)
        out[str(int(R))] = {"amplitude_kms": round(af.bulk_amplitude, 2),
                            "apex_galactic_l_b_deg": _apex(af.bulk)}
    return out


def measure() -> dict:
    if not (GROUPS.is_file() and VARIANTS.is_file()):
        return {"schema": "htt.cf4_reconstruction_dependence.v1",
                "status": "BLOCKED_MISSING_CF4_CATALOGUE"}
    g = np.load(GROUPS, allow_pickle=True)
    var = np.load(VARIANTS)
    pos = np.c_[g["SGX"], g["SGY"], g["SGZ"]].astype(float)
    r = np.linalg.norm(pos, axis=1)
    v3k = np.asarray(g["V3k"], float)
    glat = np.asarray(g["GLAT"], float)
    sigma = velocity_error(g["e_DMzp"], v3k)
    base = np.isfinite(sigma) & (sigma > 0) & (r > 1.0) & np.isfinite(v3k)
    n_hat = pos / r[:, None]

    # --- reconstruction-method comparison: identical estimator, 3 PV columns ---
    method_rows = {}
    for name in PV_VARIANTS:
        vp = np.asarray(var[name], float)
        m = base & np.isfinite(vp)
        bf, ss = _gls_bulk(n_hat[m], vp[m], sigma[m])
        method_rows[name] = {
            "estimator": VARIANT_DESC[name],
            "n_groups": int(m.sum()),
            "sigma_star_kms": round(ss, 1),
            "amplitude_kms": round(bf.amplitude, 2),
            "amplitude_error_kms": round(bf.amplitude_error, 2),
            "apex_galactic_l_b_deg": _apex(bf.vector),
        }
    catalog_spread = _spread(list(method_rows.values()))

    # --- cross-method: CF4++ WF field + 3 external reconstructions (affine) ---
    field = _field_bulk()
    carrick = _carrick_bulk()
    lilow = _lilow_nn_bulk()
    coras = _coras_bulk()
    combined = list(method_rows.values())
    for ext in (field, carrick, lilow, coras):
        if ext is not None:
            combined.append(
                {"amplitude_kms": ext["150"]["amplitude_kms"],
                 "apex_galactic_l_b_deg": ext["150"]["apex_galactic_l_b_deg"]})
    cross_spread = (_spread(combined)
                    if any(x is not None for x in (field, carrick, lilow, coras))
                    else None)

    # --- ZoA sensitivity: |b| cuts on the DIRECT Vpds ---
    vpds = np.asarray(var["Vpds"], float)
    zoa_rows = {}
    base_apex = None
    for cut in ZOA_CUTS_DEG:
        m = base & np.isfinite(vpds) & (np.abs(glat) >= cut)
        bf, _ = _gls_bulk(n_hat[m], vpds[m], sigma[m])
        apex = _apex(bf.vector)
        if base_apex is None:
            base_apex = apex
        zoa_rows[str(int(cut))] = {
            "b_cut_deg": cut, "n_groups": int(m.sum()),
            "amplitude_kms": round(bf.amplitude, 2),
            "apex_galactic_l_b_deg": apex,
            "apex_shift_from_nocut_deg": round(_ang_sep_deg(apex, base_apex), 2),
        }
    zoa_amps = [zoa_rows[str(int(c))]["amplitude_kms"] for c in ZOA_CUTS_DEG]
    zoa_shifts = [zoa_rows[str(int(c))]["apex_shift_from_nocut_deg"]
                  for c in ZOA_CUTS_DEG]

    return {
        "schema": "htt.cf4_reconstruction_dependence.v1",
        "status": "MEASURED_RECONSTRUCTION_SPREAD",
        "product": "Cosmicflows-4 groups (Tully+ 2023) + CF4++ WF field + "
                   "Carrick 2M++ + LVN-2024/CORAS 2MRS reconstructions",
        "estimator": "weighted-GLS bulk flow, identical across PV variants",
        "reconstruction_method_comparison": method_rows,
        "catalog_variant_spread": catalog_spread,
        "cf4pp_wf_field_affine_bulk": field,
        "carrick2015_2mpp_affine_bulk": carrick,
        "lilow_nn_2mrs_affine_bulk": lilow,
        "coras_2mrs_affine_bulk": coras,
        "external_reconstructions": {
            "carrick_2mpp": ("CONNECTED" if carrick is not None
                             else "BLOCKED_MISSING_CARRICK_2MPP"),
            "lilow_nn_2mrs": ("CONNECTED" if lilow is not None
                              else "BLOCKED_MISSING_LILOW_NN"),
            "coras_2mrs": ("CONNECTED" if coras is not None
                           else "BLOCKED_MISSING_CORAS"),
            "nusser_2mrs": "SUPERSEDED_BY_LILOW_2024_PUBLIC",
        },
        "cross_method_spread_incl_field": cross_spread,
        "zoa_sensitivity_direct_vpds": zoa_rows,
        "zoa_summary": {
            "amplitude_spread_kms": round(max(zoa_amps) - min(zoa_amps), 2),
            "max_apex_shift_deg": round(max(zoa_shifts), 2),
            "expectation": "literature ~10-15% magnitude, 5-10 deg direction",
        },
        "input_hashes": [f"{GROUPS.relative_to(REPO)}:{_sha(GROUPS)}",
                         f"{VARIANTS.relative_to(REPO)}:{_sha(VARIANTS)}"],
        "caveats": [
            "the 3 catalog variants isolate the reconstruction-method effect "
            "(identical estimator + objects; only the velocity column differs); "
            "Vpds is the DIRECT estimator (noisiest), Vpwf/Vpec are Wiener-"
            "filter-based (Vpec is the frozen column)",
            "four full field reconstructions extend the comparison: the CF4++ WF "
            "field (CF4 tracers), the EXTERNAL Carrick 2015 2M++ field (an "
            "INDEPENDENT tracer + linear method), and TWO public 2MRS "
            "reconstructions -- the Lilow-Ganeshaiah-Veena-Nusser 2024 neural "
            "network (arXiv:2404.02278) and CORAS (Lilow-Nusser 2021, "
            "arXiv:2102.07291, a WF/constrained-realization method) -- which "
            "REPLACE the private Nusser 2026 reconstruction (no public release); "
            "each is an affine bulk flow at its own depth/window convention "
            "(grids in Mpc or Mpc/h) -- cross-method sanity comparisons, not "
            "scale-matched measurements",
            "the 2MRS reconstructions are RECONSTRUCTION-vs-MEASUREMENT, not "
            "like-for-like: 2MRS is shallow, so the neural-network flow regresses "
            "to the mean at large r (published LVN |B|~220@50 -> ~90@200 km/s, "
            "apex l~254); the CF4 MEASURED flow being larger at large r is the "
            "expected reconstruction/measurement gap, NOT a tension",
            "the ZoA sweep removes near-plane objects (|b| cut); it measures the "
            "directional/magnitude sensitivity, it does not fill the gap",
        ],
        "claim": ("real measurement: CF4 bulk-flow amplitude spread across three "
                  "reconstruction variants (Vpds/Vpwf/Vpec) = %.0f km/s, max "
                  "apex spread %.0f deg; ZoA |b|-cut sensitivity %.0f km/s / "
                  "%.0f deg" % (catalog_spread["amplitude_spread_kms"],
                                catalog_spread["max_pairwise_apex_separation_deg"],
                                round(max(zoa_amps) - min(zoa_amps), 2),
                                max(zoa_shifts))),
        "scope_not_claimed": ("model-independent bulk-flow amplitudes/apexes and "
                              "their reconstruction-method + ZoA spread; NOT a "
                              "Bianchi family, geometry, or observer-frame claim; "
                              "no anisotropy discovery"),
    }


def _render(p):
    return json.dumps(p, indent=2, sort_keys=True, default=str) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    card = measure()
    rendered = _render(card)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE cf4_reconstruction_dependence_card.json", file=sys.stderr)
            return 1
        print("cf4 reconstruction dependence card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']}")
    if card["status"].startswith("MEASURED"):
        for n, d in card["reconstruction_method_comparison"].items():
            print(f"  {n}: |B|={d['amplitude_kms']:.0f}+/-{d['amplitude_error_kms']:.0f} "
                  f"apex={d['apex_galactic_l_b_deg']}")
        print(f"  catalog spread: {card['catalog_variant_spread']}")
        if card["cf4pp_wf_field_affine_bulk"]:
            print(f"  CF4pp field @150Mpc: {card['cf4pp_wf_field_affine_bulk']['150']}")
        for k, lbl in (("carrick2015_2mpp_affine_bulk", "Carrick 2M++"),
                       ("lilow_nn_2mrs_affine_bulk", "Lilow-NN 2MRS"),
                       ("coras_2mrs_affine_bulk", "CORAS 2MRS")):
            if card.get(k):
                print(f"  {lbl} @150: {card[k]['150']}")
        print(f"  external: {card['external_reconstructions']}")
        print(f"  cross-method spread: {card['cross_method_spread_incl_field']}")
        print(f"  ZoA: {card['zoa_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
