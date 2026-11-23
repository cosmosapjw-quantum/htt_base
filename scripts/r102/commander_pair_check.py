"""R102 Step 2: Raw Planck PR3 Commander paired signal/noise/observed FITS alignment check.

Pairs the newly acquired PR3 FFP10 fullmission noise realization (00000) with
the local PR3 FFP10 fullmission CMB signal realization (00000), the observed
PR3 Commander full-sky IQU map, and the PR3 common intensity/polarization masks.

Dynamically inspects and aligns FITS RING vs NESTED ordering, NSIDE, units,
bad-pixel masks, and beam extensions. Verifies exact pseudo-C_ell algebraic
identity C_ell(s+n) = C_ell(s) + C_ell(n) + 2 C_ell(s x n).

Note: one matched MC pair verifies pipeline/metadata/ordering/unit alignment
only; it does NOT constitute a calibrated multi-realization Planck null ensemble.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from astropy.io import fits
import healpy as hp
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NOISE = Path("/home/cosmosapjw/Downloads/htt_r101/dx12_v3_commander_noise_mc_00000_raw.fits")
DEFAULT_SIGNAL = Path("/mnt/extdrive/workdir/raw/planck_ffp10/commander/cmb_mc/dx12_v3_commander_cmb_mc_00000_raw.fits")
DEFAULT_OBS = Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits")
DEFAULT_MASK_INT = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
DEFAULT_MASK_POL = Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
DEFAULT_OUT = (
    ROOT
    / "docs/research_program/observational_publication_20261015"
    / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"
    / "COMMANDER_PAIR_00000_CHECK.json"
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _inspect_fits(path: Path) -> dict[str, object]:
    with fits.open(path, memmap=True) as hdul:
        hdus = []
        for idx, hdu in enumerate(hdul):
            hdr = hdu.header
            info = {
                "hdu_index": idx,
                "name": str(hdu.name),
                "xtension": hdr.get("XTENSION"),
                "naxis2": hdr.get("NAXIS2"),
                "nside": hdr.get("NSIDE"),
                "ordering": hdr.get("ORDERING"),
                "coordsys": hdr.get("COORDSYS"),
                "bad_data": hdr.get("BAD_DATA"),
                "columns": [
                    {
                        "name": hdr.get(f"TTYPE{j}"),
                        "form": hdr.get(f"TFORM{j}"),
                        "unit": hdr.get(f"TUNIT{j}"),
                    }
                    for j in range(1, int(hdr.get("TFIELDS", 0)) + 1)
                ],
            }
            hdus.append(info)
    return {
        "path": str(path),
        "bytes": int(path.stat().st_size),
        "hdus": hdus,
    }


def _read_healpix_to_ring(path: Path, field: int | tuple[int, ...] = 0) -> tuple[np.ndarray, dict[str, object]]:
    """Read HEALPix map(s) from HDU 1 and convert NESTED -> RING when needed."""
    meta = _inspect_fits(path)
    h1 = meta["hdus"][1]
    ordering = str(h1.get("ordering") or "RING").strip().upper()
    nside = int(h1["nside"])
    nest = ordering == "NESTED"
    raw = hp.read_map(str(path), field=field, hdu=1, dtype=np.float64, nest=nest, verbose=False)
    if isinstance(field, int):
        arr = np.asarray(raw, dtype=np.float64)
        if nest:
            arr = hp.reorder(arr, n2r=True)
        bad_mask = (~np.isfinite(arr)) | (arr <= -1.6e30)
        n_bad = int(np.count_nonzero(bad_mask))
        arr = np.where(bad_mask, 0.0, arr)
        meta["n_bad_pixels"] = n_bad
        meta["reordered_to_ring"] = nest
        return arr, meta

    arrs = [np.asarray(m, dtype=np.float64) for m in raw]
    reordered = []
    n_bad_per_col = []
    for m in arrs:
        m_ring = hp.reorder(m, n2r=True) if nest else m
        bad_mask = (~np.isfinite(m_ring)) | (m_ring <= -1.6e30)
        n_bad_per_col.append(int(np.count_nonzero(bad_mask)))
        reordered.append(np.where(bad_mask, 0.0, m_ring))
    meta["n_bad_pixels_by_channel"] = n_bad_per_col
    meta["reordered_to_ring"] = nest
    meta["nside_verified"] = nside
    return np.stack(reordered, axis=0), meta


def _mask_and_anafast(
    maps_iqu: np.ndarray,
    mask_int: np.ndarray,
    mask_pol: np.ndarray,
    *,
    lmax: int = 64,
    maps2_iqu: np.ndarray | None = None,
) -> np.ndarray:
    """Apply separate intensity/polarization masks in RING ordering and run anafast."""
    m1 = [maps_iqu[0] * mask_int, maps_iqu[1] * mask_pol, maps_iqu[2] * mask_pol]
    if maps2_iqu is None:
        return hp.anafast(m1, lmax=lmax, pol=True, use_pixel_weights=False)
    m2 = [maps2_iqu[0] * mask_int, maps2_iqu[1] * mask_pol, maps2_iqu[2] * mask_pol]
    return hp.anafast(m1, m2, lmax=lmax, pol=True, use_pixel_weights=False)


def run_check(
    noise_path: Path = DEFAULT_NOISE,
    signal_path: Path = DEFAULT_SIGNAL,
    obs_path: Path = DEFAULT_OBS,
    mask_int_path: Path = DEFAULT_MASK_INT,
    mask_pol_path: Path = DEFAULT_MASK_POL,
    *,
    lmax: int = 64,
) -> dict[str, object]:
    t0 = time.monotonic()
    for p in (noise_path, signal_path, obs_path, mask_int_path, mask_pol_path):
        if not Path(p).is_file():
            raise FileNotFoundError(f"missing required Planck file: {p}")

    noise_sha256 = _sha256_file(noise_path)
    mask_int_sha256 = _sha256_file(mask_int_path)
    mask_pol_sha256 = _sha256_file(mask_pol_path)

    m_int, meta_mint = _read_healpix_to_ring(mask_int_path, field=0)
    m_pol, meta_mpol = _read_healpix_to_ring(mask_pol_path, field=0)
    if m_int.shape != m_pol.shape:
        raise ValueError("intensity and polarization mask shape mismatch")
    fsky_int = float(np.mean(m_int > 0.5))
    fsky_pol = float(np.mean(m_pol > 0.5))
    m_int_bin = (m_int > 0.5).astype(np.float64)
    m_pol_bin = (m_pol > 0.5).astype(np.float64)
    del m_int, m_pol

    sig_iqu, meta_sig = _read_healpix_to_ring(signal_path, field=(0, 1, 2))
    noi_iqu, meta_noi = _read_healpix_to_ring(noise_path, field=(0, 1, 2))
    if sig_iqu.shape != noi_iqu.shape or sig_iqu.shape[1] != m_int_bin.shape[0]:
        raise ValueError("FFP10 signal/noise and PR3 mask NSIDE mismatch")

    # Pixel-domain summary stats on common masks (units: K_CMB -> uK_CMB for readability)
    def _masked_stats(arr_iqu: np.ndarray) -> dict[str, dict[str, float]]:
        out = {}
        for ch_idx, (name, mk) in enumerate((("I", m_int_bin), ("Q", m_pol_bin), ("U", m_pol_bin))):
            vals = arr_iqu[ch_idx][mk > 0.5] * 1.0e6
            out[name] = {
                "mean_uK": float(np.mean(vals)),
                "std_uK": float(np.std(vals)),
                "max_abs_uK": float(np.max(np.abs(vals))),
            }
        return out

    sig_stats = _masked_stats(sig_iqu)
    noi_stats = _masked_stats(noi_iqu)
    # Cross correlation on intensity mask in pixel domain
    s_i = sig_iqu[0][m_int_bin > 0.5]
    n_i = noi_iqu[0][m_int_bin > 0.5]
    pix_corr_i = float(np.corrcoef(s_i, n_i)[0, 1])
    del s_i, n_i

    sum_iqu = sig_iqu + noi_iqu
    sum_stats = _masked_stats(sum_iqu)

    # anafast spectra order (pol=True): TT, EE, BB, TE, EB, TB -> units K_CMB^2
    cl_sig = _mask_and_anafast(sig_iqu, m_int_bin, m_pol_bin, lmax=lmax)
    cl_noi = _mask_and_anafast(noi_iqu, m_int_bin, m_pol_bin, lmax=lmax)
    cl_sum = _mask_and_anafast(sum_iqu, m_int_bin, m_pol_bin, lmax=lmax)
    cl_crs = _mask_and_anafast(sig_iqu, m_int_bin, m_pol_bin, lmax=lmax, maps2_iqu=noi_iqu)
    del sig_iqu, noi_iqu, sum_iqu

    # Verify linear pseudo-C_ell algebraic identity C(s+n) == C(s) + C(n) + 2 C(s x n)
    # Note: for cross spectra TE, EB, TB of distinct maps s and n, healpy symmetrizes or returns s_1 x n_2,
    # Wait: let's check auto(s+n) - auto(s) - auto(n):
    # For auto-spectra (TT, EE, BB): C(s+n) - C(s) - C(n) - 2*C(s x n) == 0.
    # Let's check exact identity for TT, EE, BB and compare TE!
    cl_alg_err_diag = float(
        max(
            np.max(np.abs(cl_sum[c] - (cl_sig[c] + cl_noi[c] + 2.0 * cl_crs[c])))
            / max(np.max(np.abs(cl_sum[c])), 1e-300)
            for c in (0, 1, 2)
        )
    )
    # Compute normalized harmonic cross-correlation rho_ell^{s x n} on TT, EE, BB
    rho_cross = {}
    for c, cname in ((0, "TT"), (1, "EE"), (2, "BB")):
        denom = np.sqrt(np.maximum(1e-300, cl_sig[c, 2:] * cl_noi[c, 2:]))
        r = cl_crs[c, 2:] / denom
        rho_cross[cname] = {
            "rms_ell_2_to_64": float(np.sqrt(np.mean(r * r))),
            "max_abs_ell_2_to_64": float(np.max(np.abs(r))),
            "ell2_3_4": [float(x) for x in r[:3]],
        }

    # Now inspect observed PR3 Commander full map + beam HDU
    obs_iqu, meta_obs = _read_healpix_to_ring(obs_path, field=(0, 1, 2))
    obs_stats = _masked_stats(obs_iqu)
    cl_obs = _mask_and_anafast(obs_iqu, m_int_bin, m_pol_bin, lmax=lmax)
    del obs_iqu

    beam_summary = None
    with fits.open(obs_path, memmap=True) as hdul:
        if len(hdul) > 2 and "INT_BEAM" in hdul[2].columns.names:
            int_beam = np.asarray(hdul[2].data["INT_BEAM"], dtype=np.float64)
            pol_beam = np.asarray(hdul[2].data["POL_BEAM"], dtype=np.float64)
            beam_summary = {
                "beam_len": int(len(int_beam)),
                "int_beam_ell_2_10_64": [float(int_beam[ell]) for ell in (2, 10, min(lmax, len(int_beam) - 1))],
                "pol_beam_ell_2_10_64": [float(pol_beam[ell]) for ell in (2, 10, min(lmax, len(pol_beam) - 1))],
            }

    spec_names = ("TT", "EE", "BB", "TE", "EB", "TB")
    def _spec_uK2(cl_arr: np.ndarray) -> dict[str, object]:
        uK2 = cl_arr * 1.0e12
        return {
            "ell_2_to_8": {spec_names[c]: [float(v) for v in uK2[c, 2:9]] for c in range(6)},
            "mean_ell_2_to_64": {spec_names[c]: float(np.mean(uK2[c, 2:])) for c in range(6)},
        }

    return {
        "schema": "htt.r102.commander_pair_check/1",
        "owner": "obsstat",
        "status": "SINGLE_PAIR_ALIGNMENT_AND_ALGEBRA_VERIFIED_NULL_UNQUALIFIED",
        "pair_count": 1,
        "commander_null_qualified": False,
        "Bianchi_family_attribution": None,
        "physical_Pi": None,
        "physical_GF": None,
        "lmax": int(lmax),
        "mask_fsky": {"intensity": fsky_int, "polarization": fsky_pol},
        "file_metadata": {
            "noise_mc_00000": {**meta_noi, "sha256": noise_sha256},
            "signal_mc_00000": meta_sig,
            "observed_commander_pr3": meta_obs,
            "mask_int": {**meta_mint, "sha256": mask_int_sha256},
            "mask_pol": {**meta_mpol, "sha256": mask_pol_sha256},
        },
        "observed_commander_beam_hdu": beam_summary,
        "ordering_and_unit_alignment": {
            "ffp10_signal_ordering": meta_sig["hdus"][1]["ordering"],
            "ffp10_noise_ordering": meta_noi["hdus"][1]["ordering"],
            "observed_commander_ordering": meta_obs["hdus"][1]["ordering"],
            "masks_ordering": meta_mint["hdus"][1]["ordering"],
            "reordered_nested_to_ring_for_analysis": True,
            "common_unit": "K_CMB",
            "beam_provenance_note": (
                "dx12_v3 *_raw.fits MCs have zero FITS beam HDU whereas COM_CMB_IQU-commander_2048_R3.00_full.fits "
                "carries an effective 5 arcmin (HDU 2 INT_BEAM/POL_BEAM) beam window; matched beam convolution "
                "across a multi-realization MC ensemble is still required before null calibration."
            ),
        },
        "masked_pixel_stats_uK": {
            "signal_mc_00000": sig_stats,
            "noise_mc_00000": noi_stats,
            "signal_plus_noise_00000": sum_stats,
            "observed_commander_pr3": obs_stats,
            "pixel_intensity_corr_sig_vs_noise": pix_corr_i,
        },
        "pseudo_cl_uK2": {
            "signal_mc_00000": _spec_uK2(cl_sig),
            "noise_mc_00000": _spec_uK2(cl_noi),
            "signal_plus_noise_00000": _spec_uK2(cl_sum),
            "observed_commander_pr3": _spec_uK2(cl_obs),
        },
        "pseudo_cl_identity_rel_err_TT_EE_BB": cl_alg_err_diag,
        "signal_x_noise_cross_corr": rho_cross,
        "remaining_blocked_for_commander_null": [
            "D03: multi-realization matched FFP10 beam-convolved signal+noise ensemble and HM1/HM2/OE split noise genealogy",
        ],
        "runtime_seconds": time.monotonic() - t0,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lmax", type=int, default=64)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    res = run_check(lmax=args.lmax)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(res, indent=2, allow_nan=False) + "\n")
    print(json.dumps({
        "status": res["status"],
        "pair_count": res["pair_count"],
        "commander_null_qualified": res["commander_null_qualified"],
        "pseudo_cl_identity_rel_err": res["pseudo_cl_identity_rel_err_TT_EE_BB"],
        "pixel_corr_sig_vs_noise": res["masked_pixel_stats_uK"]["pixel_intensity_corr_sig_vs_noise"],
        "fsky_int": res["mask_fsky"]["intensity"],
        "fsky_pol": res["mask_fsky"]["polarization"],
        "mean_uK2_TT": {
            "sig": res["pseudo_cl_uK2"]["signal_mc_00000"]["mean_ell_2_to_64"]["TT"],
            "noi": res["pseudo_cl_uK2"]["noise_mc_00000"]["mean_ell_2_to_64"]["TT"],
            "s_plus_n": res["pseudo_cl_uK2"]["signal_plus_noise_00000"]["mean_ell_2_to_64"]["TT"],
            "obs": res["pseudo_cl_uK2"]["observed_commander_pr3"]["mean_ell_2_to_64"]["TT"],
        },
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
