#!/usr/bin/env python3
"""Retrospective exploratory SMICA low-ell power ranks in a delivered-simulation model.

300 unique signal/noise pairs, independent training60/calibration240, fixed
mask>0.5 and simultaneous ell0..5 OLS. No physical-null qualification is implied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from calibrate_reboot_statistics import calibrate, write_result, file_sha256

EXPECTED_CACHE_SHA256 = "86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
PAIR_COUNT, TRAIN_COUNT = 300, 60


def validate_cache_gate(gate):
    if gate.get("cache_hash") != "sha256:" + EXPECTED_CACHE_SHA256:
        raise ValueError("gate names a different cache identity")
    if gate.get("cache_reproducibility_green") is not True:
        raise ValueError("cache reproducibility gate is not green")


def validate_realization_ids(cmb_ids, noise_ids, count=PAIR_COUNT):
    """First `count` must be distinct within each simulation component; no recycle."""
    answer = []
    for values, name in ((cmb_ids,"cmb_ids"),(noise_ids,"noise_ids")):
        a = np.asarray(values)
        if a.ndim != 1 or len(a) < count:
            raise ValueError(f"{name}: need at least {count} one-dimensional IDs")
        ids = []
        for x in a[:count]:
            value = x.item() if isinstance(x,np.generic) else x
            if isinstance(value,float) and not np.isfinite(value):
                raise ValueError(f"{name}: invalid realization ID")
            text = str(value)
            if not text.strip() or text == "None":
                raise ValueError(f"{name}: invalid realization ID")
            ids.append(text)
        if len(set(ids)) != count:
            raise ValueError(f"{name}: duplicate component IDs; no noise/signal recycling")
        answer.append(ids)
    return answer


def build_ols_projector(design, mask):
    """Simultaneous full-column OLS via Cholesky, returning stable explicit operator.

    Supports generic pixel/column sizes for independent injection tests. Production
    code separately pins nside64 / 36 full columns and retains ell2..5 afterwards.
    """
    if np.iscomplexobj(design) or np.iscomplexobj(mask):
        raise ValueError("real design and mask required")
    design = np.asarray(design,dtype=float)
    mask = np.asarray(mask,dtype=float)
    if (design.ndim != 2 or mask.shape != (len(design),) or
        not np.isfinite(design).all() or not np.isfinite(mask).all()):
        raise ValueError("finite design and matching finite mask required")
    if np.any((mask<0)|(mask>1)):
        raise ValueError("mask must be in [0,1]")
    selected = mask > .5
    if np.count_nonzero(selected) < design.shape[1]:
        raise ValueError("insufficient masked pixels for simultaneous OLS")
    X = design[selected]
    gram = X.T @ X
    eigenvalues = np.linalg.eigvalsh(gram)
    if eigenvalues[0] <= 0 or eigenvalues[-1]/eigenvalues[0] > 1e12:
        raise ValueError("rank-deficient or numerically ill-conditioned OLS design")
    factor = cho_factor(gram,lower=True,check_finite=False)
    operator = cho_solve(factor,X.T,check_finite=False)
    residual = float(np.max(np.abs(operator @ X - np.eye(design.shape[1]))))
    if residual > 1e-8:
        raise ValueError("OLS projection failed identity residual check")
    return selected,operator,{"n_pixels":len(design),"selected_pixels":int(selected.sum()),
        "full_columns":design.shape[1],"gram_condition":float(eigenvalues[-1]/eigenvalues[0]),
        "design_condition":float(np.sqrt(eigenvalues[-1]/eigenvalues[0])),
        "operator_design_max_identity_residual":residual,
        "solver":"unweighted simultaneous OLS; Cholesky of full harmonic Gram"}


def fit_map_block(maps, selected, operator, count=PAIR_COUNT, chunk=8):
    """Project only selected initial rows, one small temporary block at a time."""
    if maps.ndim != 2 or len(maps)<count or maps.shape[1]!=len(selected):
        raise ValueError("map matrix has insufficient rows or incorrect pixel count")
    if not np.issubdtype(maps.dtype,np.number) or np.iscomplexobj(maps):
        raise ValueError("real numeric maps required")
    coeffs = np.empty((count,len(operator)))
    for i in range(0,count,chunk):
        block = np.asarray(maps[i:min(count,i+chunk)],dtype=float)
        if not np.isfinite(block[:,selected]).all():
            raise ValueError("nonfinite relevant map pixels")
        coeffs[i:min(count,i+chunk)] = block[:,selected] @ operator.T
    if not np.isfinite(coeffs).all():
        raise ValueError("nonfinite projected coefficients")
    return coeffs


def lowell_powers(retained):
    if np.iscomplexobj(retained):
        raise ValueError("orthonormal-real coefficients required")
    a = np.asarray(retained,dtype=float)
    if a.ndim not in (1,2) or a.shape[-1]!=32 or not np.isfinite(a).all():
        raise ValueError("finite retained ell2..5 orthonormal-real coefficients required")
    powers,offset = [],0
    for ell in (2,3,4,5):
        width = 2*ell+1
        powers.append(np.sum(a[...,offset:offset+width]**2,axis=-1)/width)
        offset += width
    p = np.stack(powers,axis=-1)
    if not np.isfinite(p).all():
        raise ValueError("power overflow")
    return p


def retained_labels():
    return [f"ell{ell}_m{m}_{kind}" for ell in range(2,6)
            for m in range(ell+1) for kind in (("real",) if m==0 else ("cos","sin"))]


def run(cache_path, gate_path, outdir):
    start = time.perf_counter()
    # Imports are lazy so generic OLS injection tests need no external Planck files.
    from obsstat.r7_cmb_product_response import pixel_fit_geometry
    from fit_cmb_smica_noise_modes import require_gated_cache
    if outdir.exists():
        raise ValueError("output directory already exists; use a fresh run directory")
    # Bind the cache digest named BY the gate, not the digest OF the gate document.
    gate = json.loads(gate_path.read_text())
    validate_cache_gate(gate)
    cache_identity = require_gated_cache(cache_path,gate)
    _,design = pixel_fit_geometry(nside=64)
    if design.shape!=(49152,36):
        raise ValueError("registered NSIDE64 simultaneous ell0..5 geometry required")
    with np.load(cache_path,allow_pickle=False) as data:
        required = {"cmb_maps","noise_maps","observed_map","common_mask","cmb_ids","noise_ids"}
        if not required.issubset(set(data.files)):
            raise ValueError("gated cache missing required map/identity arrays")
        cmb_ids,noise_ids = validate_realization_ids(data["cmb_ids"],data["noise_ids"])
        mask = data["common_mask"]
        selected,operator,fitmeta = build_ols_projector(design,mask)
        if fitmeta["selected_pixels"]!=38413:
            raise ValueError("pinned common-mask selected support is not 38413 pixels")
        observed_map = np.asarray(data["observed_map"],dtype=float)
        if observed_map.shape!=(49152,) or not np.isfinite(observed_map[selected]).all():
            raise ValueError("finite observed map of exact registered pixel size required")
        observed_retained = (operator @ observed_map[selected])[4:]
        # NPZ members cannot be memory-mapped: free the large signal member before
        # decompressing noise. Linearity gives fit(cmb+noise)=fit(cmb)+fit(noise).
        signal_maps = data["cmb_maps"]
        if len(signal_maps)!=999:
            raise ValueError("pinned cache needs all 999 delivered signal rows")
        signal_coefficients = fit_map_block(signal_maps,selected,operator)
        del signal_maps
        noise_maps = data["noise_maps"]
        if len(noise_maps)!=300:
            raise ValueError("pinned cache needs 300 delivered noise rows")
        noise_coefficients = fit_map_block(noise_maps,selected,operator)
        del noise_maps
    paired_retained = (signal_coefficients+noise_coefficients)[:,4:]
    observed = lowell_powers(observed_retained)
    paired = lowell_powers(paired_retained)
    pair_ids = ["pair:"+json.dumps({"cmb":c,"noise":n},sort_keys=True) for c,n in zip(cmb_ids,noise_ids)]
    pipeline = "gated-K1-NSIDE64-maskGT0.5-OLS-ell0to5-retain2to5-microK-v1"
    meta = {"analysis_label":"EXPLORATORY retrospective SMICA delivered-simulation ranks; NOT physical Planck p",
        "declaration_id":"smica-reboot-fixed-four-powers-train60-cal240-v1",
        "null_model_id":"delivered fixed-weight FFP10 SMICA signal plus separately delivered independent noise; exchangeability conditional assumption",
        "fixed_B":240,"fixed_budget_before_scores":True,"statistics_predeclared":True,
        "predeclaration_scope":"features/mask/tails/split fixed before this pilot's numerical scores; retrospective project-level selection, nonconfirmatory",
        "joint_row_generation":True,"observed_exchangeable_under_null":True,
        "exchangeability_status":"ASSUMED_CONDITIONALLY_NOT_ESTABLISHED_FOR_PHYSICAL_SKY",
        "null_draw_law":"iid_joint_vectors","independence_unit":"latent_sky_realization",
        "observed_realization_id":"actual-Planck-PR3-SMICA-sky",
        "null_realization_ids":pair_ids[TRAIN_COUNT:],"training_realization_ids":pair_ids[:TRAIN_COUNT],
        "observation_pipeline":pipeline,"null_pipeline":pipeline,"training_pipeline":pipeline,
        "transformation":"independent_training_z","training_independent_of_observed_and_calibration":True,
        "simulation_independence_status":"conditional on delivered independent simulation model; unique IDs alone do not establish independence",
        "statistics":[{"name":f"C_{ell}_microK2","tail":"two-sided"} for ell in (2,3,4,5)]}
    result = calibrate(observed,paired[TRAIN_COUNT:],meta,paired[:TRAIN_COUNT])
    result["scientific_admission"]={"status":"EXPLORATORY_RETROSPECTIVE_CONDITIONAL_SIMULATION_MODEL_ONLY",
        "rank_is_confirmatory_physical_planck_p":False,"new_bianchi_detection":False,
        "unverified_model_adequacy":["observed versus simulated residual foreground mean","residual systematic components",
            "fixed actual-data component-separation weights","full physical null law and observed/simulation exchangeability"],
        "source_regime":"Planck IV section3.5 separately propagated independent CMB/noise with fixed actual-data weights; official plancklens combines delivered cmb+noise",
        "selection":"Retrospective historical project question; no pilot mask/feature optimization. Conditional ranks do not remove historical selection."}
    result["interpretation"]["rank"]="Exploratory delivered-simulation rank under assumed observed/paired-null exchangeability, conditional on independent training and fixed current feature family. Retrospective selection prevents confirmatory physical Planck p interpretation."
    result["fit"] = fitmeta
    result["units"]={"input_maps":"microK","retained_coefficients":"microK","power_features":"microK^2"}
    outdir.mkdir(parents=True,exist_ok=True)
    write_result(result,observed,paired[TRAIN_COUNT:],paired[:TRAIN_COUNT],outdir)
    np.savez(outdir/"pilot_features_coefficients.npz",observed=observed,training=paired[:TRAIN_COUNT],
        null=paired[TRAIN_COUNT:],observed_retained_coefficients=observed_retained,
        paired_retained_coefficients=paired_retained,retained_labels=np.array(retained_labels()),
        cmb_ids=np.array(cmb_ids),noise_ids=np.array(noise_ids))
    (outdir/"declaration.json").write_text(json.dumps(meta,indent=2)+"\n")
    report = outdir/"calibration.md"
    report.write_text(report.read_text()+"\nScientific admission: EXPLORATORY retrospective conditional delivered-simulation model only.\n\n"+
        "Residual foreground mean, residual systematics, fixed actual-data weights and the full physical null are unverified. Unique simulation IDs do not establish their law.\n\n"+
        "Input microK; fitted retained coefficients microK; powers microK^2. Full ell0..5 OLS fits nuisance monopole/dipole simultaneously before retaining ell2..5; no physical dipole/global-tilt/shear estimate.\n")
    receipt={"status":"ACTUAL_GATED_CACHE_EXECUTED","exit_code":0,"command":sys.argv,
        "elapsed_seconds":time.perf_counter()-start,"peak_rss_kib_linux":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "cache_path":str(cache_path),"cache_sha256":cache_identity,"gate_path":str(gate_path),"gate_sha256":file_sha256(gate_path),
        "script_sha256":file_sha256(__file__),"calibrator_sha256":file_sha256(Path(__file__).with_name("calibrate_reboot_statistics.py")),
        "pairing":"first300 unique signal and noise IDs, used once each; train first60, calibration remaining240",
        "conditional_model_only":True,"requested_model":"INHERITED_PARENT","observed_model":"UNKNOWN",
        "requested_reasoning_effort":"INHERITED_PARENT","observed_reasoning_effort":"UNKNOWN"}
    (outdir/"execution_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--gate",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    a=parser.parse_args(argv)
    try:
        result=run(a.cache,a.gate,a.output_dir)
        print(json.dumps({"status":"EXPLORATORY_CONDITIONAL_ONLY","global_rank":result["global_joint_null"]["p_rank"],
                          "floor":result["p_rank_resolution"],"output_dir":str(a.output_dir)}))
    except (ValueError,OSError,KeyError) as exc:
        parser.exit(2,f"pilot error: {exc}\n")


if __name__=="__main__":
    main()
