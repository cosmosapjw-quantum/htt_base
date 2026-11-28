"""Predeclared finite weak-geometry and near-balanced stencil."""
import json,math
from scripts.r120.plan_grid import SHEAR

def point(name,s,k,a,u,shear,kind,**parameters):
    return {"name":name,"N6":[0,k*math.exp(u),s*k*math.exp(-u),0,0,0],"A3":[a,0,0],
            "shear6":list(shear),"expected_type":"VI_h" if s<0 else "VII_h","kind":kind,
            "parameters":{"sign":s,"k":k,"A0":a,"u":u,"h":s*(a/k)**2,**parameters}}

def make():
    p=[];fine=[]
    for n,s in (("VI",-1),("VII",1)):
        for tag,lam in (("10",.1),("03",.03),("01",.01)):
            for mark,f in (("pos",1),("zero",0),("neg",-1)):
                name=f"{n}_l{tag}_{mark}"
                p.append(point(name,s,.01*lam,.005*lam,0,[f*v for v in SHEAR],"weak",lam=lam,shear_factor=f))
                if (s<0 and tag in ("03","01")) or (s>0 and tag=="01"):fine.append(name)
    for tag,w in (("0005",.0005),("001",.001),("002",.002)):
        for mark,sgn in (("minus",-1),("plus",1)):
            name=f"VII_u_{tag}_{mark}"
            p.append(point(name,1,.01,.005,sgn*w,SHEAR,"near_balanced",width=w,side=sgn))
            if tag=="0005":fine.append(name)
    for tag,amp in (("hi",1e-4),("lo",5e-5)):
        p.append(point("VII_tensor_"+tag,1,.01,.005,0,[0,amp,-amp,0,0,0],"tensor_seed",shear_amplitude=amp))
    fine.append("VII_tensor_lo")
    base=[x["name"] for x in p]
    p.append(point("VII_center",1,.01,.005,0,SHEAR,"tangent_center"));fine.append("VII_center")
    for c,j in (("log_k",0),("log_A",1),("log_shear",2)):
        for mark,sgn in (("minus",-1),("plus",1)):
            q=[math.log(.01),math.log(.005),0.];q[j]+=.02*sgn
            name=f"VII_{c}_02_{mark}"
            p.append(point(name,1,math.exp(q[0]),math.exp(q[1]),0,[math.exp(q[2])*v for v in SHEAR],"tangent",coordinate=c,width=.02,side=sgn));fine.append(name)
    p.append({"name":"FLRW","N6":[0]*6,"A3":[0]*3,"shear6":[0]*6,"expected_type":"I","kind":"control","parameters":{}})
    fine.append("FLRW")
    return {"schema":"htt.r121.weak_chart/1","points":p,"base":base,"fine":fine,"base_steps":1600,"fine_steps":3200,
            "ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],"coordinates":["log_k","log_A","u","log_shear"],
            "scales":[1,1,.001,1],"u_widths":[.002,.001,.0005],"scope":"fixed finite samples, no population coverage"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
