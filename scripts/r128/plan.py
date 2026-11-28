import json
from scripts.r125.plan import make as previous
def make():
    pts=[]
    for pt in previous()["points"]:
        if not pt["name"].startswith(("VIIh_m1_relative_dust_","VIIh_m2_metric_")):continue
        w="early_rec" if pt["name"].startswith("VIIh_m1") else "late_swap"
        for sign in (-1,1):
            v=dict(pt,name=pt["name"]+"_"+w+("_minus" if sign<0 else "_plus"),window=w,opacity_sign=sign)
            pts.append(v)
    names=[v["name"] for v in pts]
    return {"schema":"htt.r128.fixed_tau/1","points":pts,"base":names,"fine":names,"base_steps":1600,"fine_steps":3200,
      "ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],"fd_widths":[.03,.01],
      "directions":["early_rec","late_swap","leading_tail_locked","intra_rec"],"scope":"fixed-background exactly depth-balanced nodal perturbations"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
