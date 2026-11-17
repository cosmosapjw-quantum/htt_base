#!/usr/bin/env python3
"""R63 read-only CF4 published frame-correction chart check.

Run on the existing authorized device:
  python3 r63_cf4_q_check.py --root /home/cosmosapjw/Dropbox/bianchi/htt_base
The script prints JSON only and never writes a catalogue or output file.
No stochastic likelihood, covariance or independent observer inference is made.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

C = 299792.458
SELECTED = "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
EXPECTED_SELECTED = "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def stats(r):
    r = np.asarray(r, float)
    return {
        "N": int(r.size), "mean_km_s": float(np.mean(r)),
        "rms_km_s": float(np.sqrt(np.mean(r*r))),
        "std_km_s": float(np.std(r)),
        "abs_quantiles_km_s": dict(zip(
            ["p50","p90","p95","p99","p100"],
            map(float, np.quantile(abs(r), [.5,.9,.95,.99,1.])))),
        "fraction_abs_le_1_km_s": float(np.mean(abs(r) <= 1.0)),
    }

def direction(v):
    v = np.asarray(v, float)
    amp = float(np.linalg.norm(v))
    return {
        "xyz_icrs_km_s": list(map(float,v)),
        "amplitude_km_s": amp,
        "ra_deg": float(np.degrees(np.arctan2(v[1],v[0])) % 360),
        "dec_deg": float(np.degrees(np.arcsin(v[2]/amp))),
    }

def fit(n, y, intercept=False):
    design = np.column_stack([np.ones(len(n)),n]) if intercept else n
    coef, _, rank, sv = np.linalg.lstsq(design,y,rcond=None)
    resid = y-design@coef
    result = {
        "rank": int(rank), "singular_values": list(map(float,sv)),
        "condition": float(sv[0]/sv[-1]),
        "intercept_km_s": float(coef[0]) if intercept else 0.0,
        "vector": direction(coef[1:] if intercept else coef),
        "residual": stats(resid),
    }
    return result, coef, resid

def main(root):
    root = Path(root)
    pb = (root/SELECTED).read_bytes()
    if sha(pb) != EXPECTED_SELECTED:
        raise ValueError("selected carrier identity changed")
    with np.load(root/SELECTED,allow_pickle=False) as a:
        ids=a["group_id"].copy()
        z=a["z_CMB"].copy()
        n=a["n_J2000"].copy()
        mu=a["dmzp"].copy()
        emu=a["e_dmzp"].copy()
    table_path=root/"workdir/raw/cf4_full/table4.dat.gz"
    compressed=table_path.read_bytes()
    raw=gzip.decompress(compressed)
    rows={}
    for line in raw.splitlines():
        if not line.strip():
            continue
        gid=int(line[0:7])
        if gid in rows:
            raise ValueError("duplicate raw group")
        rows[gid]=line
    selected=[rows[int(gid)] for gid in ids]
    vh=np.array([float(s[27:32]) for s in selected])
    v3k=np.array([float(s[39:44]) for s in selected])
    raw_mu=np.array([float(s[8:14]) for s in selected])
    raw_emu=np.array([float(s[15:20]) for s in selected])
    ra=np.radians([float(s[83:91]) for s in selected])
    dec=np.radians([float(s[92:100]) for s in selected])
    raw_n=np.column_stack([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)])
    parity={
        "dmzp_maxabs":float(np.max(abs(mu-raw_mu))),
        "e_dmzp_maxabs":float(np.max(abs(emu-raw_emu))),
        "z_V3k_over_c_maxabs":float(np.max(abs(z-v3k/C))),
        "n_J2000_maxabs":float(np.max(abs(n-raw_n))),
    }
    if max(parity.values()) != 0.:
        raise ValueError("raw selected parity changed: "+str(parity))
    if not np.isfinite(n).all() or min(1+vh/C) <= 0:
        raise ValueError("invalid data")
    dv=v3k-vh
    # log1p avoids subtracting near-unity redshift ratios.
    q=C*np.log1p(dv/(C+vh))
    add, ca, ra0=fit(n,dv)
    mult, cm, rm=fit(n,q)
    mult_i, cmi, rmi=fit(n,q,intercept=True)
    dvpred=n@ca
    qpred_from_add=C*np.log1p(dvpred/(C+vh))
    # A fixed additive velocity map induces a depth-dependent log-redshift chart.
    out={
        "schema":"r63.cf4_published_q_chart_check.v1",
        "scope":"deterministic published source-correction diagnostic; no stochastic likelihood",
        "requested_model":"gpt-6.1-sol","requested_effort":"high",
        "observed_model":"UNKNOWN","observed_effort":"UNKNOWN",
        "root":str(root),
        "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        "source_identities":{
            "selected_relpath":SELECTED,"selected_sha256":sha(pb),
            "table4_gzip_sha256":sha(compressed),"table4_decompressed_sha256":sha(raw),
        },
        "N_selected":len(ids),"N_raw":len(rows),
        "parity":parity,
        "units":"km/s for dv,q and fitted coefficients; q/c is dimensionless logarithmic redshift correction",
        "definitions":{
            "dv":"published V3k - published Vh",
            "q":"c ln[(1+V3k/c)/(1+Vh/c)]",
            "additive_fit":"dv = n_sourceward.ICRS dot a; unweighted least squares",
            "multiplicative_fit":"q = n_sourceward.ICRS dot b; unweighted least squares",
            "multiplicative_intercept_fit":"q = b0 + n dot b; diagnostic chart intercept",
            "additive_predicted_q":"c ln[1+(n dot a)/(c+Vh)]",
        },
        "additive_fit":add,
        "multiplicative_fit":mult,
        "multiplicative_intercept_fit":mult_i,
        "q_minus_q_from_additive_fit":stats(q-qpred_from_add),
        "depth_bins":[],
        "rounding_comparison":{
            "conditional_assumption":"both tabulated velocities independently rounded to nearest integer km/s after their underlying definitions",
            "difference_absolute_bound_km_s":1.,
            "difference_rms_if_independent_uniform_rounding_km_s":float(np.sqrt(1/6)),
            "status":"diagnostic comparison only, not an established stochastic rounding law",
        },
        "limitations":[
            "A good deterministic fit does not establish the exact upstream frame-conversion algorithm.",
            "This does not infer an observer velocity independently of catalogue construction.",
            "The log-redshift chart is not automatically a Lorentz rapidity or a complete finite boost; direction conventions, transverse Doppler and aggregation matter.",
            "No distance/photometry deboost p is supplied by this diagnostic.",
            "Reported directions/amplitudes are deterministic fitted chart coefficients; no parameter covariance or uncertainty is estimated.",
        ],
    }
    edges=[.01,.02,.04,.06,.08,.100001]
    for lo,hi in zip(edges[:-1],edges[1:]):
        use=(z>=lo)&(z<hi)
        fa,_,_=fit(n[use],dv[use])
        fm,_,_=fit(n[use],q[use])
        out["depth_bins"].append({
            "z_low":lo,"z_high":hi,"N":int(use.sum()),
            "median_z_CMB":float(np.median(z[use])),
            "median_zHEL_Vh_over_c":float(np.median(vh[use]/C)),
            "additive_fit":fa,"multiplicative_fit":fm,
            "global_additive_residual":stats(ra0[use]),
            "global_multiplicative_residual":stats(rm[use]),
            "q_minus_q_from_global_additive_fit":stats((q-qpred_from_add)[use]),
        })
    return out

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    args=parser.parse_args()
    print(json.dumps(main(args.root),indent=2,allow_nan=False))
