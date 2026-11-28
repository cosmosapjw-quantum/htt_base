"""Profile signed real opacity response against physically whitened IC maps."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from common.profiled_opacity_shapes import aggregation,compact_sky,real_shape_map,real_initial_map,profile
from common.fixed_tau_shapes import constrained_basis
from common.physical_memory_budget import metric_weights,whiten
from scripts.r127.run_tangent import inputs,context
from scripts.r129.run_nested import locks
from scripts.r129.verify_sources import DOC
from scripts.r128.spectra import read,sha,norm

def opnorm(A):return float(np.linalg.norm(A,ord=2))
def arrays(path):
    with np.load(path,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def summarize(A,AL):
    _,s,Vh=np.linalg.svd(A,full_matrices=False)
    gap=opnorm(A-AL);return {"singular_values":s.tolist(),"empirical_difference":gap,"count_above_difference":int(np.sum(s>gap))},Vh
def main(scratch):
    inp=inputs(scratch);old=locks();nested=json.loads((DOC/"C6_NESTED.json").read_text());metric=arrays(DOC/"C6_METRIC.npz")
    assert sha((DOC/"C6_METRIC.npz").read_bytes())==nested["metric_sha256"]
    records={};out={};count=0
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            key=f"{fam}_m{m}";c=context(inp,fam,m,20);s=c["system"];a=read(DOC,nested["runs"][key+"_L20"]);al=read(DOC,nested["runs"][key+"_L12"])
            pi=old["R125"];pt=pi[1]["runs"][key+"_tight"];pl=pi[1]["runs"][key+"_L12"];it=read(pi[0],pt);il=read(pi[0],pl)
            p6=old["R126"];br=p6[1]["runs"][key+"_L20_s1"];b=read(p6[0],br);W=b["whitener"];M=b["M"]
            wi,_=metric_weights(c,0.);B=s["basis"]
            np.testing.assert_array_equal(it["initial"],B)
            np.testing.assert_allclose(M,B.conj().T@(wi[:,None]*B),atol=1e-15,rtol=1e-13)
            np.testing.assert_allclose(W.conj().T@M@W,np.eye(len(M)),atol=1e-12)
            size=float(np.vdot(a["initial"],wi*a["initial"]).real);scale=np.sqrt(size)
            np.testing.assert_allclose(a["initial"],B@a["weights"],atol=1e-15)
            rows={}
            for band,high in (("full",False),("high",True)):
                T=real_initial_map(compact_sky(it["sky_host"],m,high)@W,m);TL=real_initial_map(compact_sky(il["sky_host"],m,high)@W,m)
                Z=real_shape_map(compact_sky(a["dsky"],m,high))/scale;ZL=real_shape_map(compact_sky(al["dsky"],m,high))/scale
                baseline=real_shape_map(compact_sky(a["sky"],m,high)[:,None])[:,0]/scale
                baseL=real_shape_map(compact_sky(al["sky"],m,high)[:,None])[:,0]/scale
                delta=opnorm(T-TL);floor=np.finfo(float).eps*max(T.shape)*opnorm(T)
                tol=max(delta,floor);rankinfo={"initial_singular_values":np.linalg.svd(T,compute_uv=False).tolist(),"initial_coarse_singular_values":np.linalg.svd(TL,compute_uv=False).tolist(),"initial_difference":delta,"machine_floor":floor,"cutoff_base":tol}
                out[key+"_"+band+"_T"]=T;out[key+"_"+band+"_TL"]=TL
                out[key+"_"+band+"_Z"]=Z;out[key+"_"+band+"_ZL"]=ZL
                out[key+"_"+band+"_baseline"]=baseline;out[key+"_"+band+"_baseL"]=baseL
                metrows={}
                for met in ("M_tau","M_clock"):
                    levels={}
                    for n in (4,8,16):
                        E=aggregation(n);t=E.T@metric[fam+"_t"];Msrc=E.T@metric[fam+"_"+met]@E
                        Csrc=constrained_basis(Msrc,t,list(range(n)));N=E@Csrc;S=Z@N;SL=ZL@N
                        prefix=f"{key}_{band}_{met}_{n}"
                        out[prefix+"_N"]=N;out[prefix+"_S"]=S;out[prefix+"_SL"]=SL
                        raw,Vh=summarize(S,SL);raw["leading_coordinates"]=Vh[0].tolist()
                        profiles={}
                        # Single baseline amplitude; shear initial phase columns are in
                        # original coordinates, not columns of a general whitened basis.
                        Ti=real_initial_map(compact_sky(it["sky_host"][:,:,[0]],m,high),m)
                        TiL=real_initial_map(compact_sky(il["sky_host"][:,:,[0]],m,high),m)
                        for tag,TT,TTL,cut in [("amplitude",baseline[:,None],baseL[:,None],0.),("shear",Ti,TiL,max(opnorm(Ti-TiL),np.finfo(float).eps*max(Ti.shape)*opnorm(Ti))),("factor1",T,TL,tol),("factor10",T,TL,10*tol),("factor100",T,TL,100*tol),("machine",T,TL,floor)]:
                            r=profile(TT,S,cut);lo=profile(TTL,SL,cut);q,Vh=summarize(r["E"],lo["E"])
                            motion=opnorm(r["P"]-lo["P"])
                            q.update(rank=r["rank"],coarse_rank=lo["rank"],cutoff=cut,projector_motion=motion,
                                     rank_comparable=r["rank"]==lo["rank"],retained_fraction=opnorm(r["E"])/max(opnorm(S),1e-30),
                                     orthogonality=opnorm(r["P"]@r["E"]),fit_closure=opnorm(S+TT@r["C"]-r["E"]),compensator_op_norm=opnorm(r["C"]),
                                     leading_coordinates=Vh[0].tolist())
                            if not q["rank_comparable"]:q["count_above_difference"]=None
                            if tag=="machine":q["interpretation"]="ill-conditioned machine-rank diagnostic, not certified range"
                            profiles[tag]=q
                            if tag in ("factor10","machine"):
                                out[prefix+"_"+tag+"_P"]=r["P"];out[prefix+"_"+tag+"_E"]=r["E"];out[prefix+"_"+tag+"_C"]=r["C"]
                            count+=1
                        levels[str(n)]={"raw":raw,"profiles":profiles}
                    metrows[met]=levels
                rows[band]={"initial":rankinfo,"metrics":metrows}
            records[key]={"m":m,"initial_size":size,"initial_R125_tight_sha256":pt["sha256"],"initial_R125_L12_sha256":pl["sha256"],"R126_metric_sha256":br["sha256"],"nested_sha256":nested["runs"][key+"_L20"]["sha256"],"bands":rows}
            out[key+"_W"]=W;out[key+"_M"]=M
            for n in (4,8,16):
                q=rows["full"]["metrics"]["M_tau"][str(n)]
                r=q["profiles"]["factor10"];print(key,n,"raw",q["raw"]["count_above_difference"],"IC rank",r["rank"],"coarse",r["coarse_rank"],"profile",r["count_above_difference"],"retained",r["retained_fraction"],"motion",r["projector_motion"],"comp",r["compensator_op_norm"],flush=True)
    path=DOC/"C7_PROFILE.npz";np.savez_compressed(path,**out)
    report={"sectors":records,"npz_sha256":sha(path.read_bytes()),"profile_count":count,"scope":"conditional real Euclidean signed profiles; threshold and source metric dependent, no survey inference"}
    (DOC/"C7_PROFILE.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
