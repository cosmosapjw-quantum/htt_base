"""Frozen source-matched scalar/vector plus tensor refinement experiments."""
import json
def make():
    points=[];base=[];fine=[];normal=[];tensor=[]
    for family,k,a,typ in (("VII0",.01,0.,"VII_0"),("VIIh",.01,.005,"VII_h")):
        for m in (0,1,2):
            for tag,amp in (("hi",1e-4),("lo",5e-5)):
                if m==2 and tag!="lo":continue
                for side,sgn in (("pos",1),("neg",-1)):
                    eps=sgn*amp
                    for frame in (("host","normal") if m<2 and tag=="lo" else ("host",)):
                        name=f"{family}_m{m}_{tag}_{side}_{frame}"
                        params={"k":k,"A0":a,"eps":eps,"m":m}
                        if a!=0:params["h"]=(a/k)**2
                        S=[-.5,-.5,1.,0.,0.,0.] if m==0 else ([0.,0.,0.,0.,1.,0.] if m==1 else [1.,-1.,0.,0.,0.,0.])
                        points.append({"name":name,"N6":[k,k,0.,0.,0.,0.],"A3":[0.,0.,a],"shear6":[eps*v for v in S],
                          "expected_type":typ,"kind":"oracle","parameters":params,"recombination":"table","observer_frame":frame})
                        if m==2:tensor.append(name)
                        elif frame=="normal":normal.append(name)
                        else:
                            base.append(name)
                            if tag=="lo":fine.append(name)
    return {"schema":"htt.r124.codazzi_sectors/1","points":points,"base":base,"fine":fine,"normal":normal,"tensor":tensor,
            "base_steps":1600,"fine_steps":3200,"tensor_steps":6400,"ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],
            "scope":"finite table-only scalar/vector signed response and tensor time refinement"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
