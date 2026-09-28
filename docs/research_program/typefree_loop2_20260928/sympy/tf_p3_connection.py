"""Independent Christoffel-derivative check at the point; no ODE solver."""
import json
import sympy as sp

t, x, y, z = q = sp.symbols("x0 x1 x2 x3", real=True)
b, kap, cspeed = sp.symbols("b kappa c", positive=True)
lam = sp.symbols("lambda", real=True)
phi = -b*t*t-b*(x*x+y*y+z*z)/2+lam*t*t*x/2
eta = sp.diag(-1,1,1,1)
metric = sp.exp(2*phi)*eta
inverse = sp.exp(-2*phi)*eta
dg = [[[sp.diff(metric[i,j],q[k]) for k in range(4)]
       for j in range(4)] for i in range(4)]
Gamma = [[[sp.simplify(sum(inverse[a,e]*
    (dg[e][d][c]+dg[e][c][d]-dg[c][d][e])/2 for e in range(4)))
    for d in range(4)] for c in range(4)] for a in range(4)]
at0 = {v:0 for v in q}
def ricci_at(derivative=None):
    # R^a_{bcd}=d_c Gamma^a_{db}-d_d Gamma^a_{cb}+Gamma Gamma.
    # Gamma(0)=0, so Gamma Gamma and its first derivative vanish at 0.
    out=sp.zeros(4)
    for bidx in range(4):
        for didx in range(4):
            s=0
            for a in range(4):
                term=sp.diff(Gamma[a][didx][bidx],q[a])-sp.diff(Gamma[a][a][bidx],q[didx])
                if derivative is not None: term=sp.diff(term,q[derivative])
                s += term.subs(at0)
            out[bidx,didx]=sp.simplify(s)
    return out
R=ricci_at()
dR=ricci_at(0)
Rscalar=sp.trace(eta*R)
dRscalar=sp.trace(eta*dR)
G=sp.simplify(R-eta*Rscalar/2)
dG=sp.simplify(dR-eta*dRscalar/2)
jet2_lambda_free=all(not sp.diff(metric[i,j],q[k],q[l]).subs(at0).has(lam)
    for i in range(4) for j in range(4) for k in range(4) for l in range(4))
result={
 "sympy_version":sp.__version__,
 "curvature":"[nabla_c,nabla_d]v^a=R^a_bcd v^b",
 "metric_two_jet_lambda_free":jet2_lambda_free,
 "Gamma_at_origin_zero":all(g.subs(at0)==0 for plane in Gamma for row in plane for g in row),
 "ricci_at_origin":str(R.tolist()),
 "einstein_at_origin":str(G.tolist()),
 "d0_einstein_at_origin":str(dG.tolist()),
 "d0_T1_0":str(dG[1,0]/kap),
 "selected_acceleration_1":str(sp.simplify(-cspeed**2*(dG[1,0]/kap)/(6*b/kap))),
}
print(json.dumps(result,indent=2))
