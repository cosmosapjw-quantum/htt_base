#!/usr/bin/env python3
"""Bounded RB18/19 released spectra and native-pixel polarization diagnostics.

No official full-likelihood parity, independent-sky multiplication, transfer
inversion, primordial interpretation, or native solver admission.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import time

import numpy as np
from scipy.linalg import cho_factor, cho_solve


ONLINE_SOURCES = {
    "planck": "https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/",
    "act-dr4": "https://github.com/ACTCollaboration/pyactlike/blob/master/pyactlike/like.py",
    "spt3g": "https://lambda.gsfc.nasa.gov/product/spt/",
    "class-splits": "https://lambda.gsfc.nasa.gov/product/class/class_dr1_pol_maps_info.html",
    "class-masks": "https://lambda.gsfc.nasa.gov/product/class/class_dr1_masks_info.html",
    "beyondplanck-n8": "https://beyondplanck.science/products/files_v2/",
    "ffp10-headers": "https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/",
}


def finite(x, name="array"):
    a = np.asarray(x, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError("nonfinite " + name)
    return a


def dl_to_cl(ell, dl):
    ell, dl = finite(ell), finite(dl)
    if ell.shape != dl.shape or np.any(ell < 2):
        raise ValueError("aligned ell>=2 required for Dl-to-Cl conversion")
    return dl * (2*np.pi) / (ell*(ell+1))


def exact_reference(ell, reference_ell, reference):
    ell = np.asarray(ell)
    rell = np.asarray(reference_ell)
    if ell.ndim != 1 or rell.ndim != 1 or np.any(np.diff(rell) <= 0):
        raise ValueError("ordered one-dimensional reference grid required")
    idx = np.searchsorted(rell, ell)
    if np.any(idx >= len(rell)) or not np.array_equal(rell[idx], ell):
        raise ValueError("reference lacks exact released multipoles")
    return finite(reference)[idx]


def residuals(data, reference, err_lo, err_hi):
    d, t, lo, hi = map(finite, (data, reference, err_lo, err_hi))
    if d.ndim != 1 or any(a.shape != d.shape for a in (t, lo, hi)):
        raise ValueError("aligned residual rows required")
    if np.any(lo <= 0) or np.any(hi <= 0):
        raise ValueError("positive quoted errors required")
    r = d-t
    sigma = np.where(r >= 0, lo, hi)
    return {"data": d, "reference": t, "residual": r,
            "err_lo": lo, "err_hi": hi,
            "signed_residual_over_error_toward_reference": r/sigma}


def covariance_quadratic(covariance, residual):
    c = finite(covariance)
    if c.shape != (len(residual), len(residual)) or not np.allclose(c, c.T, rtol=1e-10, atol=1e-16):
        raise ValueError("aligned symmetric covariance required")
    try:
        solved = cho_solve(cho_factor(c, lower=True), finite(residual))
    except np.linalg.LinAlgError:
        return {"quadratic": None, "status": "HOLD_NONPOSITIVE_DEFINITE_UNMODIFIED_COVARIANCE"}
    return {"quadratic": float(residual @ solved), "status": "DESCRIPTIVE_QUADRATIC_NO_CALIBRATED_P"}


def fortran_covariance(raw, n):
    """Released ACT little-endian float64 single Fortran sequential record."""
    expected = n*n*8
    if len(raw) != expected+8:
        raise ValueError("unexpected ACT Fortran covariance record length")
    start = int(np.frombuffer(raw[:4], dtype="<u4")[0])
    end = int(np.frombuffer(raw[-4:], dtype="<u4")[0])
    if start != expected or end != expected:
        raise ValueError("ACT Fortran record markers disagree")
    c = finite(np.frombuffer(raw[4:-4], dtype="<f8").reshape(n,n)).copy()
    # Source loader copies lower-triangle entries into the upper triangle.
    return np.tril(c)+np.tril(c,-1).T


def act_window_model(deep, wide, theory_table, yp2):
    theory = finite(theory_table)
    if deep.shape != (520,7924) or wide.shape != deep.shape:
        raise ValueError("ACT 520x7924 released windows required")
    if not np.isfinite(yp2) or yp2 <= 0:
        raise ValueError("positive polarization efficiency required")
    expected = np.arange(2,5001)
    idx = np.searchsorted(theory[:,0], expected)
    if np.any(idx >= len(theory)) or not np.array_equal(theory[idx,0], expected):
        raise ValueError("ACT fixed theory must cover ell2..5000 exactly")
    cls = []
    # Released theory columns are ell, TT, TE, EE, BB, PP.
    for column in (1,2,3):
        c = np.zeros(7924)
        c[:4999] = dl_to_cl(expected, theory[idx,column])
        cls.append(c)
    outputs = []
    for windows in (deep, wide):
        tt = windows[104:156] @ cls[0]
        te = windows[312:364] @ cls[1]
        ee = windows[468:520] @ cls[2]
        outputs.extend((tt[5:45], te[:45]*yp2, ee[:45]*yp2**2))
    return np.concatenate(outputs)


def planck(root):
    base = root / "workdir/obs_bundle/cmb"
    reference = base / "theory/planck_pr3_bestfit.npz"
    files = [reference, root/"workdir/obs_bundle/INDEX.json"]
    with np.load(reference, allow_pickle=False) as a:
        ref = {k: a[k] for k in a.files}
    records = []
    for channel, suffix in (("TT","tt_full"),("TE","te_full"),("EE","ee_full"),
                            ("BB","bb_lowl"),("EB","eb_lowl")):
        path = base / ("powerspectra/planck_pr3_"+suffix+".npz"); files.append(path)
        with np.load(path, allow_pickle=False) as a:
            ell = a["ell"]
            model = np.zeros(len(ell)) if channel == "EB" else exact_reference(ell, ref["ell"],ref["dl_"+channel])
            record = residuals(a["dl"], model, a["err_lo"], a["err_hi"])
            record.update({"channel": channel, "ell": ell, "unit": "uK_CMB^2 (Dl)",
                           "source": str(a["source"].item()),
                           "reference_source": "DECLARED_ZERO_EB_PARITY_REFERENCE" if channel == "EB" else str(ref["source"].item()),
                           "embedded_bestfit_all_zero": bool(np.all(a["bestfit"] == 0))})
        bands = []
        for low, high in ((2,30),(30,300),(300,1000),(1000,2600)):
            keep = (ell>=low)&(ell<high)
            if keep.any():
                values = record["signed_residual_over_error_toward_reference"][keep]
                bands.append({"ell_interval_half_open": [low,high], "rows": int(keep.sum()),
                              "median_signed_scaled_residual": float(np.median(values)),
                              "rms_scaled_residual_descriptive": float(np.sqrt(np.mean(values**2)))})
        record["fixed_band_descriptives"] = bands
        records.append(record)
    return {"owner":"OBSSTAT", "scope":"PLANCK_PR3_FIXED_REFERENCE_RESIDUAL_DESCRIPTIVES",
            "records":records,
            "caveats":["Full TT/TE/EE bestfit arrays are placeholders; separate released theory used",
                       "EB zero is a declared parity-reference comparison; BB uses released lensed-BB reference",
                       "Quoted marginal error ratios do not define a joint likelihood or calibrated chi-square",
                       "Channels share the sky; no independent likelihood multiplication",
                       "No native solver or Bianchi family inference"]}, files, []


def act_dr4(root):
    path = root / "workdir/downloads/actpollite_python_dr4.01.tar.gz"
    prefix = "actpollite_python_dr4.01/pyactlike/"
    members = []
    with tarfile.open(path) as archive:
        def read(member):
            name = prefix+member; raw = archive.extractfile(name).read()
            members.append({"archive":str(path.relative_to(root)), "member":name,
                            "sha256":hashlib.sha256(raw).hexdigest(), "size_bytes":len(raw)})
            return raw
        table = finite(np.loadtxt(io.BytesIO(read("data/cl_cmb_ap.dat"))))
        covariance = fortran_covariance(read("data/c_matrix_ap.dat"),260)
        theory = finite(np.loadtxt(io.BytesIO(read("data/bf_ACTPol_lcdm.minimum.theory_cl"))))
        windows = []
        for member in ("data/coadd_bpwf_15mJy_191127_lmin2.npz", "data/coadd_bpwf_100mJy_191127_lmin2.npz"):
            with np.load(io.BytesIO(read(member)), allow_pickle=False) as a:
                windows.append(finite(a["bpwf"]))
        read("like.py")
    if table.shape != (260,3) or np.any(np.diag(covariance)<=0):
        raise ValueError("ACT released 260-row data/covariance convention failed")
    scenarios = []
    labels = np.repeat(["deep_TT","deep_TE","deep_EE","wide_TT","wide_TE","wide_EE"], [40,45,45,40,45,45])
    for yp2 in (.95,.97,1.,1.03):
        model = act_window_model(*windows, theory, yp2)
        sigma = np.sqrt(np.diag(covariance))
        row = residuals(table[:,1], model, sigma,sigma)
        row.update({"yp2":yp2, **covariance_quadratic(covariance,row["residual"])})
        scenarios.append(row)
    return {"owner":"HTT", "scope":"ACT_DR4_ARCHIVE_WINDOWED_FIXED_YP2_SENSITIVITY",
            "ell_effective":table[:,0], "row_channels":labels, "scenarios":scenarios,
            "unit":"uK_CMB^2; source-window-contracted Cl convention",
            "caveats":["Deep then wide TT40/TE45/EE45; exact archived windows and full covariance",
                       "Source procedure: Dl->Cl, 150x150 window blocks, TT bins5:45, TE/EE first45",
                       "Theory truncated above ell5000 exactly as archived standalone default, not a missing-input fill",
                       "yp2 grid fixed at 0.95,0.97,1,1.03; no optimization or posterior",
                       "Foregrounds already marginalized by release; official full-likelihood runtime parity not established",
                       "Do not substitute plotting-only coadded Dl errors for this covariance",
                       "No calibrated quadratic p-value or independent combination with Planck"]}, [path], members


def dataset_fields(path):
    fields = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#",1)[0].strip()
        if "=" in line:
            key,value = line.split("=",1);fields[key.strip()] = value.strip()
    return fields


def spt_window_model(windows, ell, dl_by_channel, spectrum_names):
    """Input windows are bin x ell x spectrum; input spectra are Dl."""
    w = finite(windows); ell = np.asarray(ell)
    if w.ndim != 3 or w.shape[1] != len(ell) or w.shape[2] != len(spectrum_names):
        raise ValueError("SPT window/spectrum dimensions mismatch")
    out = np.empty((len(spectrum_names),w.shape[0]))
    for i,name in enumerate(spectrum_names):
        left,right = name.split("x")
        channel = left[-1]+right[-1]
        d = finite(dl_by_channel[channel])
        if d.shape != ell.shape:
            raise ValueError("SPT reference does not match window ell grid")
        out[i] = w[:,:,i] @ d
    return out


def spt3g(root):
    path = root / "workdir/compact_products/spt3g_y1_compact.npz"
    released = root / "workdir/obs_bundle/spt3g_y1_v11_obs01/extracted/SPT3G_2018_TTTEEE_public_likelihood"
    config = released / "data/SPT3G_2018_TTTEEE/SPT3G_2018_TTTEEE.dataset"
    fields = dataset_fields(config); stem = "SPT3G_2018_TTTEEE_"
    names = fields[stem+"bandpower_file_order"].split()
    if any(fields[stem+k].split() != names for k in ("spectra_to_fit","covariance_matrix_order","beam_covariance_matrix_order","window_folder_order")):
        raise ValueError("SPT released block ordering differs; explicit reordering required")
    lower = np.array([int(x) for x in fields[stem+"spectra_to_fit_bin_min"].split()])
    upper = np.array([int(x) for x in fields[stem+"spectra_to_fit_bin_max"].split()])
    if len(names)!=18 or lower.shape!=(18,) or upper.shape!=(18,) or np.any(lower<1) or np.any(upper>44):
        raise ValueError("SPT 18x44 bin contract failed")
    expected_tt = [10,10,10,10,15,15]
    for minimum,name in zip(lower,names):
        if name.endswith("_T") and name.split("x")[0].endswith("_T"):
            if minimum < expected_tt.pop(0):
                raise ValueError("SPT selected a placeholder TT bin")
    with np.load(path,allow_pickle=False) as a:
        data = finite(a["bandpowers__SPT3G_2018_TTTEEE_bandpowers_dat"]).reshape(-1)
        c = finite(a["cov__SPT3G_2018_TTTEEE_covariance_dat"])
        beam = finite(a["cov__SPT3G_2018_TTTEEE_beam_covariance_dat"])
        blocks = [finite(a[f"windows__window_{b}_txt"]) for b in range(1,45)]
    if data.shape!=(792,) or c.shape!=(792,792) or beam.shape!=c.shape or any(w.shape!=(3200,19) for w in blocks):
        raise ValueError("SPT released arrays do not satisfy schema")
    ell = blocks[0][:,0].astype(int)
    if not np.array_equal(ell,np.arange(1,3201)) or any(not np.array_equal(w[:,0],ell) for w in blocks):
        raise ValueError("SPT window ell ordering changed")
    windows = np.stack([w[:,1:] for w in blocks])
    refpath = root / "workdir/compact_products/camb_planck2018_lensing_refs.npz"
    with np.load(refpath,allow_pickle=False) as ref:
        spectra = {ch:exact_reference(ell,ref["ell_cmb"],ref["Dl_"+ch]) for ch in ("TT","TE","EE")}
    fullmodel = spt_window_model(windows,ell,spectra,names).reshape(-1)
    idx = np.concatenate([44*i+np.arange(lo-1,hi) for i,(lo,hi) in enumerate(zip(lower,upper))])
    model = fullmodel[idx]; data=data[idx]; c=c[np.ix_(idx,idx)];beam=beam[np.ix_(idx,idx)]
    scenarios = []
    for scale in (0.,1.):
        total = c+scale*np.outer(model,model)*beam
        sigma = np.sqrt(np.diag(total))
        row = residuals(data,model,sigma,sigma)
        row.update({"fractional_beam_scale":scale, **covariance_quadratic(total,row["residual"])})
        scenarios.append(row)
    return {"owner":"HTT", "scope":"SPT3G_SOURCE_ORDERED_CMB_ONLY_WINDOW_AND_BEAM_CONTROL",
            "spectra":names,"bin_min":lower,"bin_max":upper,"release_indices":idx,
            "row_spectra":[names[i//44] for i in idx], "row_bin_number":idx%44+1,
            "scenarios":scenarios, "unit":"uK_CMB^2 (window-contracted Dl)",
            "caveats":["Fixed Planck2018 CAMB reference; foregrounds zero, calibration unity, SSL/aberration disabled",
                       "CMB-only residuals include omitted foregrounds; not an adequacy test of the cosmological model",
                       "Actual dataset cuts exclude placeholder TT bins; window columns follow declared spectrum order",
                       "Fractional beam covariance multiplies outer(theory,theory)",
                       "No covariance flooring; nonpositive-definite matrices return typed HOLD",
                       "Official eigenmode conditioning/nuisance likelihood parity not established",
                       "No fitted nuisance posterior or calibrated quadratic p-value"]}, [path,config,refpath,
                released/"SPT3G_2018_TTTEEE_README.txt",released/"source/CMB_SPT3G_2018_TTTEEE.f90"], []


def fits_header(path):
    from astropy.io import fits
    with fits.open(path,memmap=True,lazy_load_hdus=True) as hdus:
        h = hdus[1]
        return {"path":str(path),"size_bytes":Path(path).stat().st_size,
                "header_sha256":hashlib.sha256(h.header.tostring().encode()).hexdigest(),
                "keys":{k:h.header.get(k,"UNSPECIFIED") for k in
                        ("PIXTYPE","ORDERING","NSIDE","COORDSYS","POLCCONV","INDXSCHM","NAXIS1","NAXIS2")},
                "columns":[{"name":c.name,"format":c.format,"unit":c.unit} for c in h.columns],
                "payload_read":False}


def read_qu(path, *, expected_nside, expected_coords=None):
    from astropy.io import fits
    with fits.open(path,memmap=True) as hdus:
        h = hdus[1]
        if (h.header.get("PIXTYPE")!="HEALPIX" or h.header.get("ORDERING")!="RING"
                or h.header.get("NSIDE")!=expected_nside or h.header.get("POLCCONV")!="COSMO"):
            raise ValueError("explicit HEALPix RING/NSIDE/COSMO contract required")
        if expected_coords is not None and h.header.get("COORDSYS")!=expected_coords:
            raise ValueError("released coordinate frame differs from reader contract")
        columns=[]; units=[]
        for field in ("Q","U"):
            available = [name for name in (field+"_POLARISATION",field+"-POLARISATION") if name in h.columns.names]
            if len(available)!=1:
                raise ValueError("unambiguous named Q/U columns required")
            name=available[0]; unit=str(h.columns[name].unit)
            factors={"K":1e6,"K_CMB":1e6,"muK":1.,"muK_CMB":1.}
            if unit not in factors:
                raise ValueError("unsupported Q/U map unit "+unit)
            raw=np.array(h.data[name],dtype=float).reshape(-1)
            invalid=~np.isfinite(raw)|(np.abs(raw)>1e25)
            values=raw*factors[unit]
            columns.append((values,invalid));units.append(unit)
        if units[0]!=units[1] or len(columns[0][0])!=12*expected_nside**2 or len(columns[1][0])!=len(columns[0][0]):
            raise ValueError("aligned full-sky named Q/U units/pixels required")
        valid=~(columns[0][1]|columns[1][1])
        return columns[0][0],columns[1][0],valid,{
            "nside":expected_nside,"ordering":"RING","polarization_convention":"COSMO",
            "coordinate_frame":h.header.get("COORDSYS","UNSPECIFIED"),
            "native_unit":units[0],"scaled_unit":"micro"+units[0].removeprefix("mu"),
            "invalid_pixels":int((~valid).sum()),"invalid_policy":"excluded, not physical zero"}


def read_binary_mask(path, column, expected_nside):
    from astropy.io import fits
    with fits.open(path,memmap=True) as h:
        if h[1].header.get("NSIDE")!=expected_nside or h[1].header.get("ORDERING")!="RING":
            raise ValueError("mask geometry mismatch")
        mask=np.array(h[1].data[column]).reshape(-1)
    if mask.shape!=(12*expected_nside**2,) or not np.all(np.isin(mask,[0,1])):
        raise ValueError("binary 0-excluded/1-retained mask required")
    return mask==1


def qu_summary(q,u,mask):
    q,u=finite(q[mask]),finite(u[mask])
    if len(q)<2:
        raise ValueError("at least two retained polarization pixels required")
    p=np.hypot(q,u)
    return {"retained_pixels":len(q),"Q_mean":float(q.mean()),"U_mean":float(u.mean()),
            "Q_rms":float(np.sqrt(np.mean(q*q))),"U_rms":float(np.sqrt(np.mean(u*u))),
            "P_rms":float(np.sqrt(np.mean(p*p))),"P_quantiles":np.quantile(p,[.05,.5,.95]),
            "Q_U_sample_covariance":np.cov(np.vstack((q,u)),ddof=1)}


def spin_pseudo_spectra(q,u,mask,nside,lmax):
    import healpy as hp
    if not 2<=lmax<=min(16,3*nside-1):
        raise ValueError("bounded spin pilot requires 2<=lmax<=min(16,3*nside-1)")
    # Zeroing is explicitly the binary-mask operator, not a missing-data fill.
    ae,ab=hp.map2alm_spin([np.where(mask,q,0.),np.where(mask,u,0.)],spin=2,lmax=lmax)
    return {"ell":np.arange(lmax+1),"EE_pseudo_Cl":hp.alm2cl(ae),
            "BB_pseudo_Cl":hp.alm2cl(ab),"EB_pseudo_Cl":hp.alm2cl(ae,ab),
            "harmonic_convention":"healpy COSMO spin2; map2alm_spin; no transfer or mask deconvolution",
            "zeroing_scope":"binary-mask operator only", "nside":nside,"lmax":lmax}


def beyondplanck(root,lmax=16):
    base=root/"workdir/raw/beyondplanck_v2"
    path=base/"BP_CMB_QU_map_n8_v2.fits";maskpath=base/"BP_CMB_IQU_analysis_mask_n8_v2.fits"
    q,u,valid,meta=read_qu(path,expected_nside=8)
    qmask=read_binary_mask(maskpath,"Q_POLARISATION",8)
    umask=read_binary_mask(maskpath,"U_POLARISATION",8)
    keep=valid&qmask&umask
    stats=qu_summary(q,u,keep);pseudo=spin_pseudo_spectra(q,u,keep,8,lmax)
    return {"owner":"OBSSTAT","scope":"BEYONDPLANCK_V2_N8_NATIVE_PIXEL_QU_MASK_SPIN_PILOT",
            "metadata":meta,"mask_fraction":float(keep.mean()),"summary":stats,"pseudo_spectra":pseudo,
            "caveats":["Released posterior mean, not an independent observed sky or posterior-chain ensemble",
                       "COORDSYS missing in delivered headers; no sky-frame rotation or directional interpretation",
                       "Mask shares released native pixel indices/resolution; retain both Q/U masks",
                       "Masked pseudo spectra have E/B leakage and no beam/transfer/noise correction",
                       "No primordial BB inference, cosmological likelihood, or calibrated significance"]},[path,maskpath],[]


def class_splits(root):
    base=root/"workdir/raw/class_dr1"
    maps=[base/"class_dr1_40GHz_skymap_n128.fits",base/"class_dr1_40GHz_skymap_m1_n128.fits",
          base/"class_dr1_40GHz_skymap_m2_n128.fits"]
    decoded=[read_qu(p,expected_nside=128,expected_coords="C") for p in maps]
    if any(m[3]["native_unit"]!="K" for m in decoded):
        raise ValueError("CLASS released K convention changed")
    valid=np.logical_and.reduce([m[2] for m in decoded])
    q,u=decoded[0][:2];q1,u1=decoded[1][:2];q2,u2=decoded[2][:2]
    contrasts={"coadd":(q,u),"m1":(q1,u1),"m2":(q2,u2),
               "half_difference":((q1-q2)/2,(u1-u2)/2),
               "coadd_minus_half_sum":(q-(q1+q2)/2,u-(u1+u2)/2)}
    rows=[];masks=[base/"class_dr1_40GHz_dX_mask_n128.fits",base/"class_dr1_40GHz_sX_mask_n128.fits"]
    for maskpath,prefix in zip(masks,("d","s")):
        for index in (0,3):
            keep=valid&read_binary_mask(maskpath,prefix+str(index),128)
            summaries={name:qu_summary(a,b,keep) for name,(a,b) in contrasts.items()}
            rows.append({"mask":prefix+str(index),"mask_fraction":float(keep.mean()),"summaries":summaries})
    transfer=[base/"class_dr1_40GHz_VEB_transfer_matrix_lmax383_hits.hdf5",base/"class_dr1_40GHz_VEB_transfer_matrix_lmax383_uniform.hdf5"]
    return {"owner":"OBSSTAT","scope":"CLASS_DR1_NATIVE_UNIT_SPLIT_AND_COADD_CONTRASTS",
            "metadata":[m[3] for m in decoded],"mask_results":rows,
            "transfer_inputs":[{"path":str(p),"exists":p.exists(),"size_bytes":p.stat().st_size if p.exists() else None} for p in transfer],
            "transfer_status":"NOT_APPLIED","units":"microK in delivered native K convention",
            "caveats":["40GHz filtered frequency maps; not foreground-cleaned CMB",
                       "Header K converted by scale only; antenna versus thermodynamic convention not inferred",
                       "M1/M2 are approximately balanced base splits; half difference is a descriptive contrast, not a certified noise covariance",
                       "Coadd is compared with half sum, not assumed to equal it",
                       "QQ/QU/UU fields are hits in seconds, not Kelvin-squared noise covariance",
                       "No spin transform, HDF5 transfer inversion, noise ensemble, or calibrated significance",
                       "h5py unavailable in inspected environment; transfer decode remains separate"]},maps+masks,[]


def ffp10_headers(root):
    base=root/"workdir/raw/planck_ffp10/smica"
    files=[base/"cmb_mc/dx12_v3_smica_cmb_mc_00000_raw.fits",base/"noise_mc/dx12_v3_smica_noise_mc_00000_raw.fits"]
    headers=[fits_header(p) for p in files]
    return {"owner":"OBSSTAT","scope":"FFP10_EXPLICIT_QU_HEADER_INTAKE_ONLY",
            "headers":headers,"status":"HOLD_FRAME_POLCONV_PROCESSING_SOURCE_BRIDGE",
            "caveats":["Header-only evidence; pixel payload and full-file hash not read",
                       "Named Q/U, K_CMB units and RING NSIDE2048 observed",
                       "Missing frame/polarization convention stays UNSPECIFIED; filename cannot fill it",
                       "No transform, downsampling, polarization measurement, or null-law admission"]},[],[]


def json_value(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)


def source_record(path,root):
    path=Path(path);sha=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):sha.update(block)
    return {"path":str(path.relative_to(root)),"size_bytes":path.stat().st_size,"sha256":sha.hexdigest()}


def plot_result(result,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    scope=result["scope"]
    if "RESIDUAL_DESCRIPTIVES" in scope:
        fig,axes=plt.subplots(3,2,figsize=(10,9));axes=axes.ravel()
        for ax,row in zip(axes,result["records"]):
            ax.plot(row["ell"],row["signed_residual_over_error_toward_reference"],".",ms=2)
            ax.set_title(row["channel"]);ax.axhline(0,color="gray");ax.set_xlabel("ell")
            ax.set_ylabel("Signed residual / quoted marginal error")
        axes[-1].axis("off")
    elif "ACT_DR4" in scope or "SPT3G" in scope:
        fig,ax=plt.subplots(figsize=(10,5))
        for row in result["scenarios"]:
            name="yp2="+str(row["yp2"]) if "yp2" in row else "fractional beam scale="+str(row["fractional_beam_scale"])
            ax.plot(row["signed_residual_over_error_toward_reference"],label=name,lw=.8)
        ax.axhline(0,color="gray");ax.set_xlabel("Released retained row index");ax.set_ylabel("Residual / marginal conditional error");ax.legend()
    elif "BEYONDPLANCK" in scope:
        fig,ax=plt.subplots(figsize=(8,5));p=result["pseudo_spectra"]
        for key in ("EE_pseudo_Cl","BB_pseudo_Cl","EB_pseudo_Cl"):
            ax.plot(p["ell"][2:],p[key][2:],"o-",label=key)
        ax.set_xlabel("ell");ax.set_ylabel("Masked native-pixel pseudo Cl (microK squared)");ax.legend()
    elif "CLASS_DR1" in scope:
        fig,ax=plt.subplots(figsize=(9,5))
        for name in ("coadd","half_difference","coadd_minus_half_sum"):
            ax.plot(np.arange(len(result["mask_results"])),[r["summaries"][name]["P_rms"] for r in result["mask_results"]],"o-",label=name)
        ax.set_xticks(np.arange(len(result["mask_results"])),[r["mask"] for r in result["mask_results"]]);ax.set_ylabel("Native-unit QU magnitude RMS (microK)");ax.legend()
    else:
        fig,ax=plt.subplots(figsize=(8,4));ax.axis("off")
        ax.text(.05,.8,"FFP10 explicit QU header intake\nHOLD: frame / convention / processing bridge\nPixel payload not read; no measurement",va="top",fontsize=12)
    fig.suptitle(scope.replace("_"," ").lower(),fontsize=9);fig.tight_layout()
    for suffix in ("png","pdf"):fig.savefig(output/("diagnostic."+suffix),dpi=160)
    plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane",choices=("planck","act-dr4","spt3g","beyondplanck-n8","class-splits","ffp10-headers"))
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--spin-lmax",type=int,default=16)
    args=parser.parse_args(argv);root=args.repo_root.resolve();output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    receipt={"schema":"htt.reboot.spectra_polarization_execution.v1","command":sys.argv,
             "lane":args.lane,"root":str(root),"python":sys.version,"numpy":np.__version__,
             "platform":platform.platform(),"requested_author_runtime":"gpt-6-sol/high",
             "observed_author_runtime":"UNKNOWN","observed_executor_runtime":"UNKNOWN"}
    for key,cmd in (("git_head",["rev-parse","HEAD"]),("git_status",["status","--porcelain=v1"])):
        run=subprocess.run(["git","-C",str(root),*cmd],capture_output=True,text=True)
        receipt[key]=run.stdout.strip() if run.returncode==0 else "UNAVAILABLE"
    try:
        if args.lane=="beyondplanck-n8":result,files,members=beyondplanck(root,args.spin_lmax)
        else:
            result,files,members={"planck":planck,"act-dr4":act_dr4,"spt3g":spt3g,
               "class-splits":class_splits,"ffp10-headers":ffp10_headers}[args.lane](root)
        result.update({"claim_tier":"DIAGNOSTIC_ONLY","scientific_admission":"NOT_EVALUATED",
                       "transfer_source":"RELEASED_PROCESSING; NO_NATIVE_SOLVER",
                       "primary_source":ONLINE_SOURCES[args.lane],"source_access_date":"2026-10-14"})
        receipt["sources"]=[source_record(p,root) for p in files];receipt["archive_members"]=members
        receipt["code_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if args.lane=="ffp10-headers":receipt["header_only_sources"]=result["headers"]
        (output/"result.json").write_text(json.dumps(result,default=json_value,indent=2,allow_nan=False)+"\n")
        plot_result(result,output)
        report="# "+result["scope"].replace("_"," ").title()+"\n\n"
        report+="Owner: "+result["owner"]+". Diagnostic-only; scientific admission not evaluated.\n\n"
        report+="Source: [release documentation]("+ONLINE_SOURCES[args.lane]+"). Exact methods, arrays and limitations: `result.json`; source/code/runtime receipt: `execution_receipt.json`.\n\n"
        report+="\n".join("- "+c for c in result["caveats"])+"\n"
        (output/"report.md").write_text(report);receipt["exit_code"]=0
    except Exception as error:
        import traceback
        receipt["exit_code"]=1;receipt["error"]=type(error).__name__+": "+str(error)
        (output/"failure.log").write_text(traceback.format_exc())
    receipt["elapsed_seconds"]=time.monotonic()-started
    (output/"execution_receipt.json").write_text(json.dumps(receipt,default=json_value,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"lane":args.lane,"output":str(output),"exit_code":receipt["exit_code"],"elapsed_seconds":receipt["elapsed_seconds"]}))
    return receipt["exit_code"]


if __name__=="__main__":
    raise SystemExit(main())
