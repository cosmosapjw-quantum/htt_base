#!/usr/bin/env python3
"""
extract_htt_data.py — HTT 파이프라인용 데이터 추출 스크립트
================================================================
로컬에서 실행하여 대용량 Planck/ACT 파일에서 필요한 데이터만 추출합니다.
추출된 파일들은 모두 합쳐서 ~5MB 이내이므로 쉽게 업로드할 수 있습니다.

사용법:
  python extract_htt_data.py --planck-dir ./planck_data --act-dir ./act_data --out ./htt_extracted

필요 패키지:
  pip install numpy astropy healpy sacc

입력 파일 (있는 것만 처리, 없으면 skip):
  planck_data/
    COM_PowerSpect_CMB-TT-full_R3.01.txt          (~167KB)
    COM_PowerSpect_CMB-TE-full_R3.01.txt           (~133KB)
    COM_PowerSpect_CMB-EE-full_R3.01.txt           (~133KB)
    COM_PowerSpect_CMB-TT-binned_R3.01.txt         (~7KB)
    COM_PowerSpect_CMB-low-ell-BB-full_R3.01.txt
    COM_PowerSpect_CMB-low-ell-EB-full_R3.01.txt
    COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt
    COM_PowerSpect_CMB_R2.02.fits                   (이미 업로드한 파일)
    COM_CMB_IQU-commander_2048_R3.00_full.fits      (~1.6GB → 추출 후 ~50KB)
    COM_CMB_IQU-smica_2048_R3.00_full.fits          (~1.6GB → 추출 후 ~50KB)
    COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits    (~200MB → 추출 후 ~10KB)
    COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits
  act_data/
    ACTDR6MFLike_v1.0/ 또는 dr6_data.fits
    ACT_dr6_likelihood_v1.2/

출력:
  htt_extracted/
    planck_tt_full_R3.01.npz        — TT 파워스펙트럼 (ℓ=2..2508)
    planck_te_full_R3.01.npz        — TE
    planck_ee_full_R3.01.npz        — EE
    planck_tt_binned_R3.01.npz      — TT binned
    planck_lowl_BB_R3.01.npz        — low-ℓ BB
    planck_theory_R3.01.npz         — best-fit ΛCDM theory (TT,TE,EE,BB)
    planck_commander_map_nside16.npz — Commander CMB map downgraded to NSIDE=16
    planck_smica_map_nside16.npz     — SMICA CMB map downgraded to NSIDE=16
    planck_mask_temp_nside16.npz     — Temperature mask downgraded to NSIDE=16
    planck_mask_pol_nside16.npz      — Polarization mask
    act_dr6_tt_bandpowers.npz       — ACT DR6 TT coadded bandpowers
    act_dr6_te_bandpowers.npz       — ACT DR6 TE
    act_dr6_ee_bandpowers.npz       — ACT DR6 EE
    extraction_log.txt              — 추출 로그
"""

import os
import sys
import argparse
import numpy as np
from datetime import datetime

from dl_fits_utils import format_fits_size, inspect_fits_file

def log(msg, logfile=None):
    print(msg)
    if logfile:
        logfile.write(msg + "\n")


def preflight_fits(path, label, kind, logf):
    """Return False when a FITS file is known-bad and should be skipped."""
    report = inspect_fits_file(path)
    if report.status == "truncated":
        log(
            f"  SKIP: {label} {kind} is truncated "
            f"(actual={format_fits_size(report.actual_size)}, "
            f"expected={format_fits_size(report.expected_size)}).",
            logf,
        )
        log(
            "        Delete the local FITS and re-download it, or rerun "
            "`FORCE=1 bash dl_pipeline/run_all.sh` to refresh the file.",
            logf,
        )
        return False
    if report.status == "unreadable":
        log(f"  SKIP: {label} {kind} is unreadable ({report.detail})", logf)
        return False
    return True


# ═══════════════════════════════════════════════════════════════
# 1. Planck Power Spectra (텍스트 파일 → npz)
# ═══════════════════════════════════════════════════════════════

def extract_planck_spectrum(path, out_path, spec_type, logf):
    """Planck TT/TE/EE full spectrum 텍스트 → npz"""
    if not os.path.exists(path):
        log(f"  SKIP: {os.path.basename(path)} not found", logf)
        return False
    
    data = np.loadtxt(path, comments='#')
    ell = data[:, 0].astype(int)
    dl = data[:, 1].astype(np.float64)
    
    if data.shape[1] >= 4:
        # low-ℓ format: [ℓ, D_ℓ, -σ, +σ]
        err_lo = np.abs(data[:, 2])
        err_hi = np.abs(data[:, 3])
    elif data.shape[1] >= 3:
        # high-ℓ format: [ℓ, D_ℓ, σ]
        err_lo = np.abs(data[:, 2])
        err_hi = err_lo.copy()
    else:
        err_lo = np.zeros_like(dl)
        err_hi = np.zeros_like(dl)
    
    # Best-fit theory if present (4th or 5th column)
    bestfit = data[:, -1] if data.shape[1] >= 5 else np.zeros_like(dl)
    
    np.savez(out_path,
        ell=ell, dl=dl, err_lo=err_lo, err_hi=err_hi,
        bestfit=bestfit, spectrum_type=spec_type,
        source=os.path.basename(path))
    
    size_kb = os.path.getsize(out_path) / 1024
    log(f"  ✓ {spec_type}: ℓ={ell[0]}..{ell[-1]} ({len(ell)} pts) → {size_kb:.1f} KB", logf)
    return True


def extract_planck_theory(path, out_path, logf):
    """Planck best-fit ΛCDM theory spectrum → npz"""
    if not os.path.exists(path):
        log(f"  SKIP: theory file not found", logf)
        return False
    
    data = np.loadtxt(path, comments='#')
    # Format: [ℓ, TT, TE, EE, BB, PP(lensing)]
    ell = data[:, 0].astype(int)
    
    out = dict(ell=ell, source=os.path.basename(path))
    labels = ['TT', 'TE', 'EE', 'BB', 'PP']
    for i, lab in enumerate(labels):
        if i + 1 < data.shape[1]:
            out[f'dl_{lab}'] = data[:, i + 1].astype(np.float64)
    
    np.savez(out_path, **out)
    size_kb = os.path.getsize(out_path) / 1024
    log(f"  ✓ Theory: ℓ={ell[0]}..{ell[-1]}, cols={list(out.keys())} → {size_kb:.1f} KB", logf)
    return True


# ═══════════════════════════════════════════════════════════════
# 2. Planck R2.02 FITS (이미 업로드된 파일과 같은 형식)
# ═══════════════════════════════════════════════════════════════

def extract_r202_fits(path, out_dir, logf):
    """COM_PowerSpect_CMB_R2.02.fits → 개별 npz"""
    if not os.path.exists(path):
        log(f"  SKIP: R2.02 FITS not found", logf)
        return False

    if not preflight_fits(path, 'R2.02', 'FITS', logf):
        return False
    
    from astropy.io import fits
    f = fits.open(path)
    
    extensions = {
        'TTLOLUNB': ('lowl_TT', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
        'TELOLUNB': ('lowl_TE', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
        'EELOLUNB': ('lowl_EE', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
        'BBLOLUNB': ('lowl_BB', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
        'EBLOLUNB': ('lowl_EB', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
        'TBLOLUNB': ('lowl_TB', ['ELL', 'D_ELL', 'ERRUP', 'ERRDOWN']),
    }
    
    for ext_name, (label, cols) in extensions.items():
        try:
            data = f[ext_name].data
            out = {c.lower(): np.array(data[c]) for c in cols}
            out['source'] = f'R2.02/{ext_name}'
            out_path = os.path.join(out_dir, f'planck_R2.02_{label}.npz')
            np.savez(out_path, **out)
            log(f"  ✓ R2.02 {label}: {len(data)} pts", logf)
        except KeyError:
            log(f"  SKIP: R2.02 extension {ext_name} not found", logf)
    
    f.close()
    return True


# ═══════════════════════════════════════════════════════════════
# 3. CMB Maps → NSIDE=16 downgrade (1.6GB → ~50KB)
# ═══════════════════════════════════════════════════════════════

def extract_cmb_map(path, out_path, label, logf,
                    nside_out=16, full_res_out_path=None):
    """고해상도 CMB map → NSIDE downgrade + optional full-resolution NPZ dump."""
    if not os.path.exists(path):
        log(f"  SKIP: {label} map not found", logf)
        return False

    try:
        import healpy as hp
    except ImportError:
        log(f"  SKIP: healpy not installed (pip install healpy)", logf)
        return False

    if not preflight_fits(path, label, 'map FITS', logf):
        return False

    log(f"  Loading {label} map (this may take ~30s for 1.6GB file)...", logf)

    # Read I, Q, U maps
    try:
        maps = hp.read_map(path, field=[0, 1, 2], dtype=np.float64)
    except Exception as exc:
        log(f"  SKIP: failed to read {label} map FITS ({type(exc).__name__}: {exc})", logf)
        return False
    nside_in = hp.npix2nside(maps.shape[1])

    # Unit detection from the full-resolution map (downgrade is UNIT-preserving
    # but heavy averaging can shrink amplitudes; doing it here is robust).
    if np.max(np.abs(maps[0])) < 0.01:  # Likely in K_CMB, not μK
        maps_uK = maps * 1e6
        unit = 'uK (converted from K_CMB)'
    else:
        maps_uK = maps
        unit = 'uK (assumed)'

    # Optional full-resolution dump (NSIDE=nside_in preserved).
    if full_res_out_path is not None:
        np.savez(full_res_out_path,
            I=maps_uK[0].astype(np.float32),
            Q=maps_uK[1].astype(np.float32),
            U=maps_uK[2].astype(np.float32),
            nside=nside_in, npix=hp.nside2npix(nside_in), unit=unit,
            source=os.path.basename(path))
        size_mb = os.path.getsize(full_res_out_path) / 1024 / 1024
        log(f"  ✓ {label} [full-res]: NSIDE={nside_in}, I/Q/U float32, {size_mb:.1f} MB", logf)

    # Downgrade to pixel-likelihood resolution.
    maps_low = np.array([hp.ud_grade(m, nside_out) for m in maps_uK])
    np.savez(out_path,
        I=maps_low[0].astype(np.float32),
        Q=maps_low[1].astype(np.float32),
        U=maps_low[2].astype(np.float32),
        nside=nside_out, nside_original=nside_in,
        npix=hp.nside2npix(nside_out), unit=unit,
        source=os.path.basename(path))

    size_kb = os.path.getsize(out_path) / 1024
    log(f"  ✓ {label}: NSIDE {nside_in}→{nside_out}, I/Q/U, {size_kb:.1f} KB", logf)
    return True


def extract_mask(path, out_path, label, logf,
                 nside_out=16, full_res_out_path=None):
    """고해상도 mask → NSIDE downgrade + optional full-resolution NPZ dump."""
    if not os.path.exists(path):
        log(f"  SKIP: {label} mask not found", logf)
        return False

    try:
        import healpy as hp
    except ImportError:
        log(f"  SKIP: healpy not installed", logf)
        return False

    if not preflight_fits(path, label, 'mask FITS', logf):
        return False

    try:
        mask = hp.read_map(path, dtype=np.float64)
    except Exception as exc:
        log(f"  SKIP: failed to read {label} mask FITS ({type(exc).__name__}: {exc})", logf)
        return False
    nside_in = hp.npix2nside(len(mask))

    if full_res_out_path is not None:
        mask_full = (mask > 0.5).astype(np.float32)
        np.savez(full_res_out_path,
            mask=mask_full, fsky=float(np.mean(mask_full)),
            nside=nside_in, source=os.path.basename(path))
        size_mb = os.path.getsize(full_res_out_path) / 1024 / 1024
        log(f"  ✓ {label} [full-res]: NSIDE={nside_in}, fsky={float(np.mean(mask_full)):.3f}, {size_mb:.1f} MB", logf)

    # Downgrade: pixel is "observed" if >50% of sub-pixels are observed
    mask_low = hp.ud_grade(mask, nside_out)
    mask_binary = (mask_low > 0.5).astype(np.float32)
    f_sky = np.mean(mask_binary)

    np.savez(out_path,
        mask=mask_binary, fsky=f_sky,
        nside=nside_out, nside_original=nside_in,
        source=os.path.basename(path))

    size_kb = os.path.getsize(out_path) / 1024
    log(f"  ✓ {label}: NSIDE {nside_in}→{nside_out}, f_sky={f_sky:.3f}, {size_kb:.1f} KB", logf)
    return True


# ═══════════════════════════════════════════════════════════════
# 4. ACT DR6 Bandpowers
# ═══════════════════════════════════════════════════════════════

def extract_act_dr6(act_dir, out_dir, logf):
    """ACT DR6 multi-frequency data → coadded bandpowers"""
    
    # Method 1: sacc file
    sacc_candidates = [
        os.path.join(act_dir, 'ACTDR6MFLike', 'v1.0', 'dr6_data.fits'),
        os.path.join(act_dir, 'v1.0', 'dr6_data.fits'),
        os.path.join(act_dir, 'dr6_data.fits'),
    ]
    
    sacc_path = None
    for p in sacc_candidates:
        if os.path.exists(p):
            sacc_path = p
            break
    
    if sacc_path is None:
        log(f"  SKIP: dr6_data.fits not found in {act_dir}", logf)
        log(f"  Searched: {sacc_candidates}", logf)
        return False
    
    try:
        import sacc
    except ImportError:
        log(f"  SKIP: sacc not installed (pip install sacc)", logf)
        return False
    
    log(f"  Loading ACT DR6 sacc file: {sacc_path}", logf)
    s = sacc.Sacc.load_fits(sacc_path)
    
    # List available tracers
    tracers = list(s.tracers.keys())
    log(f"  Tracers: {tracers}", logf)
    
    # Extract for each spectrum type
    # ACT may use either cl_00/cl_0e/cl_ee or cmb_temperature_cl etc.
    type_map = {
        'TT': ['cl_00', 'cmb_temperature_cl'],
        'TE': ['cl_0e', 'cmb_temperaturePolarization_cl_e'],
        'EE': ['cl_ee', 'cmb_polarization_cl_ee'],
    }
    for spec_type, sacc_types in type_map.items():
        extracted = False
        for sacc_type in sacc_types:
            if extracted:
                break
            try:
                tracer_pairs = []
                for t1 in tracers:
                    for t2 in tracers:
                        try:
                            ell, cl = s.get_ell_cl(sacc_type, t1, t2)
                            if len(ell) > 0:
                                tracer_pairs.append((t1, t2, len(ell)))
                        except:
                            pass
                
                if not tracer_pairs:
                    continue  # try next sacc_type
                
                tracer_pairs.sort(key=lambda x: x[2], reverse=True)
                t1, t2, n = tracer_pairs[0]
                
                ell, cl, cov = s.get_ell_cl(sacc_type, t1, t2, return_cov=True)
                err = np.sqrt(np.diag(cov))
                
                dl = ell * (ell + 1) / (2 * np.pi) * cl
                dl_err = ell * (ell + 1) / (2 * np.pi) * err
                
                out_path = os.path.join(out_dir, f'act_dr6_{spec_type.lower()}_bandpowers.npz')
                np.savez(out_path,
                    ell=ell.astype(np.float64),
                    dl=dl.astype(np.float64),
                    dl_err=dl_err.astype(np.float64),
                    cl=cl.astype(np.float64),
                    cl_err=err.astype(np.float64),
                    tracer1=t1, tracer2=t2,
                    spectrum_type=spec_type,
                    source=f'ACT_DR6/{t1}x{t2}')
                
                size_kb = os.path.getsize(out_path) / 1024
                log(f"  ✓ ACT {spec_type} ({t1}×{t2}): ℓ={ell[0]:.0f}..{ell[-1]:.0f} ({len(ell)} bins) → {size_kb:.1f} KB", logf)
                extracted = True
            
            except Exception as e:
                log(f"  ACT {spec_type} with {sacc_type}: {e}", logf)
        
        if not extracted:
            log(f"  SKIP: No {spec_type} data found in ACT DR6", logf)
    
    return True


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='HTT 데이터 추출')
    parser.add_argument('--planck-dir', default='./planck_data',
                        help='Planck 데이터 디렉토리')
    parser.add_argument('--act-dir', default='./act_data',
                        help='ACT 데이터 디렉토리')
    parser.add_argument('--out', default='./htt_extracted',
                        help='출력 디렉토리')
    parser.add_argument('--planck-nside-out', type=int, default=16,
                        help='Target NSIDE for the downgraded CMB maps + masks. '
                             'Default 16 (canonical low-ℓ pixel-likelihood resolution). '
                             'Local-dev can raise this to 64/128/256 if a downstream '
                             'analysis wants more modes.')
    parser.add_argument('--full-res-maps', action='store_true',
                        help='Also dump full-resolution (NSIDE=2048) I/Q/U maps and '
                             'binary masks as planck_*_full.npz (~200 MB per map). '
                             'Off by default; enable when you need the raw pixel data '
                             'without touching the original FITS.')
    parser.add_argument('--only-act', action='store_true',
                        help='Extract only ACT DR6 bandpowers from --act-dir; skip Planck inputs.')
    args = parser.parse_args()
    
    os.makedirs(args.out, exist_ok=True)
    logpath = os.path.join(args.out, 'extraction_log.txt')
    logf = open(logpath, 'w')
    
    log(f"═══ HTT Data Extraction ═══", logf)
    log(f"Date: {datetime.now().isoformat()}", logf)
    log(f"Planck dir: {args.planck_dir}", logf)
    log(f"ACT dir: {args.act_dir}", logf)
    log(f"Output: {args.out}\n", logf)
    
    n_ok = 0
    if args.only_act:
        log("\n── ACT DR6 Bandpowers ──", logf)
        if extract_act_dr6(args.act_dir, args.out, logf):
            n_ok += 1
        total_size = sum(
            os.path.getsize(os.path.join(args.out, f))
            for f in os.listdir(args.out) if f.endswith('.npz')
        ) / 1024
        log(f"\n═══ Summary ═══", logf)
        log(f"Extracted: {n_ok} items", logf)
        log(f"Total size: {total_size:.1f} KB ({total_size/1024:.2f} MB)", logf)
        log(f"Output: {args.out}/", logf)
        logf.close()
        print(f"\nDone. Log: {logpath}")
        return

    pdir = args.planck_dir
    
    # ── Planck PR3 Power Spectra ──
    log("── Planck PR3 Power Spectra ──", logf)
    spectra = [
        ('COM_PowerSpect_CMB-TT-full_R3.01.txt', 'planck_tt_full_R3.01.npz', 'TT'),
        ('COM_PowerSpect_CMB-TE-full_R3.01.txt', 'planck_te_full_R3.01.npz', 'TE'),
        ('COM_PowerSpect_CMB-EE-full_R3.01.txt', 'planck_ee_full_R3.01.npz', 'EE'),
        ('COM_PowerSpect_CMB-TT-binned_R3.01.txt', 'planck_tt_binned_R3.01.npz', 'TT_binned'),
        ('COM_PowerSpect_CMB-low-ell-BB-full_R3.01.txt', 'planck_lowl_BB_R3.01.npz', 'BB_lowl'),
        ('COM_PowerSpect_CMB-low-ell-EB-full_R3.01.txt', 'planck_lowl_EB_R3.01.npz', 'EB_lowl'),
    ]
    for fname, out_name, stype in spectra:
        if extract_planck_spectrum(
            os.path.join(pdir, fname),
            os.path.join(args.out, out_name), stype, logf):
            n_ok += 1
    
    # ── Planck Theory Spectrum ──
    log("\n── Planck Best-fit Theory ──", logf)
    if extract_planck_theory(
        os.path.join(pdir, 'COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt'),
        os.path.join(args.out, 'planck_theory_R3.01.npz'), logf):
        n_ok += 1
    
    # ── R2.02 FITS (if present) ──
    log("\n── Planck R2.02 FITS ──", logf)
    r202 = os.path.join(pdir, 'COM_PowerSpect_CMB_R2.02.fits')
    if extract_r202_fits(r202, args.out, logf):
        n_ok += 1
    
    nside_out = args.planck_nside_out
    want_full = args.full_res_maps

    # ── CMB Maps (downgrade) ──
    log(f"\n── CMB Maps → NSIDE={nside_out}{' (+ full-res dump)' if want_full else ''} ──", logf)
    maps = [
        ('COM_CMB_IQU-commander_2048_R3.00_full.fits', 'commander', 'Commander'),
        ('COM_CMB_IQU-smica_2048_R3.00_full.fits',     'smica',     'SMICA'),
    ]
    for fname, stem, label in maps:
        out_name = f'planck_{stem}_map_nside{nside_out}.npz'
        full_path = os.path.join(args.out, f'planck_{stem}_map_full.npz') if want_full else None
        if extract_cmb_map(
                os.path.join(pdir, fname),
                os.path.join(args.out, out_name), label, logf,
                nside_out=nside_out, full_res_out_path=full_path):
            n_ok += 1

    # ── Masks (downgrade) ──
    log(f"\n── Masks → NSIDE={nside_out}{' (+ full-res dump)' if want_full else ''} ──", logf)
    masks = [
        ('COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits', 'temp', 'Temp mask'),
        ('COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits', 'pol',  'Pol mask'),
    ]
    for fname, stem, label in masks:
        out_name = f'planck_mask_{stem}_nside{nside_out}.npz'
        full_path = os.path.join(args.out, f'planck_mask_{stem}_full.npz') if want_full else None
        if extract_mask(
                os.path.join(pdir, fname),
                os.path.join(args.out, out_name), label, logf,
                nside_out=nside_out, full_res_out_path=full_path):
            n_ok += 1
    
    # ── ACT DR6 ──
    log("\n── ACT DR6 Bandpowers ──", logf)
    if extract_act_dr6(args.act_dir, args.out, logf):
        n_ok += 1
    
    # ── Summary ──
    total_size = sum(
        os.path.getsize(os.path.join(args.out, f))
        for f in os.listdir(args.out) if f.endswith('.npz')
    ) / 1024
    
    log(f"\n═══ Summary ═══", logf)
    log(f"Extracted: {n_ok} items", logf)
    log(f"Total size: {total_size:.1f} KB ({total_size/1024:.2f} MB)", logf)
    log(f"Output: {args.out}/", logf)
    log(f"Files:", logf)
    for f in sorted(os.listdir(args.out)):
        sz = os.path.getsize(os.path.join(args.out, f)) / 1024
        log(f"  {f:50s} {sz:8.1f} KB", logf)
    
    logf.close()
    print(f"\nDone. Log: {logpath}")
    print(f"이 디렉토리({args.out})의 .npz 파일들을 업로드해주세요.")


if __name__ == '__main__':
    main()
