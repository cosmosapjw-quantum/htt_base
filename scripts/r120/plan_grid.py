"""Freeze a small physical chart and a representative-family set for native runs."""
import json,math
from pathlib import Path

# R114 general-Lie representative scales; all named original representatives.
FAMILIES={
 "FLRW":((0,0,0),0,"I"),"I":((0,0,0),0,"I"),"II":((.01,0,0),0,"II"),
 "III":((0,.01,-.01),.01,"III"),"IV":((0,0,.01),.01,"IV"),"V":((0,0,0),.01,"V"),
 "VI0":((0,.01,-.01),0,"VI_0"),"VIh":((0,.01,-.01),.005,"VI_h"),
 "VIstar":((0,.012,-.012),.004,"VI*_-1/9"),"VII0":((0,.01,.01),0,"VII_0"),
 "VIIh":((0,.01,.01),.005,"VII_h"),"VIII":((-.01,.01,.01),0,"VIII"),"IX":((.01,.01,.01),0,"IX")}
SHEAR=(.0003,.0002,-.0005,.00015,.0001,.00012)

def make():
    pts={}
    def add(name,diag,a,scale,expected,kind,params=None):
        if name in pts:raise ValueError(name)
        pts[name]={"name":name,"N6":[*diag,0,0,0],"A3":[a,0,0],"shear6":[scale*v for v in SHEAR],
                   "expected_type":expected,"kind":kind,"params":params}
    for n,(diag,a,t) in FAMILIES.items():add(n,diag,a,0 if n=="FLRW" else 1,t,"representative")
    def chart(name,sgn,k,a,u,scale,kind,expected=None):
        t=expected or ("VI_h" if sgn==-1 else "VII_h")
        add(name,(0,k*math.exp(u),sgn*k*math.exp(-u)),a,scale,t,kind,
            {"sign":sgn,"k":k,"A0":a,"u":u,"shear_scale":scale,"h":sgn*(a/k)**2 if a and k else None})
    for name,sign in (("VIh",-1),("VIIh",1)):
        for width in (.04,.02):
            for j,label in enumerate(("log_k","log_A","u","log_shear")):
                for direction,ds in (("minus",-1),("plus",1)):
                    q=[math.log(.01),math.log(.005),0.,0.];q[j]+=ds*width
                    chart(f"{name}_{label}_{int(width*100):02d}_{direction}",sign,math.exp(q[0]),math.exp(q[1]),q[2],math.exp(q[3]),"tangent")
        # Fixed A0 near V, fixed k near class A, both scales near I.
        for ratio,tag in ((.2,"20"),(.05,"05")):
            chart(f"{name}_k_down_{tag}",sign,.01*ratio,.005,0,1,"contraction_V")
            chart(f"{name}_A_down_{tag}",sign,.01,.005*ratio,0,1,"contraction_class_A")
            chart(f"{name}_both_down_{tag}",sign,.01*ratio,.005*ratio,0,1,"contraction_I")
        chart(f"{name}_zero_shear",sign,.01,.005,0,0,"curvature_only_IC")
        chart(f"{name}_negative_shear",sign,.01,.005,0,-1,"signed_shear")
    add("V_A005",(0,0,0),.005,1,"V","contraction_endpoint")
    chart("VIstar_k001",-1,.01,.01/3,0,1,"exceptional_stratum","VI*_-1/9")
    fine=["VIh","VIIh","I","II","VIII","IX","FLRW","VIstar_k001"]
    fine += [n for n in pts if "_02_" in n]
    angular=["VIh","VIIh","VIstar_k001","FLRW"]
    return {"schema":"htt.r120.finite_chart/1","base_steps":800,"fine_steps":1600,
            "base_harmonic_lmax":8,"fine_angular_harmonic_lmax":12,"ell_max":8,
            "base_los_grid":[16,32],"fine_angular_los_grid":[24,48],
            "points":list(pts.values()),"fine_time":fine,"fine_angular":angular,
            "derivative_widths":[.04,.02],"coordinates":["log_k","log_A","u","log_shear"],
            "scope":"finite deterministic chart; named exceptional strata retained, no family posterior"}

if __name__=="__main__":
    print(json.dumps(make(),indent=2,allow_nan=False))
