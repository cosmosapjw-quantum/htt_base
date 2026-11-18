"""Exploratory Gaia-CRF3 l=1 E/B vector-spherical-harmonic frame diagnostic.

RA axis is Gaia pmra*, not raw d(ra)/dt. ICRS orientation; no cosmological
vorticity inferred. Spatial cluster sandwich is a diagnostic, not a calibrated
Gaia DR3 large-angle systematic covariance.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np


def eb_design(ra_rad, dec_rad):
    x,y = np.asarray(ra_rad,float),np.asarray(dec_rad,float)
    c,s=np.cos(y),np.sin(y)
    n=np.column_stack([c*np.cos(x),c*np.sin(x),s])
    ra=np.column_stack([-np.sin(x),np.cos(x),np.zeros(len(x))])
    de=np.column_stack([-s*np.cos(x),-s*np.sin(x),c])
    B=np.empty((len(x),2,6))
    B[:,0,:3]=ra;B[:,1,:3]=de
    B[:,0,3:]=np.cross(n,ra)
    B[:,1,3:]=np.cross(n,de)
    return n,B


def accumulate(B, mu, e1, e2, corr):
    inv=1/(1-corr*corr)
    w00=inv/e1**2;w11=inv/e2**2;w01=-corr*inv/e1/e2
    v0=w00*mu[:,0]+w01*mu[:,1]
    v1=w01*mu[:,0]+w11*mu[:,1]
    score=np.einsum('ni,n->i',B[:,0,:],v0)+np.einsum('ni,n->i',B[:,1,:],v1)
    B0,B1=B[:,0,:],B[:,1,:]
    F=np.einsum('ni,nj,n->ij',B0,B0,w00)+np.einsum('ni,nj,n->ij',B1,B1,w11)
    F+=np.einsum('ni,nj,n->ij',B0,B1,w01)+np.einsum('ni,nj,n->ij',B1,B0,w01)
    chi=np.sum(mu[:,0]*v0+mu[:,1]*v1)
    return F,score,float(chi)


def finalize(F,score,chisq,N):
    beta=np.linalg.solve(F,score)
    C=np.linalg.inv(F)
    eig=np.linalg.eigvalsh(F)
    sigma=np.sqrt(np.diag(C))*1000  # mas/yr -> microarcsec/yr
    return {"n_sources":int(N),"rank":int(np.linalg.matrix_rank(F)),
            "fisher_condition":float(eig[-1]/eig[0]),
            "coefs_EB_masyr":beta.tolist(),
            "coefs_EB_microarcsecyr":(beta*1000).tolist(),
            "E_amplitude_microarcsecyr":float(np.linalg.norm(beta[:3])*1000),
            "B_amplitude_microarcsecyr":float(np.linalg.norm(beta[3:])*1000),
            "formal_marginal_sigma_microarcsecyr":sigma.tolist(),
            "chi2_per_degree_working":float((chisq-beta@score)/(2*N-6)),
            "formal_covariance_microarcsecyr2":(C*1e6).tolist()}


def run(root:Path,out:Path,chunk=100000):
    from astropy.io import fits
    import healpy as hp
    all_f={}
    sample=("all","quality","quality_north","quality_south")
    for key in sample:
        all_f[key]={"F":np.zeros((6,6)),"s":np.zeros(6),"chi":0., "N":0}
    # Clustered score and information in HEALPix patches (quality sample).
    pix=np.zeros((192,6));Fpix=np.zeros((192,6,6))
    with fits.open(root,memmap=True) as f:
        rows=f[1].data
        for start in range(0,len(rows),chunk):
            z=rows[start:start+chunk]
            ra,dec=np.deg2rad(np.asarray(z["ra"],float)),np.deg2rad(np.asarray(z["dec"],float))
            p1,p2=np.asarray(z["pmra"],float),np.asarray(z["pmdec"],float)
            e1,e2=np.asarray(z["pmra_error"],float),np.asarray(z["pmdec_error"],float)
            cor=np.asarray(z["pmra_pmdec_corr"],float)
            valid=(np.isfinite(ra)&np.isfinite(dec)&np.isfinite(p1)&np.isfinite(p2)&
                   np.isfinite(e1)&np.isfinite(e2)&np.isfinite(cor)&(e1>0)&(e2>0)&(np.abs(cor)<.999))
            quality=(np.asarray(z["ruwe"],float)<1.4)&(np.asarray(z["visibility_periods_used"])>=8)&(~np.asarray(z["duplicated_source"],bool))
            n,B=eb_design(ra,dec)
            mu=np.column_stack([p1,p2])
            sets={"all":valid,"quality":valid&quality,"quality_north":valid&quality&(dec>=0),"quality_south":valid&quality&(dec<0)}
            for key,mask in sets.items():
                if not np.any(mask):continue
                a=all_f[key];Fi,score,chi=accumulate(B[mask],mu[mask],e1[mask],e2[mask],cor[mask])
                a["F"]+=Fi;a["s"]+=score;a["chi"]+=chi;a["N"]+=int(mask.sum())
            # Pixel-level cluster influence; no per-source covariance beyond 2x2 is supplied.
            m=valid&quality
            if np.any(m):
                ip=hp.vec2pix(4,*n[m].T)
                for k in np.unique(ip):
                    sub=m.copy()
                    tmp=np.flatnonzero(m)
                    sub[:]=False
                    sub[tmp[ip==k]]=True
                    Fi,score,chi=accumulate(B[sub],mu[sub],e1[sub],e2[sub],cor[sub])
                    Fpix[k]+=Fi;pix[k]+=score
    results={k:finalize(x["F"],x["s"],x["chi"],x["N"]) for k,x in all_f.items() if x["N"]>0}
    f=all_f["quality"];C=np.linalg.inv(f["F"]);beta=np.asarray(results["quality"]["coefs_EB_masyr"])
    per_patch=pix-np.einsum("pij,j->pi",Fpix,beta)
    cluster_cov=C@per_patch.T@per_patch@C
    eig=np.linalg.eigvalsh(cluster_cov)
    results["quality"]["spatial_cluster_192_patch_sigma_microarcsecyr"]=(np.sqrt(np.maximum(0,np.diag(cluster_cov)))*1000).tolist()
    results["quality"]["spatial_cluster_cov_eigenvalue_min"]=float(eig[0])
    result={"schema":"htt.r67.gaia_frame_diagnostic/1","input":str(root),
            "data_source":"Gaia-CRF3, proper motions pmra* and pmdec; sourcewise covariance, not full spatial covariance",
            "results":results,"patch_count":192,
            "quality_selection":"RUWE<1.4, visibility_periods>=8, !duplicated_source, exploratory",
            "assumptions":["ICRS tangent frame; six E/B l=1 vectors, not matter velocity gradient", "Source-to-source independent statistical errors in Fisher, cluster proxy is only diagnostic", "Gaia frame definition/systematic large-angle correlations not modeled","AGN intrinsic motions not modeled","No cosmological omega, local-global tilt or observer velocity claimed"],
            "role":"Exploratory actual-fit observer-frame anchor diagnostic, to be compared with VLBA only after frame and proper-motion convention binding"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"GAIA_EB_FRAME.json").write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits"))
    p.add_argument("--out",type=Path,default=Path("docs/research_program/observational_publication_20261015/R67_SEVEN_AXIS_FUSION_20261118/RESULTS"))
    args=p.parse_args()
    r=run(args.input,args.out)
    print(json.dumps({k:{j:v[j] for j in ['n_sources','rank','E_amplitude_microarcsecyr','B_amplitude_microarcsecyr','fisher_condition']} for k,v in r['results'].items()}))
if __name__=="__main__":main()
