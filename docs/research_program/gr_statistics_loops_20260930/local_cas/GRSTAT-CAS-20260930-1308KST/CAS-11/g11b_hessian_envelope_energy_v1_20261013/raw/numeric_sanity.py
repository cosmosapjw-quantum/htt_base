"""Ancillary (non-proof) sanity check: Taylor identity d_h = d^2 int_0^1 (1-t) h''(b+t d) dt, the 1/2 constant,
and d_h >= d^2/(2W) with W = sup_seg z(1+xi z), incl. physical endpoints a=0 (all) and a=1 (FD). mpmath 40 digits."""
import mpmath as mp, sympy as sp
mp.mp.dps = 40
t=sp.symbols('t'); print("sympy int_0^1 (1-t) dt =", sp.integrate(1-t,(t,0,1)))
xi={'MB':0,'BE':1,'FD':-1}
def h(s,f):
    x=xi[s]; xl=lambda u: u*mp.log(u) if u>0 else mp.mpf(0)
    return {'MB':xl(f)-f,'BE':xl(f)-xl(1+f),'FD':xl(f)+xl(1-f)}[s]
hp=lambda s,f: mp.log(f/(1+xi[s]*f)); hpp=lambda s,f: 1/(f*(1+xi[s]*f))
def breg(s,a,b): return h(s,a)-h(s,b)-hp(s,b)*(a-b)
worst=mp.inf
for s,pairs in {'MB':[(2.5,0.3),(0,1),(0.01,4)],'BE':[(3,0.2),(0,0.7),(0.4,5)],'FD':[(0.9,0.2),(0,0.5),(1,0.3),(0.05,0.95)]}.items():
    for a,b in pairs:
        a,b=mp.mpf(a),mp.mpf(b); d=a-b
        W=max(z*(1+xi[s]*z) for z in [a,b]+[a+(b-a)*k/2000 for k in range(2001)]+([mp.mpf(1)/2] if s=='FD' and min(a,b)<=0.5<=max(a,b) else []))
        lhs=breg(s,a,b); low=d**2/(2*W)
        if 0<a and (s!='FD' or a<1):
            tay=d**2*mp.quad(lambda u:(1-u)*hpp(s,b+u*d),[0,1]); print(s,float(a),float(b),"taylor_resid",mp.nstr(lhs-tay,5))
        print(s,float(a),float(b),"breg",mp.nstr(lhs,12),"lower",mp.nstr(low,12),"margin",mp.nstr(lhs-low,6)); worst=min(worst,lhs-low)
print("min margin",mp.nstr(worst,8))
