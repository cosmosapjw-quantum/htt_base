#!/usr/bin/env python3
"""Extract a frozen post-release T carrier from local Commander PR3/PR4 and MC.

No downloads. Native NESTED mask-first child averages, common PR3 intensity
mask, coverage >=.995, OLS with native-averaged monopole/dipole/STF quadrupole
columns and pixel-centre real harmonics at l>=3. Primary NSIDE64,lmax6;
predeclared controls NSIDE128,lmax6 and NSIDE64,lmax8. The complete rows remain
paired across controls. Upstream effective beam/DQ response is not deconvolved.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT/"htt", ROOT/"htt/src"):
    sys.path.insert(0, str(p))
import healpy as hp
import numpy as np
from astropy.io import fits
from htt.htt.infer import r66_radiation_quotient as rq

PUB = ROOT/"docs/research_program/observational_publication_20261015"
OUT = PUB/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS"
RAW = Path("/mnt/extdrive/workdir/raw/planck_data")
PR4ROOT = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual")
MASK = RAW/"COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
OBS = {
    "PR3": (RAW/"COM_CMB_IQU-commander_2048_R3.00_full.fits", "I_STOKES", 2048),
    "PR4": (PR4ROOT/"COM_CMB_IQU-commander_4096_R4.00_full.fits", "TEMPERATURE", 4096),
}
SPECS = ((64,6), (128,6), (64,8))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda:f.read(8<<20), b""):
            h.update(b)
    return h.hexdigest()


def plain(obj):
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, np.generic): return obj.item()
    if isinstance(obj, dict): return {k:plain(v) for k,v in obj.items()}
    if isinstance(obj, (tuple,list)): return [plain(v) for v in obj]
    return obj


def save_json(path, obj):
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(plain(obj), indent=2, allow_nan=False)+"\n")
    os.replace(temp, path)


def mask2048():
    with fits.open(MASK, memmap=True) as h:
        assert h[1].header["NSIDE"] == 2048
        assert h[1].header["ORDERING"].startswith("NEST")
        x = np.asarray(h[1].data["TMASK"]).reshape(-1)
        return x > .5


def native_moments(native, mask, out_nside=128):
    """Eight masked child averages: nx,ny,nz and five STF quadratics."""
    npix, factor = hp.nside2npix(out_nside), (native//out_nside)**2
    out, counts = np.empty((npix,8)), np.empty(npix)
    # All chunk boundaries are both native and 2048 parent boundaries.
    parents = 512
    for a in range(0,npix,parents):
        b = min(a+parents,npix)
        pix = np.arange(a*factor,b*factor)
        n = np.column_stack(hp.pix2vec(native,pix,nest=True))
        m = mask[pix//((native//2048)**2)]
        values = np.column_stack((n,np.einsum("ni,aij,nj->na",n,rq.STF5_BASIS,n)))
        counts[a:b] = m.reshape(-1,factor).sum(axis=1)
        total = (values*m[:,None]).reshape(b-a,factor,8).sum(axis=1)
        out[a:b] = total / np.maximum(counts[a:b,None],1)
    return out, counts


def downgrade_moments(m128,c128,nside):
    factor = (128//nside)**2
    count = c128.reshape(-1,factor).sum(axis=1)
    data = (m128*c128[:,None]).reshape(-1,factor,8).sum(axis=1)
    return data/np.maximum(count[:,None],1),count


def read_temperature(path, col, native, mask, unit):
    """Bounded memory mask-first native average; also return a fresh file hash."""
    file_hash = sha(path)
    with fits.open(path,memmap=True) as h:
        hdr = h[1].header
        if hdr["NSIDE"] != native or not hdr["ORDERING"].startswith("NEST"):
            raise ValueError("unexpected native pixel operator")
        if str(hdr.get("COORDSYS", "")).upper() not in ("GALACTIC","G"):
            raise ValueError("expected Galactic coordinates")
        unit_found = h[1].columns[col].unit
        if unit_found != unit:
            raise ValueError(f"expected {unit}, observed {unit_found}")
        raw = h[1].data[col]
        # MC table consists of contiguous 1024-pixel cells, not one row/pixel.
        values = np.asarray(raw).reshape(-1)
        if len(values) != hp.nside2npix(native): raise ValueError("wrong map length")
        factor = (native//128)**2
        out,count = np.empty(hp.nside2npix(128)),np.empty(hp.nside2npix(128))
        for a in range(0,len(out),512):
            b=min(a+512,len(out)); lo,hi=a*factor,b*factor
            m=mask[np.arange(lo,hi)//((native//2048)**2)]
            v=np.asarray(values[lo:hi],float)
            if not np.isfinite(v[m]).all() or np.any(abs(v[m]) > 1e10):
                raise ValueError("invalid released pixels on retained native support")
            v=np.where(m,v,0)
            count[a:b]=m.reshape(-1,factor).sum(axis=1)
            out[a:b]=v.reshape(-1,factor).sum(axis=1)/np.maximum(count[a:b],1)
    scale=1e6 if unit=="K_CMB" else 1.0
    return out*scale,count,{"path":str(path),"sha256":file_hash,"bytes":path.stat().st_size,
                           "fresh_hash":True,"native_nside":native,"unit":unit,
                           "conversion_to_uK":scale,"column":col}


def coarse_map(x128,count128,nside):
    f=(128//nside)**2
    count=count128.reshape(-1,f).sum(axis=1)
    return (x128*count128).reshape(-1,f).sum(axis=1)/np.maximum(count,1)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    start=time.monotonic(); mask=mask2048()
    record={"schema":"htt.r66.commander_extraction/1", "status":"RUNNING",
            "base":"3dd1893a3f74af8e1387c844e07897efeabdd0bf",
            "source_code_sha256":sha(Path(__file__)),
            "module_sha256":sha(ROOT/"htt/htt/htt/infer/r66_radiation_quotient.py"),
            "mask":{"path":str(MASK),"sha256":sha(MASK),"threshold":.5,"parent_coverage_min":.995},
            "primary":"n64_l6", "controls":["n128_l6","n64_l8"],
            "mc_ids_predeclared":list(range(300,400)),
            "source_qualification":"same post-release operator; upstream Commander beam/DQ/foreground matching unresolved",
            "observed":{},"simulations":[],"operators":{}}
    save_json(OUT/"EXTRACTION.json",record)
    operators={}; payload={}; counts_by_native={}
    for native in (2048,4096):
        moments,count=native_moments(native,mask)
        counts_by_native[native]=count
        for nside,lmax in SPECS:
            key=f"n{nside}_l{lmax}"; m,cn=downgrade_moments(moments,count,nside)
            keep=cn/((native//nside)**2)>=.995
            n=np.column_stack(hp.pix2vec(nside,np.arange(hp.nside2npix(nside)),nest=True))
            h,labels=rq.harmonic_design(n,lmax)
            h[:,1:9]=m
            e=rq.estimator(h,keep,labels)
            response=e.matrix[4:9]@h[keep,4:9]
            dq=e.matrix[4:9]@(h[keep,4:9]@rq.DQ_UK)
            lower_leak=e.matrix[4:9]@h[keep,:4]
            operators[native,key]=e
            record["operators"][f"{native}_{key}"]={"retained_pixels":int(keep.sum()),
                "f_sky":float(keep.mean()),"design_condition":e.condition,
                "native_averaged_quadrupole_response":response,
                "DQ_response_uK":dq,"DQ_identity_error_uK":np.max(abs(dq-rq.DQ_UK)),
                "monopole_dipole_max_leak":np.max(abs(lower_leak)),
                "l_ge_3_basis":"real Y_lm evaluated at parent pixel centres"}
            payload[f"mask_{native}_{key}"]=keep
            payload[f"labels_{key}"]=np.array(labels)
            print(f"operator {native} {key} pixels={keep.sum()} cond={e.condition:.3f}",flush=True)
        del moments
    for label,(path,col,native) in OBS.items():
        x,count,receipt=read_temperature(path,col,native,mask,"K_CMB")
        record["observed"][label]=receipt
        for nside,lmax in SPECS:
            key=f"n{nside}_l{lmax}"
            co=coarse_map(x,count,nside)
            payload[f"{label}_{key}"]=operators[native,key].extract(co)
        payload[f"{label}_coarse_n128_uK"]=x
        print(f"observed {label} elapsed={time.monotonic()-start:.1f}s",flush=True)
    rows={f"n{nside}_l{lmax}":[] for nside,lmax in SPECS}
    for i in range(300,400):
        path=PR4ROOT/f"cache/npipe6v20_commander_cmb_2048_mc_{i:04d}_005a.fits"
        inherited=json.loads(Path(str(path)+".verified.json").read_text())
        x,count,receipt=read_temperature(path,"I_STOKES",2048,mask,"uK_CMB")
        if receipt["sha256"] != inherited["sha256"]:
            raise ValueError(f"raw MC hash mismatch at {i}")
        receipt.update({"id":i,"public_url":inherited["item"]["url"],"matched_original_sha256":True})
        record["simulations"].append(receipt)
        for nside,lmax in SPECS:
            key=f"n{nside}_l{lmax}"
            rows[key].append(operators[2048,key].extract(coarse_map(x,count,nside)))
        if (i-299)%10==0 or i==302:
            record["elapsed_seconds"]=time.monotonic()-start
            record["completed_rows"]=len(record["simulations"])
            payload.update({f"MC_{key}":np.array(v) for key,v in rows.items()})
            payload["mc_ids"]=np.arange(300,i+1)
            np.savez_compressed(OUT/"commander_temperature_carrier.npz",**payload)
            save_json(OUT/"EXTRACTION.json",record)
            print(f"MC {i} rows={i-299} elapsed={time.monotonic()-start:.1f}s",flush=True)
    record["status"]="COMPLETE"
    record["carrier_sha256"]=sha(OUT/"commander_temperature_carrier.npz")
    record["elapsed_seconds"]=time.monotonic()-start
    save_json(OUT/"EXTRACTION.json",record)
    print(json.dumps({"status":record["status"],"rows":100,"elapsed_seconds":record["elapsed_seconds"],
                      "carrier_sha256":record["carrier_sha256"]}),flush=True)


if __name__=="__main__": run()
