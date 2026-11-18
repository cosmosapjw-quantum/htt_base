"""P1 R69 follow-up: exact STF morphology and CF4 angular geometry (read-only inputs).
No physical shear/tilt inference, no calibrated cosmic null.
Run from htt_base root:
  PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R69_P1_FIVEVIEW_PHYSICS_LOOP2_20261119/verify_physics.py
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.integrate import quad
from scripts.r68.fiveview_geometry import stf_matrix, stf_shape

RAW=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
E=np.array([stf_matrix(np.eye(5)[i]) for i in range(5)])
K0=np.array([-.012703128010752934,-.019952470814724125,-.00020715995373952114,
              .006235564252596576,.0008323006667775552])

def exact_area(S):
    """Solid-angle area of n^T S n>0 from eigenvalues, not source occupancy."""
    l1,l2,l3=np.linalg.eigvalsh(S)
    if not (l1<0 and l3>0 and abs(l1+l2+l3)<1e-10*max(abs(l1),abs(l3))):
        raise ValueError("nonzero STF with + and - eigenvalues required")
    ta=np.sqrt(-l1/(l3-l1))
    if abs(l2-l1)<1e-12*max(abs(l1),abs(l3)):
        return float(1-ta)
    tb=np.sqrt(max(0.,-l2/(l3-l2))) if l2<0 else 0.
    def frac(t):
        den=(l2-l1)*(1-t*t)
        nom=l2*(1-t*t)+l3*t*t
        if den<=0:return 1.
        ratio=np.clip(nom/den,0.,1.)
        return 2/np.pi*np.arcsin(np.sqrt(ratio))
    value,error=quad(frac,tb,ta,epsabs=5e-12,epsrel=5e-12,limit=300)
    return float(1-ta+value)

def read_cf4():
    rows=[]
    for line in RAW.open():
        try:
            ident=int(line[:7]);dist=float(line[21:26]);l=np.deg2rad(float(line[101:109]));b=np.deg2rad(float(line[110:118]))
            if np.isfinite(dist+l+b) and dist>0:
                n=[np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)]
                rows.append((ident,dist,*n))
        except (ValueError,IndexError):pass
    a=np.array(rows,float)
    assert a.shape==(38053,5),a.shape
    return a

def gal_to_icrs(n):
    from astropy.coordinates import SkyCoord
    from astropy import units as u
    ll=np.arctan2(n[:,1],n[:,0])
    bb=np.arcsin(np.clip(n[:,2],-1,1))
    coord=SkyCoord(l=ll*u.rad,b=bb*u.rad,frame="galactic").icrs
    ra=coord.ra.radian;dec=coord.dec.radian
    return np.stack([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)],axis=1)

def area_by_region(a,S,axis=np.array([0.,0.,1.])):
    n_gal=a[:,2:];n_icrs=gal_to_icrs(n_gal)
    q=np.einsum("ni,ij,nj->n",n_icrs,S,n_icrs)
    out=[]
    for lo,hi in [(0,40),(40,80),(80,140),(140,220),(220,400),(400,np.inf),(40,400)]:
        m=(a[:,1]>=lo)&(a[:,1]<hi);pos=n_gal@axis>0
        both=np.mean(q[m]>0)
        plus=np.mean(q[m&pos]>0) if np.any(m&pos) else None
        minus=np.mean(q[m&~pos]>0) if np.any(m&~pos) else None
        out.append(dict(band_Mpc=[lo,None if not np.isfinite(hi) else hi],n=int(np.sum(m)),
                        F_sample=float(both),F_plus=None if plus is None else float(plus),
                        F_minus=None if minus is None else float(minus),
                        F_hemisphere_gap=None if plus is None or minus is None else float(plus-minus)))
    return out

def geometry_schur(a,lo1,hi1,lo2,hi2):
    def A(lo,hi):
        nn=gal_to_icrs(a[(a[:,1]>=lo)&(a[:,1]<hi),2:])
        B=np.einsum("ni,aij,nj->na",nn,E,nn)
        return B.T@B, len(nn)
    A1,n1=A(lo1,hi1);A2,n2=A(lo2,hi2)
    eff=np.linalg.inv(np.linalg.inv(A1)+np.linalg.inv(A2))
    eff_alt=A1-A1@np.linalg.solve(A1+A2,A1)
    np.testing.assert_allclose(eff,eff_alt,rtol=4e-13,atol=4e-10)
    eig=np.linalg.eigvalsh(eff)
    assert eig[0]>0
    return {"bands":[[lo1,hi1],[lo2,hi2]],"n":[n1,n2],
        "unit_delta_response_eigenvalues":eig.tolist(),
        "unit_delta_response_condition":float(np.sqrt(eig[-1]/eig[0])),
        "calibration_profile":"one shared five-component angular calibration across the two bins; independent noise and homoscedastic weights; g1-g2=1 formal normalization",
        "physical_response_g_z":"UNQUALIFIED, no actual Fisher/posterior"}

def main():
    S=stf_matrix(K0)
    chi=float(stf_shape(S)["signed_chi"])
    f0=exact_area(S)
    np.testing.assert_allclose(f0,0.52362060546875,atol=5e-4)
    l=np.linalg.eigvalsh(S)
    assert abs(np.trace(S))<1e-14
    Saxis=np.diag([-1.,-1.,2.]);Santi=-Saxis
    np.testing.assert_allclose(exact_area(Saxis),1-1/np.sqrt(3),atol=1e-11)
    np.testing.assert_allclose(exact_area(Santi),1/np.sqrt(3),atol=1e-11)
    np.testing.assert_allclose(exact_area(np.diag([-1,0,1])),.5,atol=1e-11)
    rng=np.random.default_rng(42)
    errors=[]
    for _ in range(8):
        X=rng.normal(size=(3,3));A=(X+X.T)/2;A-=np.eye(3)*np.trace(A)/3
        if np.linalg.norm(A)<1e-3: continue
        np.testing.assert_allclose(exact_area(A)+exact_area(-A),1,atol=3e-10)
    asymptotic=[]
    for delta in [1e-2,1e-3,1e-4,1e-5]:
        Sdelta=np.diag([-1.,delta,1-delta])
        fd=exact_area(Sdelta)
        chief=float(stf_shape(Sdelta)["signed_chi"])
        kappa=(fd-.5)/delta
        asymptotic.append({"delta":delta,"chi":chief,"F":fd,
                           "slope_F_delta_over_log":kappa/np.log(1/delta),
                           "expected_limit_1_over_2pi":1/(2*np.pi)})
    a=read_cf4()
    sample=area_by_region(a,S)
    F2=sample[-1]["F_sample"]
    schur=geometry_schur(a,40,80,80,140)
    schur2=geometry_schur(a,80,140,140,220)
    out={"schema":"htt.r69.p1_physical_explanation_morphology/1",
        "source":"CF4 original table4 fixed-width raw Galactic group coordinates; transformed with Astropy to ICRS for K0",
        "raw_input_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "raw_rows":len(a),"K0_status":"R62 actual apparent response STF5, NOT physical GR shear",
        "K0_STF5":K0.tolist(),"K0_chi":chi,"K0_eigenvalues":l.tolist(),
        "K0_fullsky_intrinsic_positive_area":f0,
        "K0_CF4_unweighted_geometry_occupancy":sample,
        "K0_CF4_40_400_sample_minus_fullsky":F2-f0,
        "chi_zero_saddle_asymptotic":asymptotic,
        "two_depth_shape_calibration_schur": [schur,schur2],
        "tests":"exact integral and axial/symmetric limits, sign inversion, Schur equivalent forms",
        "physical_inference":"NOT MADE; no source-specific likelihood/covariance, full-sky physical sigma or z response supplied"}
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return out

if __name__=="__main__":
    main()
