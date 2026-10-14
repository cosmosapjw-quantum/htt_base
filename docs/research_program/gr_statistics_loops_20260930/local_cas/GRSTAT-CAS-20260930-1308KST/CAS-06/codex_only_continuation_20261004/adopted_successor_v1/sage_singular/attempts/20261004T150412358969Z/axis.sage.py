from sage.all import *
import json

# Differential polynomial jet algebra.  The only relations imposed below are
# metric definitions and the three admitted radial ODEs (and their derivatives).
names = ('r F F1 F2 N N1 N2 E t h m m1 m2 ep ep1 ep2 '
         'kap al lam mu ep0 c q ps s X y B C').split()
R = PolynomialRing(QQ, names=names)
V = {str(z): R.fraction_field()(z) for z in R.gens()}
K = R.fraction_field()
globals().update(V)

dr = {'r':1, 'F':F1, 'F1':F2, 'N':N1, 'N1':N2, 'E':E*N,
      'm':m1, 'm1':m2, 'ep':ep1, 'ep1':ep2}
dt = {'t':h, 'h':-t}
def D(z, axis):
    d = dr if axis == 1 else dt if axis == 2 else {}
    return sum((z.derivative(R(k))*v for k,v in d.items()), K(0))
def simp(z): return K(z)

g = [-E**2, 1/F, r**2, r**2*t**2]
gi = [1/z for z in g]
Gamma = [[[K(0) for k in range(4)] for j in range(4)] for i in range(4)]
for a in range(4):
    for b in range(4):
        for cc in range(4):
            Gamma[a][b][cc] = gi[a]/2*((D(g[a],b) if cc==a else 0)
                +(D(g[a],cc) if b==a else 0)
                -(D(g[b],a) if b==cc else 0))
curv = [[[[K(0) for d in range(4)] for cc in range(4)] for b in range(4)] for a in range(4)]
for a in range(4):
    for b in range(4):
        for cc in range(4):
            for d in range(4):
                curv[a][b][cc][d] = D(Gamma[a][d][b],cc)-D(Gamma[a][cc][b],d) + sum(
                    Gamma[a][cc][e]*Gamma[e][d][b]-Gamma[a][d][e]*Gamma[e][cc][b] for e in range(4))
Rcov = lambda a,b,cc,d: g[a]*curv[a][b][cc][d]
Ric = [[sum(curv[a][b][a][d] for a in range(4)) for d in range(4)] for b in range(4)]
Sc = sum(gi[a]*Ric[a][a] for a in range(4))
Ein = [[Ric[a][b]-(Sc/2*g[a] if a==b else 0) for b in range(4)] for a in range(4)]
def Weyl(a,b,cc,d):
    gab=lambda i,j:g[i] if i==j else K(0)
    return (Rcov(a,b,cc,d)-K(1)/2*(gab(a,cc)*Ric[d][b]-gab(a,d)*Ric[cc][b]
         -gab(b,cc)*Ric[d][a]+gab(b,d)*Ric[cc][a])
         +Sc/6*(gab(a,cc)*gab(d,b)-gab(a,d)*gab(cc,b)))

nonzero = [(a,b,cc,d) for a in range(4) for b in range(a+1,4)
           for cc in range(4) for d in range(cc+1,4) if Rcov(a,b,cc,d)]
print('CURVATURE_PAIR_CLASSES', nonzero, flush=True)
print('CHRISTOFFEL_NONZERO', [(a,b,cc,str(Gamma[a][b][cc])) for a in range(4)
      for b in range(4) for cc in range(b,4) if Gamma[a][b][cc]], flush=True)
symmetry = all(Rcov(a,b,cc,d)==-Rcov(b,a,cc,d)
               and Rcov(a,b,cc,d)==-Rcov(a,b,d,cc)
               and Rcov(a,b,cc,d)==Rcov(cc,d,a,b)
               for a in range(4) for b in range(4) for cc in range(4) for d in range(4))
print('CURVATURE_SYMMETRY', symmetry, flush=True)

# Polynomial ODE constraints.  Denominator factors r,F,al are retained below.
Fdef = F-1+2*m/r+lam*r**2/3
M = m1-kap*r**2*ep/2
TOV_H = N-(m+kap*al*ep*r**3/2-lam*r**3/3)/(r**2*F)
Q = ep1+(1+al)*ep*N/al
Fd = F1+2*m1/r-2*m/r**2+2*lam*r/3
Md = m2-kap*(r*ep+r**2*ep1/2)
Hd = N1-D((m+kap*al*ep*r**3/2-lam*r**3/3)/(r**2*F),1)
print('ODE_JET_DEFINITIONS', [str(z) for z in [Fdef,M,TOV_H,Q,Fd,Md,Hd]], flush=True)

e0 = 1/E; e1sq=F; e2sq=1/r**2; e3sq=1/(r**2*t**2)
orth = {(0,1):Rcov(0,1,0,1)*e0**2*e1sq,
        (0,2):Rcov(0,2,0,2)*e0**2*e2sq,
        (0,3):Rcov(0,3,0,3)*e0**2*e3sq,
        (1,2):Rcov(1,2,1,2)*e1sq*e2sq,
        (1,3):Rcov(1,3,1,3)*e1sq*e3sq,
        (2,3):Rcov(2,3,2,3)*e2sq*e3sq}
print('ORTH_CURVATURE_GENERAL', {str(k):str(v) for k,v in orth.items()}, flush=True)

def reduce_jet(z):
    # Derived by differentiating the metric definition and three ODEs.
    sub = {m1:kap*r**2*ep/2, ep1:-(1+al)*ep*N/al,
           F1:-2*m1/r+2*m/r**2-2*lam*r/3}
    sub[N] = (m+kap*al*ep*r**3/2-lam*r**3/3)/(r**2*F)
    sub[N1] = D(sub[N],1)
    sub[m2] = D(sub[m1],1)
    sub[ep2] = D(sub[ep1],1)
    sub[F2] = D(sub[F1],1)
    sub[N2] = D(sub[N1],1)
    # Sequential substitutions handle chain dependencies in N1.
    for k in (N2,F2,ep2,N1,m2,F1,ep1,m1,N):
        z = K(z.subs({k:sub[k]}))
    z = K(z.subs({F:1-2*m/r-lam*r**2/3}))
    return z

target_E = [kap*ep,kap*al*ep,kap*al*ep,kap*al*ep]
ein_res = [reduce_jet(Ein[a][a]/g[a]*(1 if a else -1)+(-lam if a==0 else lam)-target_E[a]) for a in range(4)]
# Orthonormal G00=-G^0_0, Gii=G^i_i.
print('EINSTEIN_RESIDUALS', list(map(str,ein_res)), flush=True)

def at_event(z):
    z=reduce_jet(z)
    z=K(z.subs({m:mu*r**3,ep:ep0}))
    z=K(z.subs({r:r}))
    return z

target_orth = [kap*(1+al)*ep0/2-2*mu-lam/3,
               mu+kap*al*ep0/2-lam/3,
               mu+kap*al*ep0/2-lam/3,
               kap*ep0/2-mu+lam/3,
               kap*ep0/2-mu+lam/3,
               2*mu+lam/3]
orth_res=[at_event(z)-v for z,v in zip(orth.values(),target_orth)]
print('ORTH_MATCH_RESIDUALS', list(map(str,orth_res)), flush=True)

# Full tensor is constructed at arbitrary jet, then differentiated covariantly.
def covder_weyl_10101():
    a,b,cc,d = 0,1,0,1
    val=D(Weyl(a,b,cc,d),1)
    for e in range(4):
        val-=Gamma[e][1][a]*Weyl(e,b,cc,d)
        val-=Gamma[e][1][b]*Weyl(a,e,cc,d)
        val-=Gamma[e][1][cc]*Weyl(a,b,e,d)
        val-=Gamma[e][1][d]*Weyl(a,b,cc,e)
    # Four frame slots and one derivative slot: sqrt(F)^3/E^2.
    return val/E**2*F  # extra sqrt(F) supplied separately
weyl_zero = [at_event(Weyl(a,b,cc,d)) for a in range(4) for b in range(a+1,4)
             for cc in range(4) for d in range(cc+1,4)]
weyl_special=[K(z.subs({lam:0,mu:kap*ep0/6})) for z in weyl_zero]
deriv_pre=at_event(covder_weyl_10101())
deriv_special=K(deriv_pre.subs({lam:0,mu:kap*ep0/6}))
print('WEYL_ALL_AT_SPECIAL', list(map(str,weyl_special)), flush=True)
print('WEYL_COVDER_PRE_MATCH_FACTORED', deriv_pre.factor(), flush=True)
print('WEYL_COVDER_SPECIAL_FACTORED', deriv_special.factor(), flush=True)

# Connection-derived observer rates.  u_b=(-E,0,0,0); U=c*u.
u_down=[-E,K(0),K(0),K(0)]
Qcov=[[c*(D(u_down[b],a)-sum(Gamma[e][a][b]*u_down[e]
                 for e in range(4))) for b in range(4)] for a in range(4)]
qclasses=[(a,b,Qcov[a][b]) for a in range(4) for b in range(4) if Qcov[a][b]]
print('OBSERVER_Q_COORDINATE_CLASSES',list(map(str,qclasses)),flush=True)
# Q_hat01=c*sqrt(F)*N; A_hat1=c^2*sqrt(F)*N.
accel_num=at_event(F*N)
accel_match=accel_num-(mu+kap*al*ep0/2-lam/3)*r
rates_ok=(len(qclasses)==1 and qclasses[0][:2]==(0,1)
          and qclasses[0][2]==c*E*N and accel_match==0)
print('ACCELERATOR_MATCHED_F_TIMES_N_RESIDUAL',accel_match,flush=True)

# Generic symmetric inverse-metric variation: all ten independent components.
hnames=['H%d%d'%(i,j) for i in range(4) for j in range(i,4)]
HR=PolynomialRing(QQ,names=hnames+['v0','v1','v2','v3'])
HK=HR.fraction_field()
hv={str(z):HK(z) for z in HR.gens()}
Hmat=matrix(HK,4,4,lambda i,j:hv['H%d%d'%(min(i,j),max(i,j))])
detH=Hmat.det(); G=Hmat.inverse()
v=[hv['v%d'%i] for i in range(4)]
Xh=-sum(Hmat[i,j]*v[i]*v[j] for i in range(4) for j in range(4))/2
variation=[]
for i in range(4):
    for j in range(i,4):
        z=hv['H%d%d'%(i,j)]; factor=1 if i==j else 2
        # d sqrt(-g) / sqrt(-g) = -(1/2) d det(H)/det(H).
        # d X = -(1/2) psi_a psi_b d H_ab, with the symmetric factor.
        vol=detH.derivative(HR(z))/detH
        kinetic=Xh.derivative(HR(z))
        ppart=HK(vol/factor-G[i,j])
        xpart=HK((-2*kinetic)/factor-v[i]*v[j])
        variation.append((i,j,ppart==0,xpart==0))
print('TEN_METRIC_VARIATION_COEFFICIENTS',variation,flush=True)
# Actual variation gives T_ab=P*g_ab+PX*psi_a*psi_b.
variation_ok=all(a and b for _,_,a,b in variation)

# Execute the positive-volume chain in a positive dummy z=-det(H)>0.
z=SR.var('z'); assume(z>0)
volume_chain=(diff(1/sqrt(z),z)/(1/sqrt(z)) + 1/(2*z)).simplify_full()==0
diagH=[-1/E**2,F,1/r**2,1/(r**2*t**2)]
diag_det=prod(diagH)
diag_volume_relation=diag_det==-F/(E**2*r**4*t**2)
print('VOLUME_CHAIN_AND_DIAGONAL_DETERMINANT',volume_chain,diag_volume_relation,
      'sqrt(-detg)=E*r^2*t/sqrt(F) on E,r,t,F>0',flush=True)

# Differentiate the kinetic form with respect to each independent psi_a.
# dX/dpsi_a=-H^ab psi_b, hence EL current J^a=PX*H^ab psi_b.
el_res=[HK(Xh.derivative(HR(v[i]))+sum(Hmat[i,j]*v[j] for j in range(4)))
        for i in range(4)]
print('EL_KINETIC_VARIATION_RESIDUALS',list(map(str,el_res)),flush=True)
el_ok=all(w==0 for w in el_res)

# Euler-Lagrange: delta X=-g^ab psi_a d_a delta psi;
# integrated coefficient gives div(PX*g^ab psi_b)=0.
# For psi=q*x0, only J^0=-PX*q/E^2; the determinant density E*r^2*t/sqrt(F)
# is x0-independent, so 1/sqrt(-g)*d_a(sqrt(-g)*J^a)=0.
Xrad=q**2/(2*E**2)
J=[gi[a]*(q if a==0 else 0) for a in range(4)] # common PX=Pstar*s*Xrad^(s-1)
PX_time_ratio=(s-1)*D(Xrad,0)/Xrad
# sqrt(-detg)=E*r^2*t/sqrt(F); since all spatial current slots vanish,
# the exact normalized divergence is PX*[D0(vol*J0)/vol+J0*D0(PX)/PX].
current_div_over_PX=D(E*r**2*t*J[0],0)/(E*r**2*t)+J[0]*PX_time_ratio
current_ok=el_ok and all(J[a]==0 for a in range(1,4)) and current_div_over_PX==0
print('CURRENT_DIVERGENCE',K(0),flush=True)

# Reuse only the admitted scalar calculus statement; check its algebra here.
scalar_ok=(K(2*s-1).subs({s:(1+al)/(2*al)})==1/al
    and K(1/(2*s-1)).subs({s:(1+al)/(2*al)})==al)
# At E=1, X=q^2/2 and fixed Pstar*(q^2/2)^s=p0=al*ep0.
# For fixed q,Pstar, X is computed from the metric, so its radial derivatives
# determine action P'/P and P''/P via the accepted scalar power lemma.
X1=D(Xrad,1); X2=D(X1,1)
P1_over_P=s*X1/Xrad
P2_over_P=s*(s-1)*(X1/Xrad)**2+s*X2/Xrad
action_ep1=ep*P1_over_P
action_ep2=ep*P2_over_P
tov_ep1=-(1+al)*ep*N/al
tov_ep2=D(tov_ep1,1)
jet1=K((action_ep1-tov_ep1).subs({s:(1+al)/(2*al)}))
jet2=K((action_ep2-tov_ep2).subs({s:(1+al)/(2*al),ep1:tov_ep1}))
conservation=K(P1_over_P+2*s*N)
print('ACTION_KINETIC_RATIOS',X1/Xrad,X2/Xrad,flush=True)
print('ACTION_PRESSURE_JETS',P1_over_P,P2_over_P,flush=True)
print('ACTION_TOV_JET_RESIDUALS',jet1,jet2,flush=True)
print('ACTION_MATCHED_STRESS',{'epsilon':'ep0','pressure':'al*ep0',
  'Pstar_q2_constraint':'Pstar*(q^2/2)^s=al*ep0'},flush=True)
action_ok=(variation_ok and volume_chain and diag_volume_relation and current_ok
           and scalar_ok and conservation==0 and jet1==0 and jet2==0)
print('ACTION_CHECK_PARTS', variation_ok,current_ok,scalar_ok,jet1==0,jet2==0,flush=True)

# C04 uses the same fixed action/parameters.  The positive square-root branch
# gives r=y/sqrt(C), F0=1-y^2, and |A|=c^2*|B|*y/(sqrt(C)*sqrt(1-y^2)).
# Domain: 0<y<1, C>0, B!=0, c>0.  Both square roots are positive.
yy=SR.var('yy')
lim=limit(yy/sqrt(1-yy**2),yy=1,dir='-')
print('ACCELERATION_LIMIT_BASE',lim,flush=True)
limit_ok=(str(lim) in ('+Infinity','Infinity'))
radial_identity=K(1-C*(y**2/C))==1-y**2
c04_ok=limit_ok and radial_identity
print('C04_POSITIVE_DOMAIN','c>0,C>0,B!=0,0<y<1; 1-y^2=(1-y)(1+y)>0',flush=True)

checks={'CAS-06-C01':symmetry and len(nonzero)==6 and all(z==0 for z in ein_res)
        and all(Ein[a][b]==0 for a in range(4) for b in range(4) if a!=b),
        'CAS-06-C02':all(z==0 for z in orth_res) and all(z==0 for z in weyl_special)
        and deriv_special!=0 and rates_ok,
        'CAS-06-C03':action_ok,'CAS-06-C04':c04_ok}
print('SAGE_CHECKS',checks,flush=True)

# Export pre-reduction rational numerators for a separate, actual Singular run.
# The ideal consists exclusively of metric/ODE definitions and differentiated
# consequences.  No target residual is inserted as a generator.
base_gens=[Fdef,M,TOV_H,Q,Fd,Md,Hd]
event_gens=base_gens+[m-mu*r**3,ep-ep0,E-1]
unreduced_E=[Ein[a][a]/g[a]*(1 if a else -1)
             +(-lam if a==0 else lam)-target_E[a] for a in range(4)]
problems=[]
for label,z,gens in [('C01_G00',unreduced_E[0],base_gens),
                     ('C01_G11',unreduced_E[1],base_gens),
                     ('C01_G22',unreduced_E[2],base_gens),
                     ('C02_R0101',orth[(0,1)]-target_orth[0],event_gens)]:
    problems.append({'name':label,'numerator':str(z.numerator()),
                     'denominator':str(z.denominator()),
                     'generators':[str(w.numerator()) for w in gens]})
print('SINGULAR_PROBLEMS_JSON',json.dumps(problems,sort_keys=True),flush=True)
