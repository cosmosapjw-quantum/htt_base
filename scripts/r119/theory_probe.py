"""R119 R7 direct finite-geometry probe on historical native R114 output."""
import hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
REF=BASE/"R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C1_HARMONIC_LONG_ATLAS.json"
RAW=Path.home()/"Downloads/htt_r114/c1_atlas/runs"
OUT=BASE/"R119_NATIVE_CLASSIFICATION_INTAKE_20261128/R7.json"
PAIRS=("TT","TE","TB","EE","EB","BB")

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ref=json.loads(REF.read_text()); cases=ref["cases"]; norms={}; vecs={}; blocks={}; receipts={}
    for name,case in cases.items():
        path=RAW/name/"h32_s2000"
        expected=case["runs"]["h32_s2000"]["los_modes_sha256"]
        actual=digest(path/"los_modes.tsv")
        if actual!=expected: raise ValueError(f"{name} source SHA mismatch")
        data=np.loadtxt(path/"los_modes.tsv",skiprows=1)
        cl=np.loadtxt(path/"los_cl.tsv",skiprows=1)
        ell=np.repeat(np.arange(129),2*np.arange(129)+1)
        m=np.concatenate([np.arange(-l,l+1) for l in range(129)])
        assert data.shape==(129**2,20) and np.array_equal(data[:,:2],np.column_stack([ell,m]))
        assert np.isfinite(data).all() and np.isfinite(cl).all()
        a=data[:,2:8:2]+1j*data[:,3:8:2]
        ix=ell*(ell+1)-m
        err=np.max(np.abs(a[ix]-(-1.)**m[:,None]*a.conj()))
        assert np.allclose(a[ix],(-1.)**m[:,None]*a.conj(),rtol=2e-12,atol=1e-18)
        assert np.all(a[:4,1:]==0)
        assert np.array_equal(cl[:,0],np.arange(129))
        max_cl_error=0.
        for j,xy in enumerate(PAIRS):
            prod=a[:,"TEB".index(xy[0])]*a[:,"TEB".index(xy[1])].conj()
            assert np.allclose(prod,data[:,8+2*j]+1j*data[:,9+2*j],rtol=2e-12,atol=1e-24)
            c=np.bincount(ell,weights=prod.real)/(2*np.arange(129)+1)
            assert np.allclose(c,cl[:,j+1],rtol=2e-11,atol=1e-24)
            max_cl_error=max(max_cl_error,float(np.max(abs(c-cl[:,j+1]))))
        v=a[4:81]
        norm=float(np.linalg.norm(v)); norms[name]=norm
        receipts[name]={"los_modes_sha256":actual,"max_reality_error":float(err),"max_cl_abs_error":max_cl_error,"max_abs_gauss":case["runs"]["h32_s2000"]["max_abs_gauss_residual"]}
        if name!="FLRW" and norm>0:
            vecs[name]=v/norm
            blocks[name]=np.array([np.linalg.norm(v[l*l-4:(l+1)**2-4],axis=0) for l in range(2,9)]).ravel()/norm
    pairs=[]
    for i,x in enumerate(vecs):
        for y in list(vecs)[i+1:]:
            corr=np.clip(np.vdot(vecs[x],vecs[y]).real,0.,1.)
            ceiling=np.clip(blocks[x]@blocks[y],0.,1.)
            lo=float(np.sqrt(max(0.,1-ceiling**2))); hi=float(np.sqrt(max(0.,1-corr**2)))
            assert lo<=hi+2e-7
            pairs.append({"pair":[x,y],"block_lower":lo,"identity_upper":hi})
    q=np.diag([2.,-1.,-1.]); assert np.trace(q@q)==np.trace((-q)@(-q)) and np.trace(q@q@q)!=np.trace((-q)@(-q)@(-q))
    record={"scope":"full signed historical R114 LOS l<=128 checks; l=2..8 geometry-only fixed-frame bracket; no mask/no likelihood","source_sha256":digest(REF),"norms":norms,"receipts":receipts,"pairs":pairs,"counterexample_tr_Q3":[float(np.trace(q@q@q)),float(np.trace((-q)@(-q)@(-q)))]}
    OUT.write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"cases":len(receipts),"pairs":len(pairs),"FLRW_norm":norms["FLRW"],"closest_identity":sorted(pairs,key=lambda r:r["identity_upper"])[:5],"max_cl_error":max(r["max_cl_abs_error"] for r in receipts.values())},indent=2))
if __name__=="__main__":main()
