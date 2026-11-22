"""R98 seven conditional cross-route computations on signed products."""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation
from scripts.r69.gaia_e2_b2 import templates
from scripts.r90.sf_attribution import STF, codazzi_stf
from scripts.r98 import bianchi_history as bh
from scripts.r98 import cf4_p1 as cf
from bass.transport.general_bianchi_transfer import map_from_scalar_alm
from bass.background.convention_bridge import exact_momentum_divergence

DOC = cf.OUT.parent
SKY_KEY = "alm_rows_ell_ascending_entries_m_minus_ell_to_plus_ell_Re_Im"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gram_info(X,w):
    Xw = X*np.sqrt(w[:,None])
    A = Xw / np.linalg.norm(Xw,axis=0)
    eig = np.linalg.eigvalsh(A.T@A)
    return {"eigenvalues":eig.tolist(),"rank":int(sum(eig>1e-10))}


def cf4_routes(result):
    H = cf.r95._load_h03()
    ids,mu,emu,cz,v,_,_,_,n,_ = cf.catalog()
    z = cz/cf.C
    rows = np.flatnonzero((z>=.01)&(z<=.10))
    rows = rows[np.argsort(ids[rows])]
    ref = H.source(cf.r95.SELECT)
    if not np.array_equal(ids[rows],ref.ids) or len(rows)!=35970:
        raise ValueError("CF4 identity mismatch")
    n,mu,emu,cz,v = [v0[rows] for v0 in (n,mu,emu,cz,v)]
    z = cz/cf.C
    X = H.velocity_design(np.ones(len(z)),n)
    y = np.log(v/cf.HREF)-cf.MAG*(mu-25.)
    w_sigma = cf.log_sigma(v,emu)
    fitted = np.array(result["fit"]["selected_log_coefficients_4x9"])
    R = cz/70.  # working radial chart in Mpc
    U = 100*n/R[:,None]
    extended = np.column_stack((X,U))
    fixed = np.column_stack((X,n))
    leak,radial = [],[]
    for j,center in enumerate(H.CENTERS):
        w = H.window(z,w_sigma,center)
        weight = np.sqrt(w)
        WX = weight[:,None]*X
        beta = np.linalg.lstsq(WX,weight*y,rcond=None)[0]
        if not np.allclose(beta,fitted[j],rtol=0,atol=2e-12):
            raise ValueError("R98 corrected log fits disagree")
        restricted = np.linalg.lstsq(WX[:,:4],weight*y,rcond=None)[0]
        M = np.linalg.lstsq(WX[:,:4],WX[:,4:],rcond=None)[0]
        impact = M@beta[4:]
        leak.append(dict(z_center=center,operator_4x5=M,observed_dropped_STF_shift=impact,
                         closed_refit_error=np.max(abs(restricted-beta[:4]-impact))))
        WX12 = extended*weight[:,None]
        beta12 = np.linalg.lstsq(WX12,y*weight,rcond=None)[0]
        projection = np.linalg.lstsq(WX,weight[:,None]*U,rcond=None)[0]
        radial.append(dict(z_center=center,rank9=gram_info(X,w),rank12=gram_info(extended,w),
                           fixed_radius_100_Mpc=gram_info(fixed,w),observed_log_fit_12=beta12,
                           omitted_radial_coefficient_shift=projection@beta12[9:],
                           identity_error=np.max(abs(beta-beta12[:9]-projection@beta12[9:])),
                           weighted_residual_gain=np.linalg.norm(weight*(y-X@beta))**2-
                           np.linalg.norm(weight*(y-extended@beta12))**2))
    return (dict(n=len(rows),basis=result["definitions"]["angular_order"],windows=leak),
            dict(n=len(rows),radius_chart="cz_CMB / (70 km/s/Mpc); 100 Mpc / r observer dipole basis",
                 radial_range_Mpc=[R.min(),R.max()],windows=radial))


def moments(I,nh,w):
    I = np.asarray(I)
    if not np.all(np.isfinite(I)) or np.min(I)<=0:
        raise ValueError("positive finite intensity required")
    d = nh.reshape(-1,3)
    p = (I*w).ravel()
    p /= p.sum()
    m = p@d
    S = (d.T*p)@d
    V = S-np.outer(m,m)
    return m,S,V


def photon_route(result,n_gl=32):
    th,ph,nh,w = bh.r97.gl_sphere_grid(n_gl)
    out = {}
    for family,row in result["families"].items():
        arr = row["sky"]["T"][SKY_KEY]
        if len(arr)!=13 or any(len(a)!=2*l+1 for l,a in enumerate(arr)):
            raise ValueError("missing signed temperature harmonics")
        alm = {(l,m):complex(*pair) for l,vals in enumerate(arr) for m,pair in zip(range(-l,l+1),vals)}
        temp = 1+map_from_scalar_alm(alm,th,ph)
        if temp.min()<=0:
            raise ValueError("blackbody temperature must be positive")
        m,S,V = moments(temp**4,nh,w)
        out[family] = dict(min_T_over_T0=temp.min(),m_arrival=m,S=S,
                           trace_S=S.trace(),min_covariance_eigenvalue=np.linalg.eigvalsh(V)[0],
                           quadrupole_norm=np.linalg.norm(S-np.eye(3)/3))
    return out


def grouped_cmb(d):
    groups = {}
    for row in d["oof_by_cmb_id"].values():
        noise,fold,raw,ridge,diagonal,maxscore,dnll,diag_nll = row
        groups.setdefault(int(noise),[]).append((int(fold),dnll))
    if not all(len({r[0] for r in rows})==1 for rows in groups.values()):
        raise ValueError("noise group split across held-out folds")
    means = np.array([np.mean([v for _,v in rows]) for rows in groups.values()])
    return dict(pairs=sum(len(g) for g in groups.values()),noise_groups=len(groups),
                noise_group_balanced_mean_ridge_minus_raw_nll_nats=means.mean(),
                pair_weighted_mean_ridge_minus_raw_nll_nats=np.mean(
                    [v for rows in groups.values() for _,v in rows]),
                used_as_photon_moment_or_calibration=False)


def radio_route(d):
    _,_,nh,w = bh.r97.gl_sphere_grid(24)
    out = {}
    for survey,by_cut in d["surveys"].items():
        cuts = sorted(map(float,by_cut))
        counts = np.array([by_cut[str(u)]["n_sources"] for u in cuts])
        x = -np.gradient(np.log(counts),np.log(cuts))
        if np.any(x<=0):
            raise ValueError("nonpositive working count slope")
        entries = []
        for cut,slope in zip(cuts,x):
            src = by_cut[str(cut)]["models"]["NB1_4"]
            D = np.array(src["exact_fullsky_model_dipole"])
            beta = D/(2+1.75*slope)
            if beta@beta>=1:
                raise ValueError("superluminal working boost")
            doppler = np.sqrt(1-beta@beta)/(1-nh@beta)
            m,_,_ = moments(doppler**4,nh,w)
            exact = 4*beta/(3+beta@beta)
            entries.append(dict(cut_mJy=cut,x_working=slope,beta_working=beta,
                                model_arrival_direction_m=m,
                                analytic_difference_norm=np.linalg.norm(m-exact)))
        out[survey] = entries
    return out


def gaia_route(d):
    th,ph,_,w = bh.r97.gl_sphere_grid(16)
    _,template = templates(ph.ravel(),np.pi/2-th.ravel())
    Z = template[:,:,6:]
    gram = np.einsum("nci,ncj,n->ij",Z,Z,w.ravel()/(4*np.pi))
    result = {}
    cache = d["joint_160d_patch_covariance"]
    if sha(cache["cache_path"])!=cache["sha256"]:
        raise ValueError("Gaia patch statistics changed")
    with np.load(cache["cache_path"],allow_pickle=False) as f:
        names = f["names"].tolist()
        C = f["cov"]
        cf0 = names.index("crf3_all")
        for j,name in enumerate(names):
            idx = np.arange(16*j+6,16*j+16)
            old = np.arange(16*cf0+6,16*cf0+16)
            F = f[name+"__F"].sum(axis=0)[6:,6:]
            whiten = F / np.sqrt(np.outer(F.diagonal(),F.diagonal()))
            coeff = np.array(d["fits"][name]["coefs_microasyr"])[6:]
            cv = C[np.ix_(idx,idx)]+C[np.ix_(old,old)]-C[np.ix_(idx,old)]-C[np.ix_(old,idx)]
            diff = f["leave"][:,idx]-f["leave"][:,old]
            direct = 47/48*(diff-diff.mean(axis=0)).T@(diff-diff.mean(axis=0))
            result[name] = dict(n=d["fits"][name]["n_sources"],E2B2_microasyr=coeff,
                observed_weighted_gram_max_EB_abs_corr=np.max(abs(whiten[:5,5:])),
                crf3_all_contrast_cov_microasyr2=cv,shared_covariance_check_max=np.max(abs(cv-direct)))
    return dict(full_sky_mean_gram_10x10=gram,analytic_I_over_5_max_error=np.max(abs(gram-np.eye(10)/5)),
                source_census=d["source_row_census"],fits=result)


def codazzi_route():
    s = bh.early_state("VI_h")
    n0 = np.diag(s.algebra.n)
    a0 = s.algebra.a[0]
    rows=[]
    for scale in (.99,1.,1.01):
        A = np.array([a0*scale,0,0])
        # R49 q=-D.sigma for kappa=1, R90's n sign is reversed in this basis.
        M = np.stack([-exact_momentum_divergence(S,A,s.algebra.n) for S in STF],axis=1)
        direct = codazzi_stf(tuple(n0),A[0])
        transformed = codazzi_stf(tuple(-n0),A[0])
        rows.append(dict(h=A[0]**2/(n0[1]*n0[2]),rank=np.linalg.matrix_rank(M,tol=1e-12),
                         singular_values=np.linalg.svd(M,compute_uv=False),R90_same_n_difference=np.max(abs(M-direct)),
                         R90_flipped_n_difference=np.max(abs(M-transformed))))
    normal_flux=sum((p.to_projected_state().q for p in s.species_congruences),np.zeros(3))
    residual = exact_momentum_divergence(s.sigma_ab,s.algebra.a,s.algebra.n)+normal_flux
    return dict(near_exception=rows,actual_early_normal_flux=normal_flux,
                compensated_Codazzi_initial_norm=np.linalg.norm(residual),
                residual_covariance="needs joint law of geometry, shear and independent species flux")


def history_route():
    out = {}
    frame = Rotation.from_rotvec([.32,-.21,.11]).as_matrix()
    for family in ("I","V","VII_h","VI_h"):
        initial,t = bh.background(family,samples=161)
        tight = bh.r97.evolve_general_tilted_bianchi(initial,config=bh.r97.TiltedEvolutionConfig(
            N_start=bh.N_INITIAL,N_end=0.,n_eval=161,rtol=3e-13,atol=1e-18,constraint_abort_tol=1e-7))
        Sd = tight.sigma_ab_grid/tight.H_grid[:,None,None]
        Sd /= np.linalg.norm(Sd,axis=(1,2))[:,None,None]
        S=t.sigma_ab_grid / t.H_grid[:,None,None]
        sn=S/np.linalg.norm(S,axis=(1,2))[:,None,None]
        chi=np.sqrt(6)*np.trace(sn@sn@sn,axis1=1,axis2=2)
        rot=frame@sn@frame.T
        # Rank-one eigenprojectors cancel arbitrary eigenvector signs.
        ev,Q=np.linalg.eigh(sn)
        top=Q[:,:,-1]
        gap=ev[:,-1]-ev[:,-2]
        angles=np.arccos(np.clip(abs(top@top[0]),0,1))
        comm=sn[0]@sn-sn@sn[0]
        out[family]=dict(samples=len(S),source_chi_min_max=[chi.min(),chi.max()],minimum_top_spectral_gap=gap.min(),
                         largest_top_eigenline_angle_degrees=np.rad2deg(angles).max(),
                         minimum_shear_over_H=np.min(np.linalg.norm(S,axis=(1,2))),
                         tighter_ivp_max_normalized_tensor_difference=np.max(np.linalg.norm(sn-Sd,axis=(1,2))),
                         tighter_ivp_max_eigenline_difference_deg=np.max(np.rad2deg(np.arccos(np.clip(abs(
                            np.sum(top*np.linalg.eigh(Sd)[1][:,:,-1],axis=1)),0,1)))),
                         maximum_commutator_norm=np.linalg.norm(comm,axis=(1,2)).max(),
                         common_rotation_chi_error=np.max(abs(np.sqrt(6)*np.trace(rot@rot@rot,axis1=1,axis2=2)-chi)))
    return out


def compute():
    files = {k:DOC/(k+".json") for k in ("BIANCHI_HISTORY_RESULTS","CF4_P1_RESULTS","CMB_GROUPED_FULL_CACHE",
                                          "GAIA_FULL_SHARED_PATCH","RADIO_FULL_MODELS")}
    raw = {"CF4_table3":cf.r97.RAW_CF4/"table3.dat","CF4_table4":cf.r97.RAW_CF4/"table4.dat",
           "CF4_selected":cf.r95.SELECT,"implementation":Path(__file__)}
    raw.update({"Bianchi_solver":Path(bh.__file__),"CF4_solver":Path(cf.__file__),
                "R90_codazzi_basis":Path(__file__).resolve().parents[1]/"r90/sf_attribution.py",
                "Gaia_VSH_basis":Path(__file__).resolve().parents[1]/"r69/gaia_e2_b2.py"})
    before={k:sha(p) for k,p in {**files,**raw}.items()}
    inputs={k:json.loads(p.read_text()) for k,p in files.items()}
    c=inputs["CF4_P1_RESULTS"]
    for here,there in (("CF4_table3","table3.dat"),("CF4_table4","table4.dat"),("CF4_selected","selected")):
        if before[here]!=c["inputs"][there]["sha256"]:
            raise ValueError("CF4 parent fingerprint mismatch")
    r1,r7=cf4_routes(c)
    r2=photon_route(inputs["BIANCHI_HISTORY_RESULTS"])
    r2fine=photon_route(inputs["BIANCHI_HISTORY_RESULTS"],40)
    result={"schema":"r98.seven_cross_phy_routes.1","source_sha256":before,
            "PHY01":r1,"PHY02":{"conditional_bolometric_sky":r2,
               "max_abs_second_moment_32_vs_40":max(np.max(abs(r2[k]["S"]-r2fine[k]["S"])) for k in r2),
               "observed_CMB_distinct_experiment":grouped_cmb(inputs["CMB_GROUPED_FULL_CACHE"])},
            "PHY03":radio_route(inputs["RADIO_FULL_MODELS"]),"PHY04":gaia_route(inputs["GAIA_FULL_SHARED_PATCH"]),
            "PHY05":codazzi_route(),"PHY06":history_route(),"PHY07":r7,
            "physical_Q":None,"physical_Pi":None,"physical_F":None,"physical_GF":None,
            "scope":"conditional finite survey or model forward computations; models and observed catalogs have separate laws"}
    if before!={k:sha(p) for k,p in {**files,**raw}.items()}:
        raise RuntimeError("inputs changed")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    t=time.perf_counter()
    data=compute()
    data["elapsed_seconds"]=time.perf_counter()-t
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False,default=cf.json_default)+"\n")
    print(args.output,data["elapsed_seconds"])
