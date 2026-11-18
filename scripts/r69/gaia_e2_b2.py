"""R69 actual Gaia proper motion E1/B1/E2/B2 tangent-field analysis.

This fits geometric VSH-like *unnormalized physical templates* P_n sigma n,
n x sigma n, observer acceleration/glide and reference frame spin. It does not
establish a cosmological Bianchi shear, unlike source/optical-response-specific
Gaia papers. Real data, fixed per-source astrometric covariance only;
systematic patch covariance is a diagnostic rather than official calibration.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.stats import chi2
from scripts.r68.fiveview_geometry import E,stf_matrix,stf_shape
from scripts.r67.gaia_frame import accumulate


def templates(ra_rad,dec_rad):
    ra=np.asarray(ra_rad,float);dec=np.asarray(dec_rad,float)
    cr,sr=np.cos(ra),np.sin(ra)
    cd,sd=np.cos(dec),np.sin(dec)
    n=np.column_stack((cd*cr,cd*sr,sd))
    era=np.column_stack((-sr,cr,np.zeros(len(ra))))
    edec=np.column_stack((-sd*cr,-sd*sr,cd))
    Tn=np.einsum("aij,nj->nai",E,n)
    B=np.empty((len(ra),2,16))
    B[:,0,:3]=era;B[:,1,:3]=edec
    B[:,0,3:6]=np.cross(n,era);B[:,1,3:6]=np.cross(n,edec)
    B[:,0,6:11]=np.einsum("ni,nai->na",era,Tn)
    B[:,1,6:11]=np.einsum("ni,nai->na",edec,Tn)
    MTn=np.cross(n[:,None,:],Tn)
    B[:,0,11:16]=np.einsum("ni,nai->na",era,MTn)
    B[:,1,11:16]=np.einsum("ni,nai->na",edec,MTn)
    return n,B


def prepare(z,subset="all"):
    ra,dec=np.deg2rad(np.asarray(z["ra"],float)),np.deg2rad(np.asarray(z["dec"],float))
    y1,y2=np.asarray(z["pmra"],float),np.asarray(z["pmdec"],float)
    e1,e2=np.asarray(z["pmra_error"],float),np.asarray(z["pmdec_error"],float)
    rho=np.asarray(z["pmra_pmdec_corr"],float)
    valid=np.isfinite(ra)&np.isfinite(dec)&np.isfinite(y1)&np.isfinite(y2)&np.isfinite(e1)&np.isfinite(e2)&np.isfinite(rho)&(e1>0)&(e2>0)&(np.abs(rho)<.999)
    qual=(np.asarray(z["ruwe"],float)<1.4)&(np.asarray(z["visibility_periods_used"])>=8)&(~np.asarray(z["duplicated_source"],bool))
    return ra,dec,y1,y2,e1,e2,rho,valid,qual


def fit_case(a):
    F=a["F"];b=a["score"];beta=np.linalg.solve(F,b)
    cov=np.linalg.inv(F)
    eig=np.linalg.eigvalsh(F)
    groups={"E1":beta[:3],"B1":beta[3:6],"E2":beta[6:11],"B2":beta[11:]}
    def wald(indices):
        sub=np.asarray(indices)
        c=cov[np.ix_(sub,sub)]
        v=beta[sub]
        return float(v@np.linalg.solve(c,v))
    stf=stf_matrix(beta[6:11])
    shape=stf_shape(stf)
    # Physical calibration if one (incorrectly) interpreted homogeneous local
    # affine cosmic shear: this is only a diagnostic scale, not measured sigma.
    masyr_to_s=1e-3*np.pi/(180*3600*31557600.)
    H70=70000/(1e6*3.085677581491367e16)
    return {"n_sources":int(a["N"]),
            "rank":int(np.linalg.matrix_rank(F)),
            "F_condition":float(eig.max()/eig.min()),
            "coefs_microasyr":(beta*1000).tolist(),
            "formal_errors_microasyr":(1000*np.sqrt(np.diag(cov))).tolist(),
            "groups_amplitude_microasyr":{k:float(np.linalg.norm(v)*1000) for k,v in groups.items()},
            "E2_shape_chi":float(shape["signed_chi"]),
            "E2_shape_discriminant_masyr6":float(shape["discriminant"]),
            "E2_eigenvalues_microasyr":(np.linalg.eigvalsh(stf)*1000).tolist(),
            "H0_fiducial_s_inv":H70,
            "E2_affine_local_sigma_over_H70_if_misinterpreted":float(np.linalg.norm(beta[6:11])*masyr_to_s/H70),
            "nominal_within_fixed_Gaussian":{
                "E2_Wald5":wald(np.arange(6,11)),
                "B2_Wald5":wald(np.arange(11,16)),
                "E2_p_naive":float(chi2.sf(wald(np.arange(6,11)),5)),
                "B2_p_naive":float(chi2.sf(wald(np.arange(11,16)),5)),
                "joint_E2B2_Wald10":wald(np.arange(6,16))},
            "chi2_per_dof_working":float((a["chisq"]-beta@b)/(2*a["N"]-16)),
            "formal_cov_microasyr2":(cov*1e6).tolist()}


def run(input_path:Path,out:Path,chunk=100000):
    from astropy.io import fits
    import healpy as hp
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    names=("all","quality","quality_north","quality_south")
    accum={k:{"F":np.zeros((16,16)),"score":np.zeros(16),"chisq":0.,"N":0} for k in names}
    with fits.open(input_path,memmap=True) as f:
        T=f[1].data
        for i in range(0,len(T),chunk):
            z=T[i:i+chunk]
            ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(z)
            if not np.any(valid):continue
            _,B=templates(ra[valid],dec[valid])
            yy=np.column_stack([y1[valid],y2[valid]])
            e1,e2,rho=e1[valid],e2[valid],rho[valid]
            # All/quality subsets on valid rows
            q=qual[valid];decv=dec[valid]
            masks={"all":np.ones(np.sum(valid),bool),"quality":q,
                   "quality_north":q&(decv>=0),"quality_south":q&(decv<0)}
            for k,m in masks.items():
                if not np.any(m):continue
                FF,score,c=accumulate(B[m],yy[m],e1[m],e2[m],rho[m])
                a=accum[k];a["F"]+=FF;a["score"]+=score;a["chisq"]+=c;a["N"]+=int(np.sum(m))
    fits_raw={k:fit_case(v) for k,v in accum.items()}
    # Two-stage source-wise score-> sky-patch residual sandwich, 12*? not bootstrap.
    C=np.linalg.inv(accum["quality"]["F"])
    beta=np.array(fits_raw["quality"]["coefs_microasyr"])/1000
    score_p=np.zeros((192,16))
    with fits.open(input_path,memmap=True) as f:
        T=f[1].data
        for i in range(0,len(T),chunk):
            z=T[i:i+chunk]
            ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(z)
            m=valid&qual
            if not np.any(m):continue
            _,B=templates(ra[m],dec[m])
            yy=np.column_stack([y1[m],y2[m]])
            resid=yy-np.einsum("nij,j->ni",B,beta)
            e1,e2,rho=e1[m],e2[m],rho[m]
            inv=1/(1-rho*rho)
            w0=inv*(resid[:,0]/e1**2-rho*resid[:,1]/(e1*e2))
            w1=inv*(resid[:,1]/e2**2-rho*resid[:,0]/(e1*e2))
            sourcescore=B[:,0,:]*w0[:,None]+B[:,1,:]*w1[:,None]
            pidx=hp.ang2pix(4,np.pi/2-dec[m],ra[m]%(2*np.pi))
            for j in range(16):
                score_p[:,j]+=np.bincount(pidx,weights=sourcescore[:,j],minlength=192)
    Cpatch=C@score_p.T@score_p@C
    fits_raw["quality"]["spatial_patch_192_std_microasyr"]=(1000*np.sqrt(np.maximum(0,np.diag(Cpatch)))).tolist()
    fits_raw["quality"]["spatial_patch_192_cov_microasyr2"]=(Cpatch*1e6).tolist()
    fits_raw["quality"]["spatial_patch_description"]="Exploratory 192 HEALPix sky-region score sandwich, not selection/scanning-law calibrated covariance"
    result={"schema":"htt.r69.gaia_full_EB1_EB2/1",
            "actual_input":str(input_path),
            "actual_input_sha256":hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "experiment":"per-source pmRA*=mu_alpha cos delta and pmDec, ICRS frame",
            "template_convention":"E1=P_n vector, B1=Omega cross n, E2=P_n STF n, B2=n cross STF n; amplitude in mas/year, no VSH norm rescaling",
            "physical_scope":"leading Euclidean local-affine screen-template only; cosmological source proper motion needs redshift-dependent null-Jacobi/observer light cone transfer",
            "results":fits_raw,
            "nonclaims":["No direct cosmological shear, vorticity, global tilt or Bianchi-family detection",
                        "No calibrated astrophysical p-values without Gaia scanning/AGN structure and source-redshift selection",
                        "H0=70 km/s/Mpc used only to demonstrate physical-scale mismatch"]}
    (out/"GAIA_E1B1E2B2.json").write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({k:{"N":v["n_sources"],"Fcond":v["F_condition"],
                         "amps":v["groups_amplitude_microasyr"],
                         "chi_E2":v["E2_shape_chi"],
                         "E2_H70_naive":v["E2_affine_local_sigma_over_H70_if_misinterpreted"],
                         "nominal":v["nominal_within_fixed_Gaussian"]}
         for k,v in fits_raw.items()},indent=2))


if __name__=="__main__":
    root=Path(__file__).resolve().parents[2]
    run(Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits"),
        root/"docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS")
