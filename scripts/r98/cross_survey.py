"""R98 full existing radio/Gaia reanalysis with shared-patch comparisons.

Radio: retained R89 source readers/masks, positive log-intensity Poisson and
NB1 (Boehme et al. 2025) likelihoods, four-fold spatial prediction, and a
joint 15D shared-patch dipole covariance. Gaia: all CRF3 + all Quaia join,
ten overlapping source/weight/redshift fits and joint 160D patch covariance.
These are conditional diagnostic laws, not a calibrated cosmological null.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, time, resource, collections
from pathlib import Path
import healpy as hp
import numpy as np
from astropy.io import fits
from scipy.optimize import minimize
from scipy.special import gammaln, digamma
from scripts.r69.gaia_e2_b2 import templates, prepare
from htt.obsstat import pre_dag_fast
from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import stf_features

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
CACHE=Path("/home/cosmosapjw/Downloads/htt_r98_full_data")
R89=ROOT/"docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
RADIO_SOURCE=R89/"G04_RADIO_FRAME/run_g04_solver_free_research.py"
GAIA=Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
JOIN=Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""): h.update(b)
    return h.hexdigest()
def dump(name,d):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
def load_radio():
    spec=importlib.util.spec_from_file_location("r98_r89_radio_source",RADIO_SOURCE)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def logpmf_score(y,eta,p=0.0):
    """NB1 at fixed p: E n=mu; Var n=mu/(1-p); r=mu*(1-p)/p."""
    mu=np.exp(eta)
    if p<=1e-7:return y*eta-mu-gammaln(y+1),y-mu
    r=mu*(1-p)/p
    logp=gammaln(y+r)-gammaln(r)-gammaln(y+1)+r*np.log1p(-p)+y*np.log(p)
    score=r*(digamma(y+r)-digamma(r)+np.log1p(-p))
    return logp,score
def fit_count_model(y,X,model="poisson",initial=None):
    y=np.asarray(y,float); X=np.asarray(X,float)
    if X.ndim!=2 or len(y)!=len(X) or len(y)<=X.shape[1] or np.any(y<0):
        raise ValueError("invalid counts/design")
    # Same moment prescription as literature, evaluated on training cells only.
    var=float(np.var(y,ddof=1));mean=float(np.mean(y))
    p=0.0 if model=="poisson" else float(np.clip(1-mean/max(var,1e-15),0,.98))
    b=np.zeros(X.shape[1]);b[0]=np.log(max(mean,1e-10))
    if initial is not None:b[:]=initial
    # Thin QR changes optimizer coordinates, not the intensity model or law.
    # It resolves southern-footprint dipole/quadrupole collinearity without ridge.
    Q,R=np.linalg.qr(X,mode="reduced"); Z=Q*np.sqrt(len(y))
    if np.linalg.matrix_rank(R)<X.shape[1]:raise ValueError("count design rank deficient")
    theta0=R@b/np.sqrt(len(y))
    def objective(theta):
        l,score=logpmf_score(y,Z@theta,p)
        return -float(np.mean(l)),-(Z.T@score)/len(y)
    opt=minimize(objective,theta0,jac=True,method="BFGS",
                 options={"gtol":1e-7,"maxiter":700})
    nll,grad=objective(opt.x)
    beta=np.linalg.solve(R,opt.x*np.sqrt(len(y)))
    _,raw_score=logpmf_score(y,X@beta,p)
    raw_gradient=-(X.T@raw_score)/len(y)
    accepted=bool(np.isfinite(opt.fun) and np.max(np.abs(grad))<2e-5)
    if not accepted:raise RuntimeError(f"count optimizer: {opt.message}, whitened_gradient={np.max(np.abs(grad))}, model={model}, n={len(y)}, p={p}")
    return {"beta":beta,"p":p,"nll":nll,"max_mean_score_abs":float(np.max(np.abs(raw_gradient))),
            "whitened_max_mean_score_abs":float(np.max(np.abs(grad))),
            "optimizer_success":bool(opt.success),"iterations":int(opt.nit),
            "design_condition":float(np.linalg.cond(R)),"parameter_preconditioner":"thin_QR_no_ridge"}
def jackknife_cov(leave):
    z=np.asarray(leave,float)
    if z.ndim!=2 or z.shape[0]<2:raise ValueError("need synchronized leave-one-patch vectors")
    d=z-z.mean(axis=0);return (len(z)-1)/len(z)*(d.T@d)
def exact_log_dipole(b):
    """Full-sky l=1 coefficient of exp(b.n) divided by its monopole."""
    b=np.asarray(b,float);r=float(np.linalg.norm(b))
    factor=1-r*r/15+2*r**4/315 if r<1e-4 else 3*(1/np.tanh(r)-1/r)/r
    return factor*b
def radio_run(rebuild=False,audit_inputs=False):
    t=time.monotonic();CACHE.mkdir(parents=True,exist_ok=True);src=load_radio()
    cp=CACHE/"radio_full_maps.npz";receipt=CACHE/"radio_full_maps_sources.json"
    raw=[src.NHI_FITS,src.NVSS_GZ,src.RACS_GZ,src.SPICE_GZ,src.SUMSS_GZ,src.LOTSS_FITS]
    # First audit hashes complete inputs. Routine cached replay validates
    # size+mtime+inode against that audit; --audit-inputs requests fresh byte checks.
    finger=CACHE/"radio_full_maps_fingerprints.json"
    now={str(p):{"bytes":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"inode":p.stat().st_ino} for p in raw}
    if cp.exists() and receipt.exists() and finger.exists() and not rebuild:
        old_seal=json.loads(finger.read_text())
        if old_seal.get("receipt_sha256")!=sha(receipt) or old_seal.get("maps_sha256")!=sha(cp):
            raise RuntimeError("cached map/receipt digest changed; raw audit cannot authorize old-map replacement")
    use_locked=(cp.exists() and receipt.exists() and finger.exists() and not rebuild and not audit_inputs)
    if use_locked:
        seal=json.loads(finger.read_text())
        if seal.get("fingerprints")!=now:raise RuntimeError("source storage identity changed; rerun --audit-inputs")
        if seal.get("receipt_sha256")!=sha(receipt) or seal.get("maps_sha256")!=sha(cp):raise RuntimeError("cached map/receipt digest changed")
        identities=json.loads(receipt.read_text());identity_mode="locked_full_sha_plus_current_stat"
        if identities["reader_sha256"]!=sha(RADIO_SOURCE):raise RuntimeError("inherited reader identity changed")
    else:
        identities={str(p):{"bytes":p.stat().st_size,"sha256":sha(p)} for p in raw}
        identities["reader_sha256"]=sha(RADIO_SOURCE);identity_mode="all_bytes_sha256_this_run"
        after={str(p):{"bytes":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"inode":p.stat().st_ino} for p in raw}
        if now!=after:raise RuntimeError("raw file changed during source audit")
    if cp.exists() and receipt.exists() and not rebuild:
        if json.loads(receipt.read_text())!=identities:raise RuntimeError("cached maps/input identity mismatch; rebuild explicitly")
        with np.load(cp,allow_pickle=False) as z:
            maps={};masks={}
            for k in z.files:
                if k.startswith("mask__"):masks[k[6:]]=z[k].astype(bool)
                else:
                    _,name,cut=k.split("__");maps.setdefault(name,{})[float(cut)]=z[k].copy()
        full_stream=False
    else:
        nhi=src._build_nhi_ns16_icrs()
        base=(np.abs(src.PIX_B_DEG)>15)&(nhi<1e21)
        maps,masks=src._scan_all_five(base)
        arrays={f"map__{name}__{cut}":v for name,dd in maps.items() for cut,v in dd.items()}
        arrays.update({f"mask__{name}":v for name,v in masks.items()})
        np.savez_compressed(cp,**arrays);receipt.write_text(json.dumps(identities,indent=2)+"\n");full_stream=True
    # Transactional seal only after byte identities match an existing map, or a new map is complete.
    seal={"fingerprints":now,"receipt_sha256":sha(receipt),"maps_sha256":sha(cp)}
    finger.write_text(json.dumps(seal,indent=2)+"\n")
    mask_name={"NVSS":"NVSS","RACS_DR1":"RACS_DR1_unif","SPICE_RACS":"SPICE_RACS","SUMSS":"SUMSS","LoTSS_DR3":"LoTSS_DR3_int1500"}
    X4=np.column_stack((np.ones(src.NPIX),src.PIX_N))
    X9=np.column_stack((X4,stf_features(src.PIX_N)))
    rng=np.random.default_rng(9804);fold_of_patch=np.empty(48,int);fold_of_patch[rng.permutation(48)]=np.arange(48)%4
    fold=fold_of_patch[src.PIX_PATCH]
    rows={};leaves={};comparison=[]
    for survey,dd in maps.items():
        m=masks[mask_name[survey]];rows[survey]={}
        for cut,cts in sorted(dd.items()):
            row={"n_sources":int(cts[m].sum()),"n_cells":int(m.sum()),"models":{}}
            for name,model,X in (("Poisson4","poisson",X4),("NB1_4","nb1",X4),("NB1_9","nb1",X9)):
                fit=fit_count_model(cts[m],X[m],model)
                preds=[]
                for k in range(4):
                    tr=m&(fold!=k);te=m&(fold==k)
                    if te.sum()==0:continue
                    ft=fit_count_model(cts[tr],X[tr],model)
                    lp,_=logpmf_score(cts[te],X[te]@ft["beta"],ft["p"])
                    preds.append({"fold":k,"train_cells":int(tr.sum()),"test_cells":int(te.sum()),
                                  "train_p":ft["p"],"test_loglik":float(lp.sum())})
                beta=fit.pop("beta")
                fit.update(beta_log_intensity=beta.tolist(),heldout_folds=preds,
                    heldout_sum_loglik=float(sum(p["test_loglik"] for p in preds)),
                    log_dipole_norm=float(np.linalg.norm(beta[1:4])))
                if X.shape[1]==4:fit["exact_fullsky_model_dipole"]=exact_log_dipole(beta[1:4]).tolist()
                row["models"][name]=fit
            row["NB1_minus_Poisson_heldout_logscore"]=row["models"]["NB1_4"]["heldout_sum_loglik"]-row["models"]["Poisson4"]["heldout_sum_loglik"]
            row["NB1_9_minus_NB1_4_heldout_logscore"]=row["models"]["NB1_9"]["heldout_sum_loglik"]-row["models"]["NB1_4"]["heldout_sum_loglik"]
            rows[survey][str(cut)]=row
        # All surveys share exact same 48 ICRS removal patches.
        cut=50.0 if survey=="LoTSS_DR3" else 20.0;cts=dd[cut]
        full=fit_count_model(cts[m],X4[m],"nb1");ll=[]
        for k in range(48):
            mm=m&(src.PIX_PATCH!=k)
            fit=fit_count_model(cts[mm],X4[mm],"nb1",full["beta"])
            ll.append(fit["beta"][1:4])
        leaves[survey]=np.asarray(ll)
        print("R98_RADIO",survey,"cells",int(m.sum()),"cuts",len(dd),flush=True)
    names=list(leaves);joint=np.concatenate([leaves[n] for n in names],axis=1);C=jackknife_cov(joint)
    for i,a in enumerate(names):
        for j,b in enumerate(names[:i]):
            da=np.asarray(rows[a]["50.0" if a=="LoTSS_DR3" else "20.0"]["models"]["NB1_4"]["beta_log_intensity"])[1:4]
            db=np.asarray(rows[b]["50.0" if b=="LoTSS_DR3" else "20.0"]["models"]["NB1_4"]["beta_log_intensity"])[1:4]
            cv=jackknife_cov(leaves[a]-leaves[b]);naive=jackknife_cov(leaves[a])+jackknife_cov(leaves[b])
            comparison.append({"a":a,"b":b,"delta_log_dipole":(da-db).tolist(),
                "shared_patch_contrast_cov":cv.tolist(),"independence_cov":naive.tolist(),
                "trace_ratio_shared_to_independence":float(np.trace(cv)/np.trace(naive)),
                "minimum_cov_eigenvalue":float(np.linalg.eigvalsh(cv)[0]),
                "calibrated_p":None})
    np.savez_compressed(CACHE/"radio_joint_patch_statistics.npz",leave=joint,cov=C,names=np.asarray(names))
    prior=json.loads((R89/"G04_RADIO_FRAME/DEEP_FIVE_SURVEY_RESULT.json").read_text())
    out={"schema":"htt.r98.radio_full_models/1","sources":identities,
         "complete_raw_stream_this_run":full_stream,"source_identity_check":identity_mode,"all_existing_five_surveys":True,
         "all_flux_thresholds_analyzed":sum(len(v) for v in rows.values()),
         "scope":"All stored catalog rows visited by inherited readers; all eligible sources on declared R89 masks. Zero-count pixels retained on those masks; LoTSS density-defined footprint remains conditional.",
         "full_row_counts_prior_verified_reader_census":{k:{a:v for a,v in r.items() if a in ("total_rows","total_parsed_rows")} for k,r in prior["surveys"].items()},
         "maps_sha256":sha(cp),"mask_sha256":{k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in masks.items()},
         "surveys":rows,"pairwise_shared_patch_comparisons":comparison,
         "joint_15d_patch_covariance":{"order":names,"matrix":C.tolist(),"rank":int(np.linalg.matrix_rank(C)),
            "nonempty_global_patches":{name:int(np.unique(src.PIX_PATCH[masks[mask_name[name]]]).size) for name in names},
            "delete_one_interpretation":"48 synchronized global patches; inactive patches retained; unequal survey footprint information, finite spatial diagnostic not calibrated covariance estimator",
            "max_abs_cross_block_correlation":float(max(np.max(np.abs(C[3*i:3*i+3,3*j:3*j+3])/np.sqrt(np.outer(np.diag(C)[3*i:3*i+3],np.diag(C)[3*j:3*j+3]))) for i in range(5) for j in range(i)))},
         "model":"NB1 fixed p estimated using training mean/variance; mean exp(b0+b.n[+q.STF]); conditional cell factorization, no independent-source or joint-catalog cosmological likelihood claim",
         "literature":"Boehme et al. PRL135,201001(2025), DOI10.1103/6z32-3zf4 eqs4-8; positive log-link is explicit R98 extension, not exact replication.",
         "constraints":{"physical_Pi":None,"physical_GF":None,"joint_cosmological_null_qualified":False,
                        "overlap_covariance_is_spatial_diagnostic":True,"sample_flux_thresholds_are_correlated":True},
         "runtime_seconds":time.monotonic()-t}
    dump("RADIO_FULL_MODELS.json",out);return out
BACKEND_COUNTS=collections.Counter()
BACKEND_ROW_COUNTS=collections.Counter()
def empty_gaia():
    return {"F":np.zeros((48,16,16)),"s":np.zeros((48,16)),"yy":np.zeros(48),"n":np.zeros(48,int)}
def add_gaia(acc,B,y,e1,e2,rho,patch,weights=None):
    for p in np.unique(patch):
        m=patch==p;scale=1.0 if weights is None else 1/np.sqrt(weights[m])
        F,s,yy=pre_dag_fast.accumulate_gaia(B[m],y[m],e1[m]*scale,e2[m]*scale,rho[m],threads=1)
        receipt=pre_dag_fast.last_backend_receipt(); key=receipt.get("used","unknown"); BACKEND_COUNTS[key]+=1; BACKEND_ROW_COUNTS[key]+=int(m.sum())
        acc["F"][p]+=F;acc["s"][p]+=s;acc["yy"][p]+=yy;acc["n"][p]+=int(m.sum())
def summarize_gaia(a):
    F=a["F"].sum(axis=0);s=a["s"].sum(axis=0);beta=np.linalg.solve(F,s)
    leave=np.array([np.linalg.solve(F-a["F"][k],s-a["s"][k]) for k in range(48)])
    C=jackknife_cov(leave);pred=[];ins=[]
    for k in range(48):
        b=leave[k];pred.append(float(a["yy"][k]-2*b@a["s"][k]+b@a["F"][k]@b))
        ins.append(float(a["yy"][k]-2*beta@a["s"][k]+beta@a["F"][k]@beta))
    return {"n_sources":int(a["n"].sum()),"nonempty_patches":int(np.count_nonzero(a["n"])),
        "coefs_microasyr":(1000*beta).tolist(),"joint_patch_cov_microasyr2":(1e6*C).tolist(),
        "patch_prediction_chi2_per_component":float(sum(pred)/(2*a["n"].sum())),
        "prediction_minus_insample_chi2":float(sum(pred)-sum(ins)),
        "F_condition":float(np.linalg.cond(F))},leave*1000
def gaia_run():
    t=time.monotonic();CACHE.mkdir(parents=True,exist_ok=True);BACKEND_COUNTS.clear();BACKEND_ROW_COUNTS.clear()
    sets={k:empty_gaia() for k in ("crf3_all","crf3_quality","quaia_inverse_noise","quaia_multiply_selection","quaia_ipw_0p20","quaia_ipw_0p35","quaia_z0","quaia_z1","quaia_z2","quaia_z3")}
    with fits.open(GAIA,memmap=True) as h:
        T=h[1].data;total=len(T)
        for begin in range(0,total,60000):
            rr,dd,y1,y2,e1,e2,rho,valid,qual=prepare(T[begin:begin+60000])
            for name,ok in (("crf3_all",valid),("crf3_quality",valid&qual)):
                _,B=templates(rr[ok],dd[ok]);p=hp.ang2pix(2,np.pi/2-dd[ok],rr[ok])
                add_gaia(sets[name],B,np.column_stack((y1[ok],y2[ok])),e1[ok],e2[ok],rho[ok],p)
    with np.load(JOIN,allow_pickle=False) as z:
        d={k:z[k].copy() for k in ("ra","dec","redshift_quaia","gaia_pmra","gaia_pmdec","gaia_pmra_error","gaia_pmdec_error","gaia_pmra_pmdec_corr","gaia_ruwe","gaia_astrometric_params_solved","selection_relative")}
    yy=np.column_stack((d["gaia_pmra"],d["gaia_pmdec"]));e1=d["gaia_pmra_error"];e2=d["gaia_pmdec_error"];rho=d["gaia_pmra_pmdec_corr"];sel=d["selection_relative"];zq=d["redshift_quaia"]
    valid=np.isfinite(d["ra"])&np.isfinite(d["dec"])&np.isfinite(zq)&np.isfinite(yy).all(axis=1)&np.isfinite(e1)&np.isfinite(e2)&np.isfinite(rho)&(e1>0)&(e2>0)&(np.abs(rho)<.999)&(d["gaia_ruwe"]<1.4)&(d["gaia_astrometric_params_solved"]==31)&(np.abs(yy)<100).all(axis=1)&(sel>0)
    ii=np.flatnonzero(valid)
    if len(ii)!=634233:raise RuntimeError("Quaia source census changed")
    for start in range(0,len(ii),60000):
        ix=ii[start:start+60000];rr=np.deg2rad(d["ra"][ix]);dd=np.deg2rad(d["dec"][ix]);_,B=templates(rr,dd);p=hp.ang2pix(2,np.pi/2-dd,rr)
        for name,w in (("quaia_inverse_noise",np.ones(len(ix))),("quaia_multiply_selection",sel[ix]),("quaia_ipw_0p20",1/np.maximum(sel[ix],.20)),("quaia_ipw_0p35",1/np.maximum(sel[ix],.35))):
            add_gaia(sets[name],B,yy[ix],e1[ix],e2[ix],rho[ix],p,w)
        bins=np.digitize(zq[ix],[.8,1.5,2.1])
        for k in range(4):
            m=bins==k
            if np.any(m):add_gaia(sets[f"quaia_z{k}"],B[m],yy[ix][m],e1[ix][m],e2[ix][m],rho[ix][m],p[m])
    fits_out={};leaves={}
    for name,a in sets.items():fits_out[name],leaves[name]=summarize_gaia(a)
    common_score={}
    ref=sets["quaia_inverse_noise"]
    for name in ("quaia_inverse_noise","quaia_multiply_selection","quaia_ipw_0p20","quaia_ipw_0p35"):
        score=0.0
        for k in range(48):
            b=leaves[name][k]/1000;score+=ref["yy"][k]-2*b@ref["s"][k]+b@ref["F"][k]@b
        common_score[name]=float(score)
    names=list(sets);joint=np.concatenate([leaves[n] for n in names],axis=1);C=jackknife_cov(joint)
    comparisons=[]
    for a,b in (("crf3_all","crf3_quality"),("crf3_quality","quaia_inverse_noise"),("quaia_inverse_noise","quaia_multiply_selection"),("quaia_inverse_noise","quaia_ipw_0p20"),("quaia_ipw_0p20","quaia_ipw_0p35"),("quaia_z0","quaia_z3")):
        delta=np.asarray(fits_out[a]["coefs_microasyr"])-np.asarray(fits_out[b]["coefs_microasyr"]);cv=jackknife_cov(leaves[a]-leaves[b]);naive=jackknife_cov(leaves[a])+jackknife_cov(leaves[b])
        comparisons.append({"a":a,"b":b,"delta_microasyr":delta.tolist(),"shared_patch_contrast_cov":cv.tolist(),
            "trace_ratio_shared_to_independence":float(np.trace(cv)/np.trace(naive)),
            "E2_delta_norm":float(np.linalg.norm(delta[6:11])),"B2_delta_norm":float(np.linalg.norm(delta[11:16])),
            "calibrated_p":None})
    np.savez_compressed(CACHE/"gaia_joint_patch_statistics.npz",leave=joint,cov=C,names=np.asarray(names),
                        **{f"{name}__{key}":v for name,a in sets.items() for key,v in a.items()})
    out={"schema":"htt.r98.gaia_full_shared_patch/1",
        "sources":{str(p):{"bytes":p.stat().st_size,"sha256":sha(p)} for p in (GAIA,JOIN)},
        "source_row_census":{"gaia_crf3_total":total,"quaia_join_total":len(zq),"quaia_qualified":len(ii),"all_source_rows_visited":True},
        "fits":fits_out,"redshift_bin_edges":[.8,1.5,2.1],"comparisons":comparisons,
        "joint_160d_patch_covariance":{"order":names,"rank":int(np.linalg.matrix_rank(C)),"max_rank_from_48_patches":47,
            "cache_path":str(CACHE/"gaia_joint_patch_statistics.npz"),"sha256":sha(CACHE/"gaia_joint_patch_statistics.npz"),
            "full_160d_inverse_or_chi_square_used":False},
        "backend_receipt":{"last":pre_dag_fast.last_backend_receipt(),"calls_by_backend":dict(BACKEND_COUNTS),"source_row_visits_by_backend":dict(BACKEND_ROW_COUNTS)},
        "common_inverse_noise_out_of_patch_chi2":common_score,
        "working_weighted_chi2_across_different_weight_models_not_comparable":True,
        "selection_definitions":{"crf3_quality":"R69: finite covariance, ruwe<1.4, visibility_periods_used>=8, duplicated_source=False; distinct from R89 5parameter subset","quaia":"R91 634233 full G20 joined five-parameter clean source, floors relative selection"},
        "reuse":["R69 tangent VSH/CRF3 mask","R91 exact Quaia/G20 weighting semantics","certified C++ accumulation"],
        "constraints":{"physical_Pi":None,"physical_GF":None,"normal_shear_or_vorticity_inferred":False,"shared_patch_covariance_is_spatial_diagnostic":True,"coefficient_comparisons_are_correlated":True},
        "runtime_seconds":time.monotonic()-t}
    dump("GAIA_FULL_SHARED_PATCH.json",out);return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--task",choices=["radio","gaia","all"],default="all");ap.add_argument("--rebuild",action="store_true");ap.add_argument("--audit-inputs",action="store_true");args=ap.parse_args()
    if args.task in ("radio","all"):radio_run(args.rebuild,args.audit_inputs)
    if args.task in ("gaia","all"):gaia_run()
    print(json.dumps({"finished":args.task,"maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
if __name__=="__main__":main()
