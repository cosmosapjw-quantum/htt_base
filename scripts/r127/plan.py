"""Frozen source-node groups and supported native stencil."""
import numpy as np
import json
from scripts.r125.plan import make as previous
LABELS=("early","rec_peak","residual","rei_donor","conditional_tail")
def groups(table):
    t=np.asarray(table)[:,0];z=1601*np.exp(-t)-1
    # Epsilon guards floating evaluation of exact source-owned z=20 and z=4 boundaries.
    return np.select([z>=1200-1e-9,z>=800-1e-9,z>=20-1e-9,z>=4-1e-9],[0,1,2,3],default=4).astype(int)
def make():
    pts=[]
    for pt in previous()["points"]:
        if not pt["name"].startswith(("VIIh_m1_relative_dust_","VIIh_m2_metric_")):continue
        w="rec_peak" if pt["name"].startswith("VIIh_m1") else "rei_donor"
        for sign in (-1,1):
            v=dict(pt,name=pt["name"]+"_"+w+("_minus" if sign<0 else "_plus"),window=w,opacity_sign=sign)
            pts.append(v)
    names=[v["name"] for v in pts]
    return {"schema":"htt.r127.nodal_opacity/1","points":pts,"base":names,"fine":names,"base_steps":1600,"fine_steps":3200,
       "ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],"fd_widths":[.03,.01],"groups":list(LABELS),
       "oracle_L":12,"tight_L":20,"scope":"fractional perturbation of source nodes; controlled fixed-background intervention"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
