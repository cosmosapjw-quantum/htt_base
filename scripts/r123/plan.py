"""Frozen source-matched tensor-sector scan on balanced VII geometries."""
import json
def make():
    points=[];base=[];fine=[];angular=[]
    for family,k,a,typ in (("VII0",.01,0.,"VII_0"),("VIIh",.01,.005,"VII_h")):
        for tag,amp in (("hi",1e-4),("lo",5e-5)):
            for side,sgn in (("pos",1),("neg",-1)):
                name=f"{family}_{tag}_{side}";eps=sgn*amp
                params={"k":k,"A0":a,"eps":eps}
                if a!=0:params["h"]=(a/k)**2
                points.append({"name":name,"N6":[k,k,0.,0.,0.,0.],"A3":[0.,0.,a],
                    "shear6":[eps,-eps,0.,0.,0.,0.],"expected_type":typ,"kind":"oracle",
                    "parameters":params,"recombination":"table"})
                base.append(name)
                if tag=="lo":fine.append(name);angular.append(name)
    return {"schema":"htt.r123.tensor_oracle/1","points":points,"base":base,"fine":fine,"angular":angular,
            "base_steps":1600,"fine_steps":3200,"ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],
            "angular_harmonic_lmax":12,"angular_los_grid":[24,48],
            "scope":"finite balanced VII spin-2 source comparison, no calibrated likelihood"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
