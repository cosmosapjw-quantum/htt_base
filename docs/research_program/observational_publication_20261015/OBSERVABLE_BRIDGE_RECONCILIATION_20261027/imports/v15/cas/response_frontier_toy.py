"""Static finite-band entropy-response frontiers; no transport/ODE.

Dimensionless x=E/(k_B T_*), dnu/x-unit=x^2 dx.
All outputs are normalized by reference ray number; physical normalization
is D (k_B T_*)^3. The continuum theorem is in RESPONSE_FRONTIER.md.
"""
from pathlib import Path
import json, csv, platform
import numpy as np
from scipy.special import expit, xlogy
from scipy.optimize import root
from numpy.polynomial.legendre import leggauss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parents[1]
def quadrature(n):
    nodes,weights=leggauss(n)
    xx=[];ww=[]
    for a,b in zip([0,1,2,4,8,16,32],[1,2,4,8,16,32,64]):
        x=(a+b)/2+(b-a)*nodes/2
        xx.extend(x);ww.extend(weights*(b-a)/2*x*x)
    return np.array(xx),np.array(ww)
def occupation(z,xi):
    if xi==0:return np.exp(-z)
    if xi==-1:return expit(-z)
    if np.min(z)<=0:raise ValueError("Bose score left regular domain")
    return 1/np.expm1(z)
def entropy(f,xi):
    if xi==0:return xlogy(f,f)-f
    if xi==-1:return xlogy(f,f)+xlogy(1-f,1-f)
    return xlogy(f,f)-xlogy(1+f,1+f)
def solve_case(xi,eta,n=64,ts=None):
    x,w=quadrature(n);phi=np.array([np.ones_like(x),x])
    k=np.exp(-.5*((x-4)/.8)**2)
    g=occupation(x-eta,xi);mom=phi@(w*g);n0=mom[0]
    W=g*(1+xi*g)
    G=(phi*(w*W))@phi.T
    beta=np.linalg.solve(G,phi@(w*W*k))
    kp=k-beta@phi
    sig2=np.sum(w*W*kp*kp)/n0
    raw=np.sum(w*W*k*k)/n0
    ref=np.sum(w*g*k)/n0
    results=[]
    ts=np.r_[np.linspace(-1.5,-.03,40),np.linspace(.03,1.5,40)] if ts is None else np.array(ts)
    max_res=0.;dual_res=0.;min_margin=float("inf")
    for t in ts:
        def fun(a):
            z=x-eta-t*k+a@phi
            f=occupation(z,xi)
            return (phi@(w*f)-mom)/mom
        def jac(a):
            f=occupation(x-eta-t*k+a@phi,xi)
            v=w*f*(1+xi*f)
            return -((phi*v)@phi.T)/mom[:,None]
        # The local solution gives an excellent starting point without ODE continuation.
        sol=root(fun,t*beta,jac=jac,tol=1e-11)
        residual=np.max(np.abs(fun(sol.x)))
        if residual>1e-10:raise RuntimeError((xi,t,sol.message,residual))
        f=occupation(x-eta-t*k+sol.x@phi,xi)
        score0=eta-x
        D=np.sum(w*(entropy(f,xi)-entropy(g,xi)-score0*(f-g)))
        dO=np.sum(w*k*(f-g))
        # Convex competitors preserve number and energy exactly.
        for s in [.2,.6,.9]:
            h=(1-s)*g+s*f
            Dhg=np.sum(w*(entropy(h,xi)-entropy(g,xi)-score0*(h-g)))
            scoref=score0+t*k-sol.x@phi
            Dhf=np.sum(w*(entropy(h,xi)-entropy(f,xi)-scoref*(h-f)))
            identity=Dhg-D-t*np.sum(w*k*(h-f))-Dhf
            dual_res=max(dual_res,abs(float(identity))/n0)
            assert Dhg<=D+1e-11*n0
            assert t*np.sum(w*k*(h-f))<=1e-11*n0
        max_res=max(max_res,float(residual))
        min_margin=min(min_margin,float(1+sol.x[1]))
        results.append([float(t),float(D/n0),float(dO/n0),*map(float,sol.x)])
    return {"xi":xi,"eta0":eta,"number":float(n0),"energy":float(mom[1]),
            "reference_response":float(ref),"sigma2_projected":float(sig2),
            "sigma2_unprojected":float(raw),"projected_to_raw_width_ratio":float(np.sqrt(sig2/raw)),
            "max_relative_moment_residual":max_res,
            "max_three_point_identity_residual":dual_res,
            "min_inverse_temperature_coefficient":min_margin,
            "rows":results},(x,k,kp)

cases=[("MB",0,0.),("BE",1,-.5),("FD",-1,1.)]
allrows=[];stats={};fig,axes=plt.subplots(2,2,figsize=(10,7.5),layout="constrained")
plt.rcParams.update({"pdf.fonttype":42,"font.family":"DejaVu Sans"})
for i,(name,xi,eta) in enumerate(cases):
    r,curves=solve_case(xi,eta)
    # Independent quadrature refinement at both signed tilts.
    a,_=solve_case(xi,eta,32,[-1.5,.3,1.5])
    b,_=solve_case(xi,eta,128,[-1.5,.3,1.5])
    err=max(abs(np.array(a["rows"])[:,:3]-np.array(b["rows"])[:,:3]).ravel())
    assert err<2e-10
    r["quadrature_32_vs_128_max_difference"]=float(err)
    stats[name]={k:v for k,v in r.items() if k!="rows"}
    arr=np.array(r["rows"])
    for row in r["rows"]:allrows.append([name,*row])
    ax=axes.flat[i+1]
    for sign,color in [(-1,"#c05f29"),(1,"#1767a4")]:
        z=arr[arr[:,0]*sign>0]
        ax.plot(z[:,1],z[:,2],color=color,label="Finite-amplitude extremizer" if sign==1 else None)
        ax.plot(z[:,1],sign*np.sqrt(2*z[:,1]*r["sigma2_projected"]),color="#60646b",ls="--",
                label="Local Fisher approximation" if sign==1 else None)
    ax.axhline(0,color="#aaaaaa",lw=.6)
    ax.set_title(name+f" reference: eta = {eta:g}")
    ax.set_xlabel("Entropy budget / reference ray number")
    ax.set_ylabel("Response change / reference ray number")
    ax.grid(alpha=.18)
    if i==0:ax.legend(fontsize=8,frameon=False)
    if i==0:
        x,k,kp=curves;sel=x<12
        axes[0,0].plot(x[sel],k[sel],label="Bounded detector kernel",color="#1767a4")
        axes[0,0].plot(x[sel],kp[sel],label="Number-energy projected kernel (MB)",color="#9270a9")
axes[0,0].set(title="Which spectral shape does the detector see?",
              xlabel=r"$E/(k_{\rm B}T_*)$",ylabel="Dimensionless response kernel")
axes[0,0].legend(fontsize=8,frameon=False);axes[0,0].grid(alpha=.18)
fig.suptitle("Calibrated entropy-response frontiers: static analytic-family toy",fontsize=14)
fig.savefig(BASE/"figures/response_frontier.pdf")
fig.savefig(BASE/"figures/response_frontier.png",dpi=190)
plt.close(fig)
with (BASE/"cas/response_frontier.csv").open("w") as f:
    wr=csv.writer(f);wr.writerow(["statistics","tilt","entropy_per_number","response_per_number","number_multiplier","energy_multiplier"]);wr.writerows(allrows)
result={"status":"PASS_SCOPED_TOY","python":platform.python_version(),
        "kernel":"exp(-0.5*((x-4)/0.8)^2)","x_max":64,
        "quadrature":"piecewise Gauss-Legendre; 32/64/128 points per subinterval",
        "continuum_scope":"Finite domain numerical evaluation; tail to infinity is exponentially suppressed but no interval-certified quadrature is claimed.",
        "cases":stats}
(BASE/"cas/response_frontier_results.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
