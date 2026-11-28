"""Matched-width native vs independent equal-depth finite signed stencils."""
import json,gzip,io
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from scripts.r128.verify_sources import DOC
from scripts.r128.plan import make
from scripts.r128.spectra import sha,norm,read

def load_native(mode):
    r=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text());const=json.loads((DOC/"C2_CONSTANTS.json").read_text());lock=json.loads((DOC/"C1.json").read_text());tables=json.loads((DOC/"SHAPE_TABLES.json").read_text())["tables"]
    assert r["plan_sha256"]==sha((DOC/"SCAN_PLAN.json").read_bytes()) and r["binary_sha256"]==lock["binary_sha256"]
    assert r["opacity_sha256"]==const["original_opacity_sha256"]
    assert [v["name"] for v in r["records"]]==make()[mode]
    points={v["name"]:v for v in make()["points"]};sky={}
    for v in r["records"]:
        n=v["name"];p=points[n];w=p["window"]+("_minus" if p["opacity_sign"]<0 else "_plus")
        assert v["intervention_sha256"]==tables[w]["sha256"] and v["window"]==p["window"] and v["opacity_sign"]==p["opacity_sign"]
        if v["status"]!="validated_scoped":raise ValueError(v)
        raw=(DOC/"raw"/mode/n/"los_modes.tsv").read_bytes();assert sha(raw)==v["hashes"]["los_modes.tsv"]
        x,_=decode_signed_modes(raw,8);sky[n]=x[1:]
    return {v["name"]:v for v in r["records"]},sky

def main():
    shapes=json.loads((DOC/"C7_SHAPES.json").read_text())["runs"];mb,b=load_native("base");mf,f=load_native("fine");out={};arrays={}
    for name,m,col in (("early_rec",1,"relative_dust"),("late_swap",2,"metric")):
        r=shapes[name];a=read(DOC,r);ref=a["h03"];target=a["tangent"]
        res={}
        for mode,data,meta in (("base",b,mb),("fine",f,mf)):
            def odd(sign):
                return (data[f"VIIh_m{m}_{col}_pos_host_{name}_{sign}"]-data[f"VIIh_m{m}_{col}_neg_host_{name}_{sign}"])/1e-4
            x=(odd("plus")-odd("minus"))/.06;arrays[name+"_"+mode]=x
            # finite native depth spread: independently recorded; includes nonlinear geometry and quadrature.
            depths=[meta[f"VIIh_m{m}_{col}_{seed}_host_{name}_{sign}"]["depth"] for seed in ("pos","neg") for sign in ("plus","minus")]
            res[mode]={"norm":norm(x),"relative_to_same_width_oracle":norm(x-ref)/norm(ref),"relative_to_tangent":norm(x-target)/norm(target),"native_depth_spread":max(depths)-min(depths),"native_depths":depths}
        out[name]={"sector":f"VIIh_m{m}","column":col,"shape_sha256":r["sha256"],"native":res,"time_error_ratio":res["base"]["relative_to_same_width_oracle"]/res["fine"]["relative_to_same_width_oracle"]}
        print(name,out[name],flush=True)
    path=DOC/"C8_NATIVE.npz";np.savez_compressed(path,**arrays)
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    result={"runs":out,"npz_sha256":sha(path.read_bytes()),"counts":{"base":len(b),"fine":len(f)},"smoke_LOS_byte_replay":smoke["hashes"]["los_modes.tsv"]==mb[smoke["name"]]["hashes"]["los_modes.tsv"],
        "scope":"nested signed finite difference at fixed background depth; native actual nonlinear background and time integration may change measured depth"}
    (DOC/"C8_NATIVE.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n");print("COUNTS",result["counts"],"SMOKE",result["smoke_LOS_byte_replay"])
if __name__=="__main__":main()
