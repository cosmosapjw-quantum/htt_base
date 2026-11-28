"""Registered finite R122 chart; distinct table-only I oracle input."""
import math,json
from scripts.r121.plan import point
from scripts.r120.plan_grid import SHEAR

def make():
    p=[];base=[];fine=[]
    for tag,lam in (("025",.025),("035",.035),("045",.045)):
        for mark,f in (("pos",1),("zero",0),("neg",-1)):
            n=f"VI_l{tag}_{mark}"
            p.append(point(n,-1,.01*lam,.005*lam,0,[f*v for v in SHEAR],"crossover",lam=lam,shear_factor=f))
            base.append(n)
            if tag=="035":fine.append(n)
    for tag,eps in (("hi",1e-4),("lo",5e-5)):
        for mark,sgn in (("pos",1),("neg",-1)):
            n=f"I_{tag}_{mark}";v=sgn*eps
            p.append({"name":n,"N6":[0.]*6,"A3":[0.]*3,"shear6":[-.5*v,-.5*v,v,0.,0.,0.],"expected_type":"I","kind":"oracle","parameters":{"eps":v}})
            base.append(n)
            if tag=="lo":fine.append(n)
    p.append(point("VII_center",1,.01,.005,0,SHEAR,"tangent_center"));fine.append("VII_center")
    for c,j,w in (("log_k",0,.02),("log_A",1,.02),("u",2,.0005),("log_shear",3,.02),("log_shear",3,.01)):
        tag="0005" if j==2 else ("02" if w==.02 else "01")
        for mark,sgn in (("minus",-1),("plus",1)):
            q=[math.log(.01),math.log(.005),0.,0.];q[j]+=sgn*w
            n=f"VII_{c}_{tag}_{mark}"
            p.append(point(n,1,math.exp(q[0]),math.exp(q[1]),q[2],[math.exp(q[3])*v for v in SHEAR],"tangent",coordinate=c,width=w,side=sgn));fine.append(n)
    for r in p:r["recombination"]="table" if r["kind"]=="oracle" else "matched"
    return {"schema":"htt.r122.source_response/1","points":p,"base":base,"fine":fine,"base_steps":3200,"fine_steps":6400,
          "ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],"coordinates":["log_k","log_A","u","log_shear"],"scales":[1,1,.001,1],
          "scope":"finite registered runs, no observational likelihood"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
