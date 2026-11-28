"""Direct depth-preserving histories, including a shape outside the old span."""
import argparse,gzip,json,time,hashlib,io
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from common.fixed_tau_shapes import source_metrics,balanced_pair,visibility,integrate_direction,perturb_nodes
from common.opacity_memory_kernel import NodalWindows,solve_state
from common.physical_memory_budget import build_context
from common.initial_data_response import observe_columns
from scripts.r127.run_tangent import inputs,context,seed_matrix
from scripts.r127.plan import groups,LABELS
from scripts.r128.spectra import read,norm,sha
from scripts.r128.verify_sources import DOC
def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]));c=context(inp,"VIIh",0,20)
    q=source_metrics(c,w);q8=source_metrics(c,w,8);t=q["t"];d=q["nodal"];z=1601*np.exp(-w.table[:,0])-1
    report=json.loads((DOC/"C6_SPECTRA.json").read_text());old=DOC.parent/"R127_OPACITY_MEMORY_KERNEL_20261128"
    tr=json.loads((old/"C6_TANGENT.json").read_text())["runs"]
    v=np.array(report["sectors"]["VIIh_m2"]["metrics"]["M_tau"]["tail_locked"]["full"]["directions"])[:,0];v/=np.max(abs(v))
    intra=np.zeros(len(z));mask=w.groups==1;intra[mask]=z[mask]-d[mask]@z[mask]/d[mask].sum();intra/=np.max(abs(intra))
    dirs={"early_rec":balanced_pair(t,1,0)[w.groups],"late_swap":balanced_pair(t,3,2)[w.groups],"leading_tail_locked":v[w.groups],"intra_rec":intra}
    root=DOC/"shapes";root.mkdir(exist_ok=False);tables={};records={}
    header=(scratch/"merged_ZERO.tsv").read_text().splitlines()[0]
    basevis=visibility(c,w,12)
    for name,m,idx in (("early_rec",1,1),("late_swap",2,1),("leading_tail_locked",2,0),("intra_rec",1,0)):
        start=time.monotonic();f=dirs[name]
        assert abs(d@f)<2e-12 and abs(q8["nodal"]@f)<2e-12 and np.all(f[w.groups==4]==0)
        c=context(inp,"VIIh",m,20);s=c["system"];weights,names=seed_matrix(c,"VIIh");y=s["basis"]@weights[:,idx]
        r=integrate_direction(c,w,f,y);base=observe_columns(r["end"][:,None],s,"host")[:,:,0];target=observe_columns(r["tangent"][:,None],s,"host")[:,:,0]
        prior=read(old,tr[f"VIIh_m{m}_L20"]);oldbase=prior["sky"][:,:,idx]
        pg=None;coeff=None
        if name!="intra_rec":
            coeff=np.array([f[w.groups==i][0] for i in range(5)])
            ref=np.einsum("g,gmc->mc",coeff,prior["dsky"][:,:,:,idx]);pg=norm(target-ref)/norm(ref)
        arrays={"f":f,"initial":y,"endpoint":r["end"],"tangent_state":r["tangent"],"base":base,"tangent":target}
        fd={};vis={}
        for h in (.03,.01):
            vv=[];tag="h03" if h==.03 else "h01"
            for sign in (-1,1):
                tab=perturb_nodes(w,f,sign*h);cp=build_context(**dict(inp,table=tab),a0=.005,m=m,L=20)
                ws=NodalWindows(tab,w.groups);vi=visibility(cp,ws,12)
                assert abs(vi["tau"]-basevis["tau"])<2e-11
                vi["tau_difference"]=vi["tau"]-basevis["tau"];vi["min_xe"]=float(tab[:,1].min());vi["max_xe"]=float(tab[:,1].max())
                zz=solve_state(cp,y,rtol=2e-11,max_step=.015)["end"];sky=observe_columns(zz[:,None],cp["system"],"host")[:,:,0];vv.append(sky)
                side="minus" if sign<0 else "plus";arrays[tag+"_"+side]=sky;vis[tag+"_"+side]=vi
                if h==.03 and name in ("early_rec","late_swap"):
                    fn=name+"_"+side;path=scratch/(fn+".tsv")
                    np.savetxt(path,tab,header=header,comments="",fmt="%.17e")
                    raw=path.read_bytes();np.testing.assert_array_equal(np.loadtxt(io.BytesIO(raw),skiprows=1),tab)
                    (DOC/(fn+".tsv.gz")).write_bytes(gzip.compress(raw,mtime=0))
                    tables[fn]={"sha256":sha(raw),"direction":name,"width":sign*h,"tau":vi["tau"],"tau_difference":vi["tau_difference"]}
            a=(vv[1]-vv[0])/(2*h);arrays[tag]=a;fd[tag]={"width":h,"relative_to_tangent":norm(a-target)/max(norm(target),1e-30),"norm":norm(a),"same_depth_sky_separation":norm(vv[1]-vv[0]),"separation_over_baseline":norm(vv[1]-vv[0])/norm(base),
                "channel_separation":np.linalg.norm(vv[1]-vv[0],axis=0).tolist()}
        path=root/(name+".npz");np.savez_compressed(path,**arrays)
        rec={"path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes()),"m":m,"seed":names[idx],"group_coefficients":None if coeff is None else coeff.tolist(),"max_node_amplitude":float(np.max(abs(f))),"depth_residual":float(d@f),
             "GL8_depth_residual":float(q8["nodal"]@f),"baseline_relative_to_R127":norm(base-oldbase)/norm(oldbase),"direction_relative_to_R127":pg,
             "prior_tangent_sha256":tr[f"VIIh_m{m}_L20"]["sha256"],"tangent_norm":norm(target),"tangent_endpoint_constraint":r["max_endpoint_constraint"],"nfev":r["nfev"],
             "fd":fd,"visibility":vis,"wall_s":time.monotonic()-start}
        records[name]=rec
        print(name,"coeff",rec["group_coefficients"],"tau_residual",rec["depth_residual"],"tangent",rec["tangent_norm"],"prior",pg,"fd",fd,"mean_z +/-",vis["h03_minus"]["mean_z"],vis["h03_plus"]["mean_z"],"seconds",round(rec["wall_s"],2),flush=True)
    # Exact scalar B on VII0: same-depth shape and independent scalar integration at tight absolute tolerance.
    c0=context(inp,"VII0",0,8);q0=source_metrics(c0,w);f0=balanced_pair(q0["t"],1,0)[w.groups];bs=[]
    for sign in (-1,1):
        tab=perturb_nodes(w,f0,sign*.03);cp=build_context(**dict(inp,table=tab),a0=0.,m=0,L=8);wp=NodalWindows(tab,w.groups);dep=source_metrics(cp,wp)["tau"]
        sol=solve_ivp(lambda t,y:-cp["system"]["coeff"](t)[5]*y,(0.,tab[-1,0]),[1.],method="DOP853",rtol=2e-11,atol=1e-29,max_step=.015)
        if not sol.success:raise RuntimeError(sol.message)
        bs.append({"sign":sign,"tau":dep,"B_end":float(sol.y[0,-1]),"exact":float(np.exp(-dep)),"relative_error":float(abs(sol.y[0,-1]/np.exp(-dep)-1))})
    out={"runs":records,"visibility_baseline":basevis,"scalar_B_control":bs,"source_sha256":json.loads((DOC/"C2_CONSTANTS.json").read_text())["original_opacity_sha256"],
         "scope":"controlled equal-depth histories on fixed background; no self-consistent REC/REI parameter derivative"}
    (DOC/"C7_SHAPES.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    (DOC/"SHAPE_TABLES.json").write_text(json.dumps({"tables":tables,"scope":"four controlled finite tables at fixed background tau"},indent=2,allow_nan=False)+"\n")
    print("B_CONTROL",json.dumps(bs),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
