#!/usr/bin/env python3
"""Independent R58 data checks; numpy/scipy only, no candidate function calls.
Contract: reproduce selected-CF4 seven-model 32-row carriers from committed rows
using independently formed WLS normal equations; verify full GLS and ablation
sandwich against persisted candidate, without pair sums or cache mutation.
Conditional on the inherited frozen LCDM covariance and fixed Gaussian model.
"""
from pathlib import Path
import argparse
import sys
import numpy as np
from scipy import linalg, stats, integrate
import scipy,json,hashlib,platform,time

R58_RELATIVE = Path("docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117")


def check(root: Path, results: Path, output: Path, candidate_root: Path) -> None:
    """Replay the unchanged independent numerical oracle against supplied files."""
    if not __debug__:
        raise RuntimeError("Run without Python -O: this numerical checker requires assertions.")
    R, OUT = root.resolve(), results.resolve()
    output, candidate_root = output.resolve(), candidate_root.resolve()
    if output in {OUT / "OWNED_TENSOR_RESULT.json", OUT / "OWNED_TENSOR_CARRIERS.npz"}:
        raise ValueError("The review output must not overwrite a numerical input.")
    t0=time.monotonic()
    hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result=json.loads((OUT/'OWNED_TENSOR_RESULT.json').read_text())
    inputs={R/k:v for k,v in result['inputs_sha256'].items()}
    candidate_sources = {candidate_root/'scripts/r58/run_r58_owned_tensor.py':result['implementation']['runner_sha256'], candidate_root/'htt/htt/htt/infer/r58_mixed_tensor_likelihood.py':result['implementation']['fit_module_sha256']}
    inputs.update(candidate_sources)
    inputs.update({OUT/'OWNED_TENSOR_RESULT.json':hashfile(OUT/'OWNED_TENSOR_RESULT.json'),OUT/'OWNED_TENSOR_CARRIERS.npz':result['carrier_sha256']})
    before={str(p):hashfile(p) for p in inputs}
    assert all(before[str(p)]==v for p,v in inputs.items())
    car=np.load(OUT/'OWNED_TENSOR_CARRIERS.npz',allow_pickle=False)
    cat=np.load(R/'docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz',allow_pickle=False)
    rd=R/'docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS'
    lab=np.load(rd/'R54_L04_SURVEY_LABELS.npz',allow_pickle=False)
    assert np.array_equal(lab['group_id'],cat['group_id'])
    z=cat['z_CMB']; n=cat['n_J2000'];m=cat['method_family'];e=cat['e_dmzp'];mu=cat['dmzp']
    Om=.3153;c=299792.458
    zg=np.linspace(0,z.max()*1.001,6001); einv=1/np.sqrt(Om*(1+zg)**3+1-Om)
    chi=np.interp(z,zg,integrate.cumulative_trapezoid(einv,zg,initial=0))
    g=((1+z)/(np.sqrt(Om*(1+z)**3+1-Om)*chi)-1)/c
    eta=np.log(c*(1+z)*chi/10**((mu-25)/5));tau2=(np.log(10)/5*e)**2+(250*g)**2
    x,y,zz=n.T
    basis=np.column_stack((np.ones(len(z)),x,y,zz,(x*x-y*y)/np.sqrt(2),(x*x+y*y-2*zz*zz)/np.sqrt(6),np.sqrt(2)*x*y,np.sqrt(2)*x*zz,np.sqrt(2)*y*zz))
    physical=np.column_stack((g[:,None]*n,basis[:,1:]))
    mono=np.column_stack([m==s for s in ('FP','SN','TF')]).astype(float)
    step=np.where(zz>=0,1.,-1.)
    split=np.column_stack([mono]+[(m==s)*step for s in ('FP','OTHER','SN','TF')])
    rot=np.array([[-.0548755604162154,-.8734370902348850,-.4838350155487132],[.4941094278755837,-.4448296299600112,.7469822444972189],[-.8676661490190047,-.1980763734312015,.4559837761750669]])
    labels=lab['survey'];sur=np.column_stack([(labels==s).astype(float) for s in np.unique(labels) if s!='OTHER_ALL'])
    extra={'log':None,'log_mono':mono,'log_split':split,'log_survey':sur,'log_mono_radial':np.column_stack((mono,z)),'log_mono_galactic':np.column_stack((mono,abs((n@rot.T)[:,2]))),'log_mono_error':np.column_stack((mono,(np.log(10)/5*e)**2))}
    rows=np.r_[[9*w+k for w in range(4) for k in (1,2,3)],[9*w+k for w in range(4) for k in range(4,9)]]
    assert np.array_equal(rows,car['row_indices32'])
    s=car['parameter_scale'];report={}
    rel=lambda a,b:float(np.max(abs(np.asarray(a)-b))/max(float(np.max(abs(np.asarray(b)))),1e-30))
    nsim=60000;ez=np.random.default_rng(9345081).standard_normal((nsim,32)); cutoff=stats.chi2.ppf(.95,11)
    for name,nuisance in extra.items():
        design=basis if nuisance is None else np.column_stack((basis,nuisance))
        ops=[];condition=[]
        for center in (.025,.04,.06,.08):
            w=np.exp(-.5*((z-center)/.012)**2)/tau2
            xtw=design.T*w; normal=xtw@design; condition.append(np.linalg.cond(normal))
            ops.append(linalg.solve(normal,xtw,assume_a='pos')[:9])
        op=np.vstack(ops);y36=op@eta; d36=op@physical; cw=(op*tau2)@op.T
        cache=np.load(rd/('R54_L05_COSMIC_COV.npz' if name in ('log','log_mono','log_split') else 'R54_L04_COSMIC_COV.npz'),allow_pickle=False)
        ix=np.array([i for i,l in enumerate(cache['labels']) if str(l).split(':')[0]==name]); assert len(ix)==36
        assert list(cache['labels'][ix])==[f'{name}:{i}' for i in range(36)]
        cb=cache['cosmic_linear'][np.ix_(ix,ix)];C=(cw+cb)[np.ix_(rows,rows)];Y=y36[rows];X=d36[rows];Xs=X*s
        cx=linalg.solve(C,Xs,assume_a='pos');J=Xs.T@cx; jf=linalg.cho_factor(J,lower=True)
        A=linalg.cho_solve(jf,cx.T);est=s*(A@Y);pcov=s[:,None]*linalg.cho_solve(jf,np.eye(11))*s[None,:]
        resid=Y-X@est; qres=float(resid@linalg.solve(C,resid,assume_a='pos'));q0=float(Y@linalg.solve(C,Y,assume_a='pos'));wald=q0-qres
        f=result['variants'][name]['fit']; B=linalg.block_diag(C[:12,:12],C[12:,12:]); bx=linalg.solve(B,Xs,assume_a='pos');BJ=Xs.T@bx
        BA=linalg.solve(BJ,bx.T,assume_a='pos'); be=s*(BA@Y);bc=s[:,None]*linalg.inv(BJ)*s[None,:];BA=s[:,None]*BA
        sand=BA@C@BA.T; evals=linalg.eigvalsh(sand,bc)
        nominal_error=ez@linalg.cholesky(C,lower=True).T@BA.T
        whiten=linalg.solve_triangular(linalg.cholesky(bc,lower=True),nominal_error.T,lower=True).T
        mc=float(np.mean(np.sum(whiten**2,axis=1)<=cutoff));mcse=float(np.sqrt(mc*(1-mc)/nsim))
        covfull=ez@linalg.cholesky(C,lower=True).T@(s[:,None]*A).T
        wf=linalg.solve_triangular(linalg.cholesky(pcov,lower=True),covfull.T,lower=True).T
        coverage_full=float(np.mean(np.sum(wf**2,axis=1)<=cutoff))
        ab=result['variants'][name]['same_response_block_diagonal_covariance_ablation'];cal=result['variants'][name]['block_diagonal_uncertainty_calibration']
        errors={'observations_rel':rel(y36,car[name+'__theta36']),'white_cov_rel':rel(cw,car[name+'__white36']),'design_rel':rel(d36,car[name+'__response36x11']),'body_cov_rel':rel(cb,car[name+'__body36']),'estimate_rel':rel(est,f['estimate']),'cov_rel':rel(pcov,f['covariance']),'null_q_abs':abs(q0-f['null_chi2']),'wald_q_abs':abs(wald-f['wald']),'resid_q_abs':abs(qres-f['residual_chi2']),'ablation_estimate_rel':rel(be,ab['estimate']),'ablation_nominal_cov_rel':rel(bc,ab['covariance']),'ablation_sandwich_rel':rel(sand,cal['actual_sampling_covariance']),'ablation_eigenvalue_rel':rel(evals,cal['actual_to_nominal_variance_eigenvalues'])}
        assert max(v for k,v in errors.items() if k.endswith('_rel'))<1e-8,(name,errors)
        assert max(v for k,v in errors.items() if k.endswith('_abs'))<1e-7,(name,errors)
        assert abs(mc-cal['coverage_of_nominal_95_ellipsoid_under_full_covariance'])<5*np.sqrt(mcse**2+cal['simulation']['mc_standard_error']**2)
        assert abs(coverage_full-.95)<5*np.sqrt(.95*.05/nsim)
        assert np.linalg.norm((s[:,None]*A)@X-np.eye(11),ord=np.inf)<1e-10
        ann_cols = np.ones((len(z),1)) if nuisance is None else np.column_stack((np.ones(len(z)),nuisance))
        annihilation = float(np.max(np.abs(op[rows] @ ann_cols)))
        report[name]={'errors':errors,'operator_normal_condition_max':max(condition),'gls_scaled_precision_condition':float(np.linalg.cond(J)),'nuisance_annihilation_max_abs':annihilation,'independent_sampling_coverage_block_nominal95':mc,'independent_sampling_coverage_full_nominal95':coverage_full,'mc_se':mcse,'wald_p':float(stats.chi2.sf(wald,11)),'null_p':float(stats.chi2.sf(q0,32)),'adequacy_p':float(stats.chi2.sf(qres,21))}
        print(name, max(errors.values()), mc, coverage_full, flush=True)
    zs=np.quantile(z,np.linspace(0,1,13));truechi=np.array([integrate.quad(lambda t:1/np.sqrt(Om*(1+t)**3+1-Om),0,zi,epsabs=1e-13,epsrel=1e-13)[0] for zi in zs]);approxchi=np.interp(zs,zg,integrate.cumulative_trapezoid(einv,zg,initial=0))
    maxp=max(v['wald_p'] for v in report.values());assert abs(maxp-result['robust']['max_wald_p_common_theta_zero'])<1e-10
    for i,p in enumerate(result['parameter_names']):
        lower=min(v['simultaneous_95_intervals'][p]['estimate']-np.sqrt(cutoff)*v['simultaneous_95_intervals'][p]['sd'] for v in result['variants'].values());upper=max(v['simultaneous_95_intervals'][p]['estimate']+np.sqrt(cutoff)*v['simultaneous_95_intervals'][p]['sd'] for v in result['variants'].values());assert abs(lower-result['robust']['coordinate_support_hull'][p]['lower'])<1e-12;assert abs(upper-result['robust']['coordinate_support_hull'][p]['upper'])<1e-12
    out={'status':'IMPLEMENTATION_AND_FINITE_ASSERTION_VERIFIED_CONDITIONAL','assertion_tested':__doc__,'baseline':result['baseline'],'candidate_implementation':result['implementation'],'reviewer_script_sha256':hashfile(Path(__file__)),'requested_runtime':{'model':'inherited parent setting','reasoning_effort':'inherited parent setting'},'observed_runtime':{'model':'UNKNOWN','reasoning_effort':'UNKNOWN'},'argv':[sys.executable, *sys.argv],'execution_kind':'deterministic numpy/scipy replay of independent numerical oracle','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'domain':{'N':len(z),'models':list(extra),'carrier_rows':32,'parameters':11,'mc_n':nsim,'mc_seed':9345081},'inputs_before':before,'inputs_after':{str(p):hashfile(p) for p in inputs},'checks':report,'distance_integrator_relative_error_vs_quad_at_13_quantiles':rel(approxchi,truechi),'findings':[],'review_conclusions':{'blocking_end_to_end_defects':0,'parameter_model':'eta = nuisance + g n.V + n.dH + n.K.n; V in km/s; dH and STF5 kappa dimensionless log-H coefficients','ablation':'same 32x11 response, only dipole/STF cross covariance removed; estimator error covariance is B C_full B.T','coverage':'conditional Gaussian calibration, not empirical survey coverage or validation of true covariance','union':'finite union of common-target ellipsoids; valid at nominal level if at least one listed fixed-Gaussian model is valid; max modelwise p needs no independence','test_distinction':'max_wald_p=0.01534 tests 11 parameter coefficients zero; max_null_p=0.11221 tests all 32 compressed mean rows zero; no contradiction','cache_reuse':'pinned code/input/cache and numerical operator/carrier reproduction; original byte fingerprint mismatch explicitly retained; no exact-byte replay claim','allowed_repair':'independently inspected r54_tensor_five_view change only rejects invalid finite-MC count inputs; extraction/STF/GLS code unchanged'},'limitations':['No independent raw pair sum or cosmic-model validation; original pinned cached body inherited.','Fixed covariance Gaussian coverage only; covariance/selection misspecification and model-search multiplicity are not calibrated.','Operator bytes differ from stored original fingerprints; numerical reproduction is distinct from exact replay.','Direct WLS normal equations used only as independent bounded cross-check; production uses QR.'],'elapsed_seconds':time.monotonic()-t0}
    assert out['inputs_before']==out['inputs_after']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'seconds':out['elapsed_seconds'],'max_wald_p':maxp,'distance_quad_rel':out['distance_integrator_relative_error_vs_quad_at_13_quantiles']}))


def check_axis_diagnostics(root: Path, output: Path) -> dict:
    """Referee repair M1: recompute D1 (block Wald), D2 (principal frame of K) and D4 (fixed-axis contrasts) of
    RESULTS/AXIS_DIAGNOSTICS.json from the committed fit with code written here: the STF basis is written out from its
    definition (orthonormal, trace-free, symmetric; same convention as R54), Galactic coordinates from the J2000 pole
    (RA 192.85948, Dec 27.12825) and the longitude of the celestial pole (122.93192 deg). No candidate function is called."""
    pkg = root / R58_RELATIVE
    fit_doc = json.loads((pkg / "RESULTS/OWNED_TENSOR_RESULT.json").read_text())
    diag = json.loads((pkg / "RESULTS/AXIS_DIAGNOSTICS.json").read_text())
    s2, s6 = 1 / np.sqrt(2.0), 1 / np.sqrt(6.0)
    basis = np.array([[[s2, 0, 0], [0, -s2, 0], [0, 0, 0]], [[s6, 0, 0], [0, s6, 0], [0, 0, -2 * s6]],
                      [[0, s2, 0], [s2, 0, 0], [0, 0, 0]], [[0, 0, s2], [0, 0, 0], [s2, 0, 0]], [[0, 0, 0], [0, 0, s2], [0, s2, 0]]])
    gram = np.einsum("aij,bij->ab", basis, basis)
    assert np.allclose(gram, np.eye(5)) and np.allclose(np.einsum("aii->a", basis), 0)
    ra_p, dec_p, l_ncp = np.radians(192.85948), np.radians(27.12825), np.radians(122.93192)

    def lb(v):
        v = np.asarray(v, float) / np.linalg.norm(v)
        ra, dec = np.arctan2(v[1], v[0]), np.arcsin(np.clip(v[2], -1, 1))
        sb = np.sin(dec) * np.sin(dec_p) + np.cos(dec) * np.cos(dec_p) * np.cos(ra - ra_p)
        y = np.cos(dec) * np.sin(ra - ra_p)
        x = np.sin(dec) * np.cos(dec_p) - np.cos(dec) * np.sin(dec_p) * np.cos(ra - ra_p)
        return [float(np.degrees(l_ncp - np.arctan2(y, x)) % 360.0), float(np.degrees(np.arcsin(np.clip(sb, -1, 1))))]

    def angdist(a, b):           # headless angular distance in degrees between two (RA, Dec) or (l, b) pairs
        a, b = np.radians(a), np.radians(b)
        c = np.sin(a[1]) * np.sin(b[1]) + np.cos(a[1]) * np.cos(b[1]) * np.cos(a[0] - b[0])
        return float(np.degrees(np.arccos(min(1.0, abs(c)))))

    c95 = stats.chi2.ppf(0.95, 11)
    report, worst = {}, {"wald_rel": 0.0, "p_abs": 0.0, "eig_abs": 0.0, "axis_deg": 0.0, "lb_deg": 0.0, "contrast_rel": 0.0}
    for m, var in diag["variants"].items():
        fit = fit_doc["variants"][m]["fit"]
        a, cov = np.array(fit["estimate"], float), np.array(fit["covariance"], float)
        for name, sl in (("V", slice(0, 3)), ("dH", slice(3, 6)), ("kappa", slice(6, 11))):
            w = float(a[sl] @ linalg.solve(cov[sl, sl], a[sl], assume_a="pos"))
            got = var["D1_block_wald"][name]
            worst["wald_rel"] = max(worst["wald_rel"], abs(w - got["wald"]) / w)
            worst["p_abs"] = max(worst["p_abs"], abs(stats.chi2.sf(w, sl.stop - sl.start) - got["p"]))
        k = np.einsum("a,aij->ij", a[6:], basis)
        evals, evecs = linalg.eigh(k)
        worst["eig_abs"] = max(worst["eig_abs"], float(np.max(np.abs(evals - var["D2_principal_frame"]["eigenvalues"]))))
        for i, ax in enumerate(("neg", "mid", "pos")):
            v = evecs[:, i]
            radec = [float(np.degrees(np.arctan2(v[1], v[0])) % 360.0), float(np.degrees(np.arcsin(v[2])))]
            worst["axis_deg"] = max(worst["axis_deg"], angdist(radec, var["D2_principal_frame"][ax]["ra_dec"]))
            worst["lb_deg"] = max(worst["lb_deg"], angdist(lb(v), var["D2_principal_frame"][ax]["l_b"]))
        for r, got in var["D4_fixed_axis_contrasts"].items():
            n = np.array(diag["reference_axes"][r]["icrs_unit"], float)
            c = np.r_[np.zeros(6), np.einsum("i,aij,j->a", n, basis, n)]
            est, sd = float(c @ a), float(np.sqrt(c @ cov @ c))
            exp = [est, sd, est - np.sqrt(c95) * sd, est + np.sqrt(c95) * sd]
            obs = [got["estimate"], got["sd"], *got["simultaneous_95"]]
            worst["contrast_rel"] = max(worst["contrast_rel"], max(abs(x - y) / max(abs(sd), 1e-300) for x, y in zip(exp, obs)))
        report[m] = "checked"
    # the M87 reference axis from its catalogue coordinates, and the Galactic transform on the Galactic pole itself
    m87 = np.array(diag["reference_axes"]["M87"]["ra_dec"], float)
    assert angdist(m87, [187.7059308, 12.39112326]) < 1e-9
    assert abs(lb([np.cos(dec_p) * np.cos(ra_p), np.cos(dec_p) * np.sin(ra_p), np.sin(dec_p)])[1] - 90.0) < 1e-6
    tol = {"wald_rel": 1e-9, "p_abs": 1e-12, "eig_abs": 1e-12, "axis_deg": 1e-6, "lb_deg": 1e-3, "contrast_rel": 1e-9}
    ok = all(worst[k] <= tol[k] for k in tol)
    out = {"schema": "htt.r58.axis_diagnostics_independent_check/1", "status": "D1_D2_D4_INDEPENDENTLY_REPRODUCED" if ok else "MISMATCH",
           "max_deviation": worst, "tolerance": tol, "variants": report,
           "inputs_sha256": {p: hashlib.sha256((pkg / p).read_bytes()).hexdigest() for p in ("RESULTS/OWNED_TENSOR_RESULT.json", "RESULTS/AXIS_DIAGNOSTICS.json")},
           "note": "lb tolerance reflects the rounded published J2000 pole constants used here versus the R_I2G matrix of the candidate"}
    output.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    if not ok:
        raise SystemExit(f"axis diagnostics differ from the independent recomputation: {worst}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Repository containing the pinned R54 source files and inputs.")
    parser.add_argument("--results", type=Path,
                        help="Directory with OWNED_TENSOR_RESULT.json and OWNED_TENSOR_CARRIERS.npz; defaults to root/R58/RESULTS.")
    parser.add_argument("--output", type=Path,
                        help="Review JSON path; defaults to root/R58/REVIEW/DATA_INDEPENDENT_REPLAY.json.")
    parser.add_argument("--candidate-root", type=Path,
                        help="Separate candidate source root for isolated patch validation; defaults to --root.")
    parser.add_argument("--axis-diagnostics", type=Path, metavar="OUTPUT",
                        help="Only recompute D1, D2 and D4 of RESULTS/AXIS_DIAGNOSTICS.json independently and write the check to OUTPUT.")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.axis_diagnostics is not None:
        print(json.dumps(check_axis_diagnostics(root, args.axis_diagnostics)["max_deviation"]))
        return
    results = args.results if args.results is not None else root / R58_RELATIVE / "RESULTS"
    output = args.output if args.output is not None else root / R58_RELATIVE / "REVIEW/DATA_INDEPENDENT_REPLAY.json"
    check(root, results, output, args.candidate_root if args.candidate_root is not None else root)


if __name__ == "__main__":
    main()
