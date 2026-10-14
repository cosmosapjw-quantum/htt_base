#!/usr/bin/env python3
"""Exact-source Planck PR3 nine-bin lensing amplitude diagnostic.

Contracts the released native windows against one fixed CAMB reference. The
scalar amplitude is reconstruction-phi-phi only, with no cosmology or A_L fit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.special import ndtr, ndtri
from scipy.stats import norm

DATA_REL=Path("workdir/cobaya_packages/data/planck_supp_data_and_covmats/lensing/2018")
THEORY_REL=Path("workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz")
STEM="smicadx12_Dec5_ftl_mv2_ndclpp_p_teb_consext8"
MARG=STEM+"_CMBmarged.dataset"
BASE=STEM+".dataset"


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def parse_config(path, *, parent=None):
    text=Path(path).read_text()
    settings=dict(parent or {})
    for line in text.splitlines():
        line=line.split("#",1)[0].strip()
        if not line or line.startswith("DEFAULT("):
            continue
        if "=" not in line:
            raise ValueError("unrecognized Planck dataset line")
        k,v=line.split("=",1)
        settings[k.strip()]=v.strip()
    return settings


def finite(value,name):
    a=np.asarray(value)
    if np.iscomplexobj(a) or not np.isfinite(a).all():
        raise ValueError("finite real "+name+" required")
    return np.asarray(a,float)


def covariance9(value):
    c=finite(value,"covariance")
    if c.shape!=(9,9):
        raise ValueError("nine-bin covariance required")
    asym=float(np.linalg.norm(c-c.T,ord="fro")/np.linalg.norm(c,ord="fro"))
    if not np.isfinite(asym) or asym>1e-12:
        raise ValueError("Planck covariance antisymmetry exceeds 1e-12")
    sym=(c+c.T)/2
    cho_factor(sym,lower=True,check_finite=True)  # no jitter, floor, or diagonalization
    return sym,asym


def read_window(path,columns):
    raw=finite(np.loadtxt(path),"window")
    if raw.ndim!=2 or raw.shape[1]!=len(columns)+1:
        raise ValueError("native window column/order shape mismatch: "+str(path))
    ell=raw[:,0]
    if not np.array_equal(ell,ell.astype(int)) or not np.all(np.diff(ell)>0):
        raise ValueError("window ell must be strict integers")
    ell=ell.astype(int)
    if ell[0]<0 or ell[-1]>2500:
        raise ValueError("window ell exceeds released 0..2500 support")
    keep=(ell>=2)&(ell<=2500)
    values=raw[:,1:]
    receipt={"path":str(path),"rows":len(raw),"ell_min":int(ell[0]),
             "ell_max":int(ell[-1]),"outside_native_support_nonzero":int(np.count_nonzero(values[~keep])),
             "outside_native_support_abs_weight":float(np.abs(values[~keep]).sum()),
             "columns":columns}
    return (ell[keep],values[keep]),receipt


def read_bandpowers(path):
    header=next((line for line in Path(path).read_text().splitlines() if line.lstrip().startswith("# bin ")),None)
    if header is None or header.lstrip("# ").split()!=["bin","L_min","L_max","L_av","PP","Error","Ahat"]:
        raise ValueError("released PP column/header identity mismatch")
    return finite(np.loadtxt(path),"bandpowers")


def window_product(windows,order,spectra):
    result=np.zeros(len(windows))
    for b,(ell,weights) in enumerate(windows):
        result[b]=sum(float(weights[:,j]@spectra[name][ell]) for j,name in enumerate(order))
    return result


def read_variant(base,filename,*,marginal):
    path=base/filename
    if marginal:
        first=next(line.strip() for line in path.read_text().splitlines() if line.strip())
        if first!="DEFAULT("+BASE+")":
            raise ValueError("CMB-marginalized parent dataset identity mismatch")
        cfg=parse_config(path,parent=parse_config(base/BASE))
        files=[base/BASE,path]
    else:
        cfg=parse_config(path)
        files=[path]
    if (cfg.get("like_approx")!="gaussian" or cfg.get("binned")!="T" or
            cfg.get("nbins")!="9" or cfg.get("use_min")!="1" or cfg.get("use_max")!="9" or
            cfg.get("cl_lmin")!="2" or cfg.get("cl_lmax")!="2500" or
            cfg.get("covmat_cl")!="PP" or cfg.get("bin_window_in_order")!="PP" or
            cfg.get("bin_window_out_order")!="PP"):
        raise ValueError("Planck 2018 Gaussian nine-bin PP source contract mismatch")
    if cfg.get("fields_required") != ("P" if marginal else "T E P"):
        raise ValueError("CMB-marginalized/nonmarginal field contract mismatch")
    correction_order=cfg["linear_correction_bin_window_in_order"].split()
    expected=["PP"] if marginal else ["TT","EE","TE","PP"]
    if (correction_order!=expected or
            cfg["linear_correction_bin_window_out_order"].split()!=["PP"]*len(expected)):
        raise ValueError("Planck linear correction field/order mismatch")
    if (cfg.get("calibration_param") != ("" if marginal else "planck_calib.paramnames")):
        raise ValueError("A_planck source variant mismatch")
    bandpath=base/cfg["cl_hat_file"]
    band=read_bandpowers(bandpath)
    if (band.shape!=(9,7) or not np.array_equal(band[:,0],np.arange(1,10)) or
            not np.array_equal(band[:,1],np.array([8,41,85,130,175,220,265,310,355])) or
            not np.array_equal(band[:,2],np.array([40,84,129,174,219,264,309,354,400]))):
        raise ValueError("exact nine released bin/header coordinates required")
    y=band[:,4].copy()  # PP, never Error (column 5) or Ahat (column 6)
    files.append(bandpath)
    covpath=base/cfg["covmat_fiducial"]
    cov,asym=covariance9(np.loadtxt(covpath));files.append(covpath)
    fpath=base/cfg["linear_correction_fiducial_file"]
    f=finite(np.loadtxt(fpath),"fiducial correction")
    if f.shape!=(9,2) or not np.array_equal(f[:,0],np.arange(1,10)):
        raise ValueError("exact nine-bin fiducial correction required")
    files.append(fpath)
    ordinary=[];response=[];audits=[]
    for b in range(1,10):
        path=base/cfg["bin_window_files"].replace("%u",str(b))
        window,audit=read_window(path,["PP"])
        ordinary.append(window);audits.append({"family":"ordinary",**audit});files.append(path)
        path=base/cfg["linear_correction_bin_window_files"].replace("%u",str(b))
        window,audit=read_window(path,correction_order)
        response.append(window);audits.append({"family":"linear_correction",**audit});files.append(path)
    return {"config":cfg,"data":y,"bin_info":band[:,:4],"cov":cov,"cov_asymmetry":asym,
            "fiducial_correction":f[:,1],"ordinary":ordinary,"response":response,
            "response_order":correction_order,"window_audit":audits,"files":files,
            "variant":"CMB_MARGINALIZED" if marginal else "NONMARGINAL_FIXED_CMB"}


def load_reference(path):
    with np.load(path,allow_pickle=False) as z:
        ell_pp=z["ell_pp"];ell_cmb=z["ell_cmb"]
        pp=finite(z["lens_potential_cls"],"lensing reference")
        if (not np.array_equal(ell_pp,np.arange(len(ell_pp))) or
                not np.array_equal(ell_cmb,np.arange(len(ell_cmb))) or
                pp.ndim!=2 or pp.shape[1]!=3 or len(pp)<2501 or len(ell_cmb)<2501):
            raise ValueError("explicit ell-zero CAMB reference indexing mismatch")
        spectra={"PP":pp[:,0],"TT":finite(z["Dl_TT"],"TT reference"),
                 "EE":finite(z["Dl_EE"],"EE reference"),
                 "TE":finite(z["Dl_TE"],"TE reference")}
    return spectra


def affine_terms(variant,spectra):
    p=spectra["PP"]
    ordinary=window_product(variant["ordinary"],["PP"],{"PP":p})
    response_pp=window_product(variant["response"],["PP"],{"PP":p}) if variant["variant"]=="CMB_MARGINALIZED" else None
    if response_pp is None:
        response_pp=window_product([(ell,weights[:,[3]]) for ell,weights in variant["response"]],["PP"],{"PP":p})
    a=ordinary+response_pp
    c=-variant["fiducial_correction"].copy()
    if variant["variant"]=="NONMARGINAL_FIXED_CMB":
        for j,name in enumerate(("TT","EE","TE")):
            windows=[(ell,weights[:,[j]]) for ell,weights in variant["response"]]
            c+=window_product(windows,[name],{name:spectra[name]})
    return a,c,{"ordinary_PP":ordinary,"linear_correction_PP":response_pp}


def affine_fit(y,a,c,cov):
    y,a,c=[finite(v,name) for v,name in ((y,"data"),(a,"response"),(c,"fixed offset"))]
    if y.shape!=a.shape or y.shape!=c.shape or y.ndim!=1 or len(y)!=9:
        raise ValueError("nine aligned affine bins required")
    cov,asym=covariance9(cov)
    factor=cho_factor(cov,lower=True)
    solve=lambda v:cho_solve(factor,v)
    information=float(a@solve(a))
    if information<=0:
        raise ValueError("fixed-reference amplitude unidentified")
    ahat=float(a@solve(y-c)/information)
    residual=y-c-ahat*a
    return {"amplitude":ahat,"conditional_se":float(1/np.sqrt(information)),
            "information":information,"optimized_chi_square_descriptor":float(residual@solve(residual)),
            "reference_A1_chi_square_descriptor":float((y-c-a)@solve(y-c-a)),
            "residual":residual,"covariance_antisymmetry":asym}


def bounded_posterior(ahat,sigma):
    low,high=(0-ahat)/sigma,(2-ahat)/sigma
    mass=float(ndtr(high)-ndtr(low))
    if mass<=0 or not np.isfinite(mass):
        raise FloatingPointError("proper Uniform[0,2] posterior mass unresolved")
    shift=(norm.pdf(low)-norm.pdf(high))/mass
    mean=ahat+sigma*shift
    variance=sigma*sigma*(1+(low*norm.pdf(low)-high*norm.pdf(high))/mass-shift*shift)
    if variance<0:
        raise FloatingPointError("proper amplitude posterior variance unresolved")
    return {"prior":"scenario Uniform[0,2] on scalar PP reference amplitude, not release prior",
            "normalizing_gaussian_mass":mass,"mean":float(mean),"variance":float(variance),
            "quantiles":{str(q):float(ahat+sigma*ndtri(ndtr(low)+q*mass)) for q in (.025,.5,.975)}}


def native_parity(root,variant,spectra,a,c,amplitudes=(.8,1.0,1.2)):
    from cobaya.likelihoods.planck_2018_lensing import CMBMarged,native
    cls=CMBMarged if variant["variant"]=="CMB_MARGINALIZED" else native
    packages=(root/"workdir/cobaya_packages").resolve()
    obj=cls({"path":str(packages/"data/planck_supp_data_and_covmats")},
            packages_path=str(packages),name="planck_pr3_lensing_parity")
    if obj.nbins_used!=9 or obj.pcl_lmin!=2 or obj.pcl_lmax!=2500:
        raise ValueError("native source selection mismatch")
    cov,f=variant["cov"],variant["fiducial_correction"]
    rows=[]
    for A in amplitudes:
        dls={"pp":A*spectra["PP"],"tt":spectra["TT"],
             "ee":spectra["EE"],"te":spectra["TE"]}
        obj.get_theory_map_cls(dls,{"A_planck":1.0})
        native_model=obj.get_binned_map_cls(obj.map_cls)[:,0]
        own=A*a+c
        delta=native_model-own
        whitened=float(np.sqrt(delta@cho_solve(cho_factor(cov,lower=True),delta)))
        chi=float((variant["data"]-own)@cho_solve(cho_factor(cov,lower=True),variant["data"]-own))
        native_chi=-2*float(obj.log_likelihood(dls,A_planck=1.0))
        if whitened>1e-9 or abs(native_chi-chi)>1e-8*(1+abs(chi)):
            raise AssertionError("native Planck 2018 bin/model/chi-square parity failed")
        rows.append({"A":A,"whitened_model_difference":whitened,
                     "chi_square_own":chi,"chi_square_native":native_chi,
                     "absolute_chi_square_difference":abs(chi-native_chi)})
    return {"kernel":"cobaya.likelihoods.planck_2018_lensing native CMBlikes",
            "cobaya_version":importlib.metadata.version("cobaya"),"fixed_A_planck":1.0,
            "model_whitened_tolerance":1e-9,"chi_square_tolerance":"1e-8*(1+abs(chi2))",
            "rows":rows}


def source_bound_saved_result(root,result_path):
    """Verify the saved result and its immutable source bindings without refitting."""
    path=Path(result_path).resolve()
    result=json.loads(path.read_text())
    if (result.get("scope")!="PLANCK_PR3_RELEASED_NINE_BIN_RECONSTRUCTION_PP_AMPLITUDE" or
            result.get("primary_variant")!="CMB_MARGINALIZED" or
            [v.get("variant") for v in result.get("variants",[])]!=
            ["CMB_MARGINALIZED","NONMARGINAL_FIXED_CMB"]):
        raise ValueError("saved Planck PR3 result scope/variant identity mismatch")
    sources=result.get("source_files",[])
    if len(sources)<30 or len({entry["path"] for entry in sources})!=len(sources):
        raise ValueError("saved Planck PR3 source receipt incomplete")
    required={str(THEORY_REL),str(DATA_REL/MARG),str(DATA_REL/BASE)}
    if not required.issubset({entry["path"] for entry in sources}):
        raise ValueError("saved Planck PR3 required source identity missing")
    for entry in sources:
        source=Path(entry["path"])
        source=source if source.is_absolute() else root/source
        if source.stat().st_size!=entry["size_bytes"] or sha256(source)!=entry["sha256"]:
            raise ValueError("saved Planck PR3 source identity mismatch: "+entry["path"])
    execution=path.parent/"execution_receipt.json"
    receipt=json.loads(execution.read_text())
    if receipt.get("exit_code")!=0 or not receipt.get("code_sha256"):
        raise ValueError("original Planck PR3 execution receipt is not successful")
    return result,{"result_path":str(path),"result_sha256":sha256(path),
                   "original_execution_receipt_path":str(execution),
                   "original_execution_receipt_sha256":sha256(execution),
                   "original_code_sha256":receipt["code_sha256"],
                   "verified_source_count":len(sources),"source_sha256":sources}


def saved_quadratic_profile(row,amplitudes):
    """Full covariance Q(A) from saved y,a,c,C; saved Ahat is never refitted."""
    y=finite(row["y_PP_dimensionless"],"saved PP")
    a=finite(row["a_PP_amplitude_response_dimensionless"],"saved response")
    c=finite(row["c_fixed_offset_dimensionless"],"saved fixed offset")
    cov,_=covariance9(row["covariance_dimensionless_squared"])
    if y.shape!=a.shape or y.shape!=c.shape or y.shape!=(9,):
        raise ValueError("saved nine-bin vectors mismatch")
    amplitudes=finite(amplitudes,"profile amplitudes")
    if amplitudes.ndim!=1:
        raise ValueError("profile grid must be one dimensional")
    solve=cho_factor(cov,lower=True)
    residual=y[None,:]-amplitudes[:,None]*a[None,:]-c[None,:]
    q=np.einsum("ij,ij->i",residual,cho_solve(solve,residual.T).T)
    return q


def closeout_saved(root,result_path):
    saved,binding=source_bound_saved_result(root,result_path)
    base=root/DATA_REL
    spectra=load_reference(root/THEORY_REL)
    checks=[]
    for row,filename,marginal in zip(saved["variants"],(MARG,BASE),(True,False)):
        variant=read_variant(base,filename,marginal=marginal)
        a,c,_=affine_terms(variant,spectra)
        stored_a=finite(row["a_PP_amplitude_response_dimensionless"],"saved response")
        stored_c=finite(row["c_fixed_offset_dimensionless"],"saved offset")
        stored_y=finite(row["y_PP_dimensionless"],"saved data")
        stored_cov,_=covariance9(row["covariance_dimensionless_squared"])
        if (not np.allclose(stored_a,a,rtol=1e-12,atol=1e-20) or
                not np.allclose(stored_c,c,rtol=1e-12,atol=1e-20) or
                not np.array_equal(stored_y,variant["data"]) or
                not np.array_equal(stored_cov,variant["cov"])):
            raise ValueError("saved nine-bin result differs from exact source contraction")
        A=float(row["fit"]["amplitude"])
        if not np.isfinite(A) or not 0<=A<=2:
            raise ValueError("saved amplitude is outside declared closeout support")
        factor=cho_factor(stored_cov,lower=True)
        residual=stored_y-A*stored_a-stored_c
        score=float(stored_a@cho_solve(factor,residual))
        information=float(stored_a@cho_solve(factor,stored_a))
        q_peak=float(residual@cho_solve(factor,residual))
        if (abs(score)>1e-8*(1+information) or
                abs(1/np.sqrt(information)-row["fit"]["conditional_se"])>1e-10 or
                abs(q_peak-row["fit"]["optimized_chi_square_descriptor"])>1e-8*(1+q_peak)):
            raise ValueError("saved fitted amplitude/curvature/quadratic identity mismatch")
        parity=native_parity(root,variant,spectra,stored_a,stored_c,amplitudes=(A,))
        check={"variant":row["variant"],"saved_amplitude":A,
               "saved_fit_reused_without_refit":True,"saved_score":score,
               "saved_full_covariance_curvature":information,
               "saved_peak_chi_square":q_peak,"native_peak_call":parity["rows"][0],
               "native_kernel":parity["kernel"],"fixed_A_planck":1.0}
        checks.append(check)
    return saved,{"status":"PEAK_PARITY_AND_SAVED_RESULT_RENDER_CLOSEOUT",
                  "first_gap":"original execution checked only A=0.8,1,1.2; saved fitted A was not checked",
                  "original_result_preserved":True,"binding":binding,"peak_checks":checks,
                  "claim_tier":"CONDITIONAL_DIAGNOSTIC","scientific_admission":"NOT_EVALUATED"}


def plot_closeout(saved,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(14,8))
    for i,row in enumerate(saved["variants"]):
        bins=finite(row["ell_bins"],"saved bin geometry")
        if bins.shape!=(9,4):
            raise ValueError("saved bin geometry missing L_av and source edges")
        x=bins[:,3];xerr=np.vstack((x-bins[:,1],bins[:,2]-x))
        y=finite(row["y_PP_dimensionless"],"saved PP")
        a=finite(row["a_PP_amplitude_response_dimensionless"],"saved response")
        c=finite(row["c_fixed_offset_dimensionless"],"saved offset")
        cov,_=covariance9(row["covariance_dimensionless_squared"])
        sigma=np.sqrt(np.diag(cov))
        ahat=float(row["fit"]["amplitude"])
        pred1=a+c;predhat=ahat*a+c
        ax=axes[i,0]
        ax.errorbar(x,y,xerr=xerr,yerr=sigma,fmt="ko",label="observed PP; source bins")
        ax.plot(x,pred1,"--",label="corrected A=1 prediction")
        ax.plot(x,predhat,"-",label="corrected saved Ahat prediction")
        ax.set(xlabel="Source L_av and L_min/L_max edges",ylabel="PP bandpower (dimensionless)",title=row["variant"])
        ax.legend(fontsize=7)
        grid=np.linspace(max(0,ahat-4*row["fit"]["conditional_se"]),
                         min(2,ahat+4*row["fit"]["conditional_se"]),161)
        profile=saved_quadratic_profile(row,grid)
        axes[i,1].plot(grid,profile)
        axes[i,1].axvline(ahat,color="tab:orange",ls="--",label="saved Ahat")
        axes[i,1].axvline(1,color="gray",ls=":",label="A=1")
        axes[i,1].set(xlabel="Reconstruction PP reference amplitude A",ylabel="Full-covariance chi-square descriptor")
        axes[i,1].legend(fontsize=7)
        standardized=(y-predhat)/sigma
        axes[i,2].axhline(0,color="gray",lw=.7)
        axes[i,2].plot(x,standardized,"o-")
        axes[i,2].set(xlabel="Source L_av",ylabel="Residual / marginal sigma",title="Correlated residuals; no independent-bin PTE")
    fig.suptitle("Planck PR3 saved-result fitted-peak closeout")
    fig.tight_layout()
    for suffix in ("png","pdf"):
        fig.savefig(output/("peak_closeout."+suffix),dpi=150)
    plt.close(fig)


def run_closeout(root,output,result_path):
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    repair={"task":"PLANCK_PR3_EXACT_NATIVE_NINE_BIN_PP_PEAK_CLOSEOUT",
            "command":sys.argv,"repo_root":str(root),"requested_author_runtime":"gpt-6-sol/high",
            "observed_author_runtime":"UNKNOWN","python":sys.version,"numpy":np.__version__}
    try:
        saved,closeout=closeout_saved(root,result_path)
        plot_closeout(saved,output)
        (output/"closeout.json").write_text(json.dumps(closeout,indent=2,allow_nan=False)+"\n")
        (output/"report.md").write_text(
            "# Planck PR3 saved-result peak closeout\n\n"
            "The original execution checked A=0.8, 1, and 1.2; it did not check the fitted peaks. "
            "This closeout checked native Cobaya at each saved Ahat, verified source hashes, and rendered "
            "the saved full-covariance profile without refitting. Original result and receipt are preserved.\n\n"
            "Residual/sigma panels have correlated bins. No calibrated PTE, cosmology posterior, evidence, "
            "or independent primary-CMB/ACT multiplication follows.\n")
        repair["exit_code"]=0
        repair["original_result_sha256"]=closeout["binding"]["result_sha256"]
        repair["original_execution_receipt_sha256"]=closeout["binding"]["original_execution_receipt_sha256"]
        repair["verified_source_count"]=closeout["binding"]["verified_source_count"]
        repair["verified_source_list_sha256"]=hashlib.sha256(
            json.dumps(closeout["binding"]["source_sha256"],sort_keys=True).encode()).hexdigest()
        repair["peak_calls"]=closeout["peak_checks"]
        repair["closeout_sha256"]=sha256(output/"closeout.json")
    except Exception as error:
        repair["exit_code"]=1
        repair["error"]=type(error).__name__+": "+str(error)
        (output/"failure.log").write_text(traceback.format_exc())
    repair["elapsed_seconds"]=time.monotonic()-started
    repair["final_code_sha256"]=sha256(Path(__file__))
    (output/"repair_receipt.json").write_text(json.dumps(repair,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"closeout_exit_code":repair["exit_code"],"output":str(output)}))
    return repair["exit_code"]


def evaluate(root):
    base=root/DATA_REL
    reference_path=root/THEORY_REL
    spectra=load_reference(reference_path)
    variants=[read_variant(base,MARG,marginal=True),read_variant(base,BASE,marginal=False)]
    outputs=[]
    for variant in variants:
        a,c,pieces=affine_terms(variant,spectra)
        fit=affine_fit(variant["data"],a,c,variant["cov"])
        parity=native_parity(root,variant,spectra,a,c)
        posterior=bounded_posterior(fit["amplitude"],fit["conditional_se"])
        predictive={"mean":posterior["mean"]*a+c,
                    "covariance":variant["cov"]+posterior["variance"]*np.outer(a,a),
                    "status":"ANALYTIC_CONDITIONAL_GAUSSIAN_PROXY_MOMENTS_NO_NULL_PTE"}
        outputs.append({"variant":variant["variant"],"y_PP_dimensionless":variant["data"].tolist(),
                        "ell_bins":variant["bin_info"].tolist(),
                        "a_PP_amplitude_response_dimensionless":a.tolist(),
                        "c_fixed_offset_dimensionless":c.tolist(),
                        "ordinary_PP_dimensionless":pieces["ordinary_PP"].tolist(),
                        "linear_correction_PP_dimensionless":pieces["linear_correction_PP"].tolist(),
                        "fixed_fiducial_correction_dimensionless":variant["fiducial_correction"].tolist(),
                        "covariance_dimensionless_squared":variant["cov"].tolist(),
                        "window_audit":variant["window_audit"],
                        "covariance_antisymmetry_relative_frobenius":variant["cov_asymmetry"],
                        "fit":{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in fit.items()},
                        "proper_scalar_amplitude_posterior":posterior,
                        "posterior_predictive_conditional_covariance":{
                            "mean":predictive["mean"].tolist(),
                            "covariance":predictive["covariance"].tolist(),"status":predictive["status"]},
                        "native_parity":parity})
    import cobaya.likelihoods.base_classes.cmblikes as cmblikes
    native_source=Path(inspect.getfile(cmblikes))
    files=list(dict.fromkeys([reference_path,native_source]+[p for v in variants for p in v["files"]]))
    sources=[]
    for path in files:
        try: label=str(path.relative_to(root))
        except ValueError: label=str(path)
        sources.append({"path":label,"sha256":sha256(path),"size_bytes":path.stat().st_size})
    result={"owner":"HTT","scope":"PLANCK_PR3_RELEASED_NINE_BIN_RECONSTRUCTION_PP_AMPLITUDE",
            "release":"Planck 2018 lensing PP reconstruction, consext8",
            "method_source":"https://arxiv.org/abs/1807.06210",
            "transfer_source":"fixed bundled CAMB Planck 2018 reference; released native Planck windows",
            "reference_convention":"lens_potential_cls[:,0] at explicit ell_pp is [L(L+1)]^2 C_L^phiphi/(2pi), dimensionless; TT/EE/TE D_ell in uK^2",
            "amplitude_definition":"multiplicative reconstruction phi-phi reference amplitude, not smoothing A_L, shear, or tilt",
            "primary_variant":"CMB_MARGINALIZED","variants":outputs,
            "source_files":sources,"claim_tier":"CONDITIONAL_DIAGNOSTIC",
            "scientific_admission":"NOT_EVALUATED","calibrated_null_PTE":None,"evidence":None,
            "caveats":["Primary CMB-marginalized covariance and response already encode CMB information; no multiplication with primary CMB likelihood",
                       "Nonmarginal fixed-CMB version is a sensitivity using its own covariance and A_planck=1, not another likelihood factor",
                       "Reference best-fit includes Planck lensing information; source-consistency diagnostic only",
                       "No cosmological posterior, evidence, physical null PTE, or independent ACT/Planck combination"]}
    return result


def plot(result,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for row,color in zip(result["variants"],["tab:blue","tab:orange"]):
        x=np.array(row["ell_bins"])[:,3]
        y=np.array(row["y_PP_dimensionless"])
        model=row["fit"]["amplitude"]*np.array(row["a_PP_amplitude_response_dimensionless"])+np.array(row["c_fixed_offset_dimensionless"])
        label=row["variant"].replace("_"," ")
        axes[0].plot(x,model,"-o",color=color,label=label)
        axes[1].plot(x,y-model,"-o",color=color,label=label)
    axes[0].plot(np.array(result["variants"][0]["ell_bins"])[:,3],result["variants"][0]["y_PP_dimensionless"],"kx",label="released PP")
    axes[0].set(xlabel="L effective",ylabel="PP bandpower (dimensionless)")
    axes[1].set(xlabel="L effective",ylabel="Data minus fitted affine model")
    axes[0].legend(fontsize=7)
    fig.suptitle("Planck PR3 released nine-bin PP amplitude diagnostic")
    fig.tight_layout()
    for suffix in ("png","pdf"):
        fig.savefig(output/("diagnostic."+suffix),dpi=150)
    plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--closeout-from-result",type=Path,
                        help="verify saved fitted peaks and render from existing nine-bin result without refitting")
    args=parser.parse_args(argv)
    root=args.repo_root.resolve();output=args.output.resolve()
    if args.closeout_from_result is not None:
        return run_closeout(root,output,args.closeout_from_result)
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    receipt={"task":"PLANCK_PR3_EXACT_NATIVE_NINE_BIN_PP","command":sys.argv,
             "repo_root":str(root),"requested_author_runtime":"gpt-6-sol/high",
             "observed_author_runtime":"UNKNOWN","python":sys.version,"numpy":np.__version__}
    for key,command in (("git_head",["rev-parse","HEAD"]),("git_status",["status","--porcelain=v1"])):
        call=subprocess.run(["git","-C",str(root),*command],capture_output=True,text=True)
        receipt[key]=call.stdout.strip() if call.returncode==0 else "UNAVAILABLE"
    try:
        result=evaluate(root)
        (output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
        plot(result,output)
        primary,sensitivity=result["variants"]
        report=("# Planck PR3 exact-source nine-bin PP amplitude\n\n"
                f"Primary CMB-marginalized A_PP = {primary['fit']['amplitude']:.8g} ± {primary['fit']['conditional_se']:.8g} (fixed reference Gaussian proxy).\n\n"
                f"Nonmarginal fixed-CMB sensitivity A_PP = {sensitivity['fit']['amplitude']:.8g} ± {sensitivity['fit']['conditional_se']:.8g}; A_planck=1.\n\n"
                "Native Cobaya bin/window and unnormalized Gaussian chi-square parity passed at A=0.8,1,1.2 for both variants. "
                "The scalar Uniform[0,2] posterior is a declared scenario, not the release prior. "
                "No cosmological fit, physical null PTE, evidence, or independent multiplication with primary CMB or ACT+Planck products follows.\n")
        (output/"report.md").write_text(report)
        receipt["exit_code"]=0
    except Exception as error:
        receipt["exit_code"]=1
        receipt["error"]=type(error).__name__+": "+str(error)
        (output/"failure.log").write_text(traceback.format_exc())
    receipt["elapsed_seconds"]=time.monotonic()-started
    receipt["code_sha256"]=sha256(Path(__file__))
    (output/"execution_receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"exit_code":receipt["exit_code"],"output":str(output)}))
    return receipt["exit_code"]


if __name__=="__main__":
    raise SystemExit(main())
