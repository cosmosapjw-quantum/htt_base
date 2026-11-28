"""Independent finite shape and compensating-IC integrations."""
import argparse,gzip,json,time,io
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from common.fixed_tau_shapes import balanced_pair,perturb_nodes,integrate_direction,source_metrics
from common.opacity_memory_kernel import NodalWindows,solve_state
from common.physical_memory_budget import build_context,metric_weights
from common.profiled_opacity_shapes import compact_sky,real_shape_map,unpack_ic
from common.initial_data_response import observe_columns
from scripts.r127.run_tangent import inputs,context,seed_matrix
from scripts.r127.plan import groups
from scripts.r128.spectra import read,sha,norm
from scripts.r129.profile_maps import arrays
from scripts.r129.verify_sources import DOC

def sky(c,y):
    zz=solve_state(c,y,rtol=2e-11,max_step=.015)["end"]
    return observe_columns(zz[:,None],c["system"],"host")[:,:,0]
def real(x,m):return real_shape_map(compact_sky(x,m)[:,None])[:,0]

def native_case(args):
    scratch,name,m,g0,g1=args;start=time.monotonic();inp=inputs(scratch)
    g=groups(inp["table"]);w=NodalWindows(inp["table"],g);mt=arrays(DOC/"C6_METRIC.npz");ng=mt["groups"]
    c=context(inp,"VIIh",m,20);s=c["system"];weights,names=seed_matrix(c,"VIIh");y=s["basis"]@weights[:,1]
    coeff=balanced_pair(mt["VIIh_t"],g0,g1);f=np.r_[coeff,0.][ng]
    q=source_metrics(c,w);assert abs(q["nodal"]@f)<2e-12
    r=integrate_direction(c,w,f,y);base=observe_columns(r["end"][:,None],s,"host")[:,:,0];target=observe_columns(r["tangent"][:,None],s,"host")[:,:,0]
    arr={"f":f,"coeff":coeff,"initial":y,"base":base,"tangent":target,"endpoint":r["end"],"tangent_state":r["tangent"]};tables={};fd={}
    for h in (.03,.01):
        vals=[];tag="h03" if h==.03 else "h01";depths=[]
        for sign in (-1,1):
            tab=perturb_nodes(w,f,sign*h);cp=build_context(**dict(inp,table=tab),a0=.005,m=m,L=20)
            dep=source_metrics(cp,NodalWindows(tab,g))["tau"];depths.append(dep);assert abs(dep-q["tau"])<2e-11
            z=sky(cp,y);vals.append(z);side="minus" if sign<0 else "plus";arr[tag+"_"+side]=z
            if h==.03:
                fn=name+"_"+side;path=scratch/(fn+".tsv");np.savetxt(path,tab,header=(scratch/"merged_ZERO.tsv").read_text().splitlines()[0],comments="",fmt="%.17e")
                raw=path.read_bytes();np.testing.assert_array_equal(np.loadtxt(io.BytesIO(raw),skiprows=1),tab)
                (DOC/(fn+".tsv.gz")).write_bytes(gzip.compress(raw,mtime=0))
                tables[fn]={"sha256":sha(raw),"direction":name,"width":sign*h,"tau":dep,"tau_difference":dep-q["tau"]}
        a=(vals[1]-vals[0])/(2*h);arr[tag]=a
        fd[tag]={"width":h,"norm":norm(a),"relative_to_tangent":norm(a-target)/norm(target),"max_tau_difference":max(abs(x-q["tau"]) for x in depths)}
    path=DOC/"direct"/(name+".npz");np.savez_compressed(path,**arr)
    rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"m":m,"seed":names[1],"direction":coeff.tolist(),"depth_residual":float(q["nodal"]@f),"tangent_norm":norm(target),"fd":fd,"wall_s":time.monotonic()-start}
    print("DIRECT",name,"tangent",rec["tangent_norm"],"FD",fd,flush=True)
    return name,rec,tables

def compensate(args):
    scratch,name,fam,m,choice=args;start=time.monotonic();inp=inputs(scratch);g=groups(inp["table"]);w=NodalWindows(inp["table"],g);mt=arrays(DOC/"C6_METRIC.npz");ng=mt["groups"]
    c=context(inp,fam,m,20);s=c["system"];weights,names=seed_matrix(c,fam);y=s["basis"]@weights[:,0]
    pr=json.loads((DOC/"C7_PROFILE.json").read_text());a=arrays(DOC/"C7_PROFILE.npz");key=f"{fam}_m{m}";prefix=key+"_full_M_tau_16"
    rr=pr["sectors"][key];q=rr["bands"]["full"]["metrics"]["M_tau"]["16"];pf=q["profiles"]["factor10"]
    vec=np.asarray(q["raw"]["leading_coordinates"] if choice=="raw" else pf["leading_coordinates"])
    coeff=a[prefix+"_N"]@vec;scale=np.max(abs(coeff));coeff=coeff/scale;vec=vec/scale;f=np.r_[coeff,0.][ng]
    source=source_metrics(c,w);assert abs(source["nodal"]@f)<2e-12
    # Source response normalized by initial physical size; undo that normalization.
    size=rr["initial_size"];root_size=np.sqrt(size);H=a[key+"_W"];C=a[prefix+"_factor10_C"]@vec
    physical_shift=s["basis"]@(H@unpack_ic(C,m))*root_size;wi,_=metric_weights(c,0.);shift=float(np.sqrt(np.vdot(physical_shift,wi*physical_shift).real)/root_size)
    np.testing.assert_allclose(shift,norm(C),rtol=1e-12,atol=1e-12)
    h=min(.03,.05/max(shift,1e-30));assert h>0 and np.all(abs(h*f)<=.03+1e-15)
    raw_pred=a[prefix+"_S"]@vec*root_size;comp_pred=a[prefix+"_factor10_E"]@vec*root_size
    vals={"f":f,"coeff":coeff,"initial":y,"physical_shift":physical_shift,"whitened_compensator":C,"raw_pred":raw_pred,"comp_pred":comp_pred}
    for sign in (-1,1):
        tab=perturb_nodes(w,f,sign*h);cp=build_context(**dict(inp,table=tab),a0=.005 if fam=="VIIh" else 0.,m=m,L=20)
        dep=source_metrics(cp,NodalWindows(tab,g))["tau"];assert abs(dep-source["tau"])<2e-11
        side="minus" if sign<0 else "plus"
        vals["raw_"+side]=sky(cp,y);vals["comp_"+side]=sky(cp,y+sign*h*physical_shift)
    d0=real((vals["raw_plus"]-vals["raw_minus"])/(2*h),m);d1=real((vals["comp_plus"]-vals["comp_minus"])/(2*h),m)
    vals["raw_fd"]=d0;vals["comp_fd"]=d1
    path=DOC/"direct"/(name+".npz");np.savez_compressed(path,**vals)
    rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"family":fam,"m":m,"selection":choice,"profile_rank":pf["rank"],
         "width":h,"max_relative_nodal_change":float(np.max(abs(h*f))),"initial_relative_shift":h*shift,"IC_shift_per_unit_shape":shift,
         "depth_residual":float(source["nodal"]@f),"raw_prediction_norm":norm(raw_pred),"profile_prediction_norm":norm(comp_pred),
         "raw_fd_norm":norm(d0),"comp_fd_norm":norm(d1),"predicted_retained_fraction":norm(comp_pred)/norm(raw_pred),
         "measured_retained_fraction":norm(d1)/norm(d0),"raw_fd_error_over_raw":norm(d0-raw_pred)/norm(raw_pred),
         "comp_fd_error_over_raw":norm(d1-comp_pred)/norm(raw_pred),"wall_s":time.monotonic()-start}
    print("COMP",name,rec,flush=True);return name,rec

def main(scratch):
    root=DOC/"direct";root.mkdir(exist_ok=False);tables={};rec={};comp={}
    jobs=[(scratch,"rec_subswap",1,4,7),(scratch,"rei_subswap",2,12,15)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for n,r,t in pool.map(native_case,jobs):rec[n]=r;tables.update(t)
    jobs=[(scratch,"scalar_compensation","VII0",0,"raw"),(scratch,"tensor_compensation","VIIh",2,"profiled")]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for n,r in pool.map(compensate,jobs):comp[n]=r
    (DOC/"C7_DIRECT.json").write_text(json.dumps({"native_cases":rec,"compensation":comp,"counts":{"directional_tangents":2,"native_case_FD_solves":8,"compensation_FD_solves":8},"scope":"finite independent changed-table and co-varying-IC controls; no native compensation parity"},indent=2,allow_nan=False)+"\n")
    (DOC/"SHAPE_TABLES.json").write_text(json.dumps({"tables":tables,"scope":"four fixed-background equal-depth contrast tables"},indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
