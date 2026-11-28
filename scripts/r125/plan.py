"""Source-matched supported initial columns and refinement grid."""
import json
def make():
    points=[];base=[];fine=[]
    for family,k,a,typ in (("VII0",.01,0.,"VII_0"),("VIIh",.01,.005,"VII_h")):
        for m in (0,1,2):
            col="metric" if m==2 else "relative_dust"
            for side,sgn in (("pos",1),("neg",-1)):
                eps=sgn*5e-5;name=f"{family}_m{m}_{col}_{side}_host"
                n=[k*(1+eps),k*(1-eps),0.,0.,0.,0.] if m==2 else [k,k,0.,0.,0.,0.]
                params={"k":k,"A0":a,"eps":eps,"m":m,"column":col}
                if a:params["h"]=a*a/(n[0]*n[1])
                p={"name":name,"N6":n,"A3":[0.,0.,a],"shear6":[0.]*6,"expected_type":typ,"kind":"oracle",
                   "parameters":params,"recombination":"table","observer_frame":"host"}
                if m<2:p["dust_beta"]=[0.,0.,.843*eps] if m==0 else [.843*eps,0.,0.]
                points.append(p);base.append(name);fine.append(name)
    return {"schema":"htt.r125.initial_data/1","points":points,"base":base,"fine":fine,"base_steps":1600,"fine_steps":3200,
            "ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],
            "scope":"native-supported zero shear relative dust tilt and metric split, table-only"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
