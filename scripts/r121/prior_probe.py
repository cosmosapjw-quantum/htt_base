"""Reanalyze actual R120 signed results without rerunning the producer."""
import json, numpy as np
from scripts.r120.analyze_scan import get_scan,quotient
def main():
    _,b=get_scan("base");_,f=get_scan("fine")
    coords=["log_k","log_A","u","log_shear"];out={}
    for n in ("VIh","VIIh"):
        _,q04=quotient(b,n,.04,coords);_,q02=quotient(b,n,.02,coords);_,qf=quotient(f,n,.02,coords)
        d=np.array([1.,1.,.001 if n=="VIIh" else 1.,1.])
        m=qf["projected"]*d
        w=(q04["projected"]-q02["projected"])*d;t=(q02["projected"]-qf["projected"])*d
        x,y,z=b[n],b[n+"_negative_shear"],b[n+"_zero_shear"]
        odd=(x-y)/2;even=(x+y)/2-z
        np.testing.assert_allclose(z+odd+even,x,rtol=1e-10,atol=1e-16)
        np.testing.assert_allclose(z-odd+even,y,rtol=1e-10,atol=1e-16)
        sig=np.linalg.svd(m,compute_uv=False)
        err=max(np.linalg.norm(w,2),np.linalg.norm(t,2))
        out[n]={"scale":d.tolist(),"scaled_singular":sig.tolist(),"scaled_width_op":float(np.linalg.norm(w,2)),"scaled_time_op":float(np.linalg.norm(t,2)),"empirical_count":int(np.sum(sig>err)),
          "absolute":{"zero":float(np.linalg.norm(z)),"odd":float(np.linalg.norm(odd)),"even":float(np.linalg.norm(even))}}
    print(json.dumps(out,indent=2,allow_nan=False))
if __name__=="__main__":main()
