"""Frozen intervention and native-supported experiment chart."""
import json
from scripts.r125.plan import make as previous
def make():
    pts=[p for p in previous()["points"] if p["name"].startswith(("VIIh_m1_","VIIh_m2_"))]
    names=[p["name"] for p in pts]
    return {"schema":"htt.r126.memory_loss/1","points":pts,"base":names,"fine":names,
            "base_steps":1600,"fine_steps":3200,"ell_max":8,"harmonic_lmax":8,"los_grid":[16,32],
            "opacity_scale":.25,"oracle_scales":[0.,.25,.5,1.],"oracle_L":16,"tight_L":20,"tight_scales":[.25,1.],
            "scope":"counterfactual opacity intervention on exact fixed source background"}
if __name__=="__main__":print(json.dumps(make(),indent=2,allow_nan=False))
