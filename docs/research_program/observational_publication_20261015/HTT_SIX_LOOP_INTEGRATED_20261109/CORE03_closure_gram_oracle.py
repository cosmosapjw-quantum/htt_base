"""CORE-03 read-only oracle: SR closure vs 4x4 Lorentz boosts, exact-branch round trip, STF5 Gram vs tr(S^2). SYNTHETIC checks of repository functions; run: python -I <this file>."""
import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "htt" / "src"))
from common.relativistic_velocity_closure import compose_velocities_sr
from common.kinematic_response import compose_velocities
from common.stf_metric_bridge import G_STF5
def boost(b):
    b=np.asarray(b,float); b2=b@b; g=1/np.sqrt(1-b2)
    L=np.eye(4); L[0,0]=g; L[0,1:]=g*b; L[1:,0]=g*b
    L[1:,1:]+= (g-1)*np.outer(b,b)/b2 if b2>0 else 0
    return L
def oracle(rm,mo):
    gm=1/np.sqrt(1-mo@mo); U=np.r_[gm,gm*mo]          # observer 4-velocity in M frame
    UR=boost(rm)@U                                    # M moves at rm relative to R
    return UR[1:]/UR[0]
rng=np.random.default_rng(20261110)
out={}
errs=[]
for _ in range(2000):
    rm=rng.normal(size=3); rm*=rng.uniform(0,0.9)/np.linalg.norm(rm)
    mo=rng.normal(size=3); mo*=rng.uniform(0,0.9)/np.linalg.norm(mo)
    errs.append(np.max(np.abs(compose_velocities_sr(rm,mo)-oracle(rm,mo))))
out["sr_vs_lorentz_oracle_max_abs_err_2000_random"]=float(max(errs))
# cosmological-scale
rm=np.array([1.1e-3,-.4e-3,.2e-3]); mo=np.array([.8e-3,.3e-3,-.5e-3])
d=compose_velocities_sr(rm,mo)-(rm+mo)
out["first_order_gap_norm_cosmo"]=float(np.linalg.norm(d)); out["rel_gap"]=float(np.linalg.norm(d)/np.linalg.norm(rm+mo))
out["oracle_err_cosmo"]=float(np.max(np.abs(compose_velocities_sr(rm,mo)-oracle(rm,mo))))
z=np.zeros(3)
out["zero_rm_exact"]=bool(np.array_equal(compose_velocities_sr(z,mo),mo)); out["zero_mo_exact"]=bool(np.array_equal(compose_velocities_sr(rm,z),rm))
# smoothness across 1e-15 threshold on |rm|^2
mo2=np.array([.3,.2,-.1]); u=np.array([1.,2.,-1.])/np.sqrt(6)
lo=compose_velocities_sr(u*np.sqrt(0.99e-15),mo2); hi=compose_velocities_sr(u*np.sqrt(1.01e-15),mo2)
out["threshold_jump_norm"]=float(np.linalg.norm(lo-hi)); out["threshold_oracle_err_below"]=float(np.max(np.abs(lo-oracle(u*np.sqrt(0.99e-15),mo2))))
# round trip of kinematic_response.compose_velocities (exact_composition=True branch)
rt=[]
for _ in range(2000):
    rm=rng.normal(size=3); rm*=rng.uniform(0.01,0.8)/np.linalg.norm(rm)
    ro=rng.normal(size=3); ro*=rng.uniform(0.01,0.8)/np.linalg.norm(ro)
    bmo=compose_velocities(ro,rm)
    rt.append(np.max(np.abs(compose_velocities_sr(rm,bmo)-ro)))
out["roundtrip_exact_branch_max_abs_err"]=float(max(rt))
# first-order branch error at tilt-scale
rm=np.array([1.1e-3,-.4e-3,.2e-3]); ro=np.array([1.9e-3,-.1e-3,-.3e-3])
out["first_order_branch_closure_resid_norm"]=float(np.linalg.norm(compose_velocities_sr(rm,ro-rm)-ro))
# Gram
def mat(v): 
    a,b,c,d,e=v; return np.array([[a,c,d],[c,b,e],[d,e,-a-b]])
gerr=0; 
for _ in range(1000):
    v=rng.normal(size=5); gerr=max(gerr,abs(v@G_STF5@v-np.trace(mat(v)@mat(v))))
out["gram_vs_trace_S2_max_err"]=float(gerr)
v=np.array([1.,1.,0,0,0]); out["example_norm_euclid_vs_gram"]=[float(np.linalg.norm(v)), float(np.sqrt(v@G_STF5@v))]
import json; print(json.dumps(out,indent=1))
