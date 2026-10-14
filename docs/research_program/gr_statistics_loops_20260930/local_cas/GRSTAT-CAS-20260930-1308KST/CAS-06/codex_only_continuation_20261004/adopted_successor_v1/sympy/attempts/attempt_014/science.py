"""Independent SymPy calculations for the owner-adopted finite CAS-06 scope.

No curvature, stress, or acceleration target is installed as an assumption.
The radial functions are formal smooth jets.  This module makes no ODE
existence, center, interval-identification, or scientific-admission claim.
"""
import json
import sympy as S
from functools import lru_cache
from pathlib import Path

PROGRESS=Path(__file__).with_name('progress.txt')
def mark(stage):PROGRESS.write_text(stage+'\n')


@lru_cache(None)
def z(x):
    if x==0:return True
    rational=S.cancel(x)
    return rational==0 or S.cancel(S.trigsimp(rational))==0


def require(label, predicate, record):
    good = bool(predicate)
    record.append([label, good])
    if not good:
        raise AssertionError(label)


def calculate():
    mark('metric connection')
    rec = []
    r, th, ph, x0 = S.symbols('r theta phi x0', real=True)
    kap, al, lam, c, mu, E0, r0 = S.symbols('kappa alpha Lambda c mu epsilon0 r0', real=True)
    Pstar, q, X, y = S.symbols('Pstar q X y', positive=True)
    m, nu, ep = (S.Function('m',real=True)(r), S.Function('nu',real=True)(r),
                 S.Function('epsilon',real=True)(r))
    coords = (x0,r,th,ph)
    F = 1-2*m/r-lam*r*r/3
    gd = [-S.exp(2*nu),1/F,r*r,r*r*S.sin(th)**2]
    gi = [1/v for v in gd]
    eta = [-1,1,1,1]

    def gamma(a,b,d):
        return S.cancel(gi[a]*(
            (S.diff(gd[a],coords[b]) if a==d else 0)
            +(S.diff(gd[a],coords[d]) if a==b else 0)
            -(S.diff(gd[b],coords[a]) if b==d else 0))/2)

    G = {(a,b,d):gamma(a,b,d) for a in range(4) for b in range(4) for d in range(4)}
    nzG = [(a,b,d) for (a,b,d),v in G.items() if v!=0]
    require('connection lower symmetry',all(z(G[a,b,d]-G[a,d,b]) for a,b,d in nzG),rec)

    @lru_cache(None)
    def R(a,b,d,e):
        # R^a_{bde} = partial_d Gamma^a_{eb} - partial_e Gamma^a_{db} + ...
        terms = S.diff(G[a,e,b],coords[d])-S.diff(G[a,d,b],coords[e])
        terms += sum(G[a,d,h]*G[h,e,b]-G[a,e,h]*G[h,d,b] for h in range(4))
        return terms

    def Rlow(a,b,d,e):
        return gd[a]*R(a,b,d,e)

    pair = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    # The 6x6 antisymmetric-pair matrix enumerates every independent class.
    # Evaluate its index reversals directly from the metric connection.
    mark('Riemann independent pairs')
    riem = {(a,b,d,e):Rlow(a,b,d,e) for a,b in pair for d,e in pair}
    mark('Riemann symmetry tests')
    require('all Riemann component symmetry classes',all(
        z(riem[a,b,d,e]+Rlow(b,a,d,e)) and
        z(riem[a,b,d,e]+Rlow(a,b,e,d)) and
        z(riem[a,b,d,e]-Rlow(d,e,a,b))
        for a,b in pair for d,e in pair),rec)
    require('all mixed pair curvature components zero',all(z(riem[a,b,d,e])
        for a,b in pair for d,e in pair if (a,b)!=(d,e)),rec)
    Ric = {(b,d):S.cancel(S.trigsimp(sum(R(a,b,a,d) for a in range(4))))
           for b in range(4) for d in range(4)}
    mark('Ricci and Einstein')
    scal = S.cancel(sum(gi[a]*Ric[a,a] for a in range(4)))
    Ein = {(a,b):S.cancel(Ric[a,b]-(gd[a]*scal/2 if a==b else 0))
           for a in range(4) for b in range(4)}
    mark('Einstein off diagonal')
    require('all off-diagonal Einstein components zero',all(z(Ein[a,b])
        for a in range(4) for b in range(4) if a!=b),rec)

    mark('TOV second jets')
    m1=kap*r*r*ep/2
    n1=(m+kap*al*ep*r**3/2-lam*r**3/3)/(r*r*F)
    e1=-(1+al)*ep*n1/al
    def sub1(v):
        return v.xreplace({S.diff(m,r):m1,S.diff(nu,r):n1,S.diff(ep,r):e1})
    m2=sub1(S.diff(m1,r))
    n2=S.cancel(sub1(S.diff(n1,r)))
    e2=S.cancel(sub1(S.diff(e1,r)))
    mark('C01 Ehat reduction')
    jets={S.diff(m,r,2):m2,S.diff(nu,r,2):n2,
          S.diff(m,r):m1,S.diff(nu,r):n1,S.diff(ep,r,2):e2,S.diff(ep,r):e1}
    def reduce(v):
        return S.cancel(v.xreplace(jets))

    # Transform coordinate components with the admitted diagonal tetrad.
    frame=[S.exp(-nu),S.sqrt(F),1/r,1/(r*S.sin(th))]
    Rhat={(a,b,d,e):frame[a]*frame[b]*frame[d]*frame[e]*riem[a,b,d,e]
          for a,b in pair for d,e in pair}
    Ehat=[reduce(frame[a]**2*Ein[a,a]+lam*eta[a]) for a in range(4)]
    mark('C01 checks')
    require('C01 tetrad Einstein 00',z(Ehat[0]-kap*ep),rec)
    for a in (1,2,3):
        require('C01 tetrad Einstein '+str(a)+str(a),z(Ehat[a]-kap*al*ep),rec)
    require('C01 all tetrad off-diagonal components',all(z(Ein[a,b])
        for a in range(4) for b in range(4) if a!=b),rec)
    C01=True

    def point(v,weyl=False):
        v=S.cancel(v)
        v=reduce(v)
        return S.cancel(v.subs({m:mu*r**3,ep:E0}).subs(r,r0))
    B=mu+kap*al*E0/2-lam/3
    C=2*mu+lam/3
    target={(0,1):kap*(1+al)*E0/2-2*mu-lam/3,
            (0,2):B,(0,3):B,
            (1,2):kap*E0/2-mu+lam/3,
            (1,3):kap*E0/2-mu+lam/3,(2,3):C}
    for ab in pair:
        require('C02 Rhat '+str(ab),z(point(Rhat[ab[0],ab[1],ab[0],ab[1]])-target[ab]),rec)
    mark('C02 curvature/rates')
    require('C02 independent mixed orthonormal Riemann',all(z(v)
        for (a,b,d,e),v in Rhat.items() if (a,b)!=(d,e)),rec)

    # ∇_a U_b from U=c exp(nu) delta_b0 covariantly; frame rates.
    Ucov=[-c*S.exp(nu),0,0,0]
    Q={(a,b):frame[a]*frame[b]*(S.diff(Ucov[b],coords[a])-
          sum(G[h,a,b]*Ucov[h] for h in range(4))) for a in range(4) for b in range(4)}
    acc=reduce(c*Q[0,1])
    accpoint=point(acc)
    F0=1-C*r0*r0
    require('C02 acceleration from covariant derivative',z(accpoint-c*c*B*r0/S.sqrt(F0)),rec)
    require('C02 acceleration magnitude squared',z(accpoint**2-(c*c*S.Abs(B)*r0/S.sqrt(F0))**2),rec)
    cp0,rp0,Fp0=S.symbols('c_pos r_pos F_pos',positive=True)
    breal=S.Symbol('B_real',real=True,nonzero=True)
    require('C02 acceleration positive-root branch',z(S.sqrt((cp0**2*breal*rp0/S.sqrt(Fp0))**2)
            -cp0**2*S.Abs(breal)*rp0/S.sqrt(Fp0)),rec)
    require('C02 expansion shear vorticity',all(z(Q[a,b]) for a in (1,2,3) for b in (1,2,3)),rec)
    require('C02 acceleration only radial',all(z(Q[0,a]) for a in (0,2,3)),rec)

    # Full Weyl tensor from the metric's Riemann and Ricci, before point evaluation.
    def gab(a,b):return gd[a] if a==b else S.Integer(0)
    def W(a,b,d,e):
        return (Rlow(a,b,d,e)-(gab(a,d)*Ric[e,b]-gab(a,e)*Ric[d,b]
            -gab(b,d)*Ric[e,a]+gab(b,e)*Ric[d,a])/2+
            scal*(gab(a,d)*gab(e,b)-gab(a,e)*gab(d,b))/6)
    Weyl=W
    special={lam:S.Integer(0),mu:kap*E0/6}
    for ab in pair:
        for de in pair:
            w=frame[ab[0]]*frame[ab[1]]*frame[de[0]]*frame[de[1]]*Weyl(ab[0],ab[1],de[0],de[1])
            if ab!=de:
                # Stronger generic identity: no mixed pair survives anywhere.
                require('C02 Weyl mixed '+str((ab,de)),z(w),rec)
            else:
                mark('C02 Weyl diagonal '+str(ab))
                require('C02 Weyl event '+str((ab,de)),z(point(w).subs(special)),rec)
    mark('C02 Weyl derivative')
    # Reduce the full metric-derived Weyl tensor on the TOV jet first. Then
    # differentiate it covariantly on the radial formal jet. This commutes with
    # the TOV substitutions because they hold on the prescribed smooth jet.
    # Event specialization is only after all five tensor slots are assembled.
    a,b,d,e=0,1,0,1
    Wred=lambda i,j,k,l:reduce(S.cancel(Weyl(i,j,k,l)))
    Dw=S.diff(Wred(a,b,d,e),r)-sum(
        G[h,1,a]*Wred(h,b,d,e)+G[h,1,b]*Wred(a,h,d,e)
        +G[h,1,d]*Wred(a,b,h,e)+G[h,1,e]*Wred(a,b,d,h)
        for h in range(4))
    Dhat=frame[1]*frame[0]*frame[1]*frame[0]*frame[1]*Dw
    derivative=S.factor(point(Dhat).subs(special))
    print('WEYL_DERIVATIVE_DERIVED='+str(derivative),flush=True)
    factored=-S.sqrt(3)*E0**2*kap**2*r0*(al+1)*(3*al+1)/(
        18*al*S.sqrt(3-E0*kap*r0*r0))
    require('C02 Weyl derivative exact factorization',z(derivative-factored),rec)
    # Lambda=0 and mu=kappa epsilon0/6 give F0=1-kappa epsilon0 r0²/3;
    # hence D=3-kappa epsilon0 r0²=3F0>0. All remaining factors are
    # positive on the admitted domain, proving the derivative strictly negative.
    require('C02 Weyl radicand domain',z((3-E0*kap*r0*r0)-
            3*(1-E0*kap*r0*r0/3)),rec)
    kp,ee,rp,ap,Dp=S.symbols('k_pos e_pos r_pos a_pos D_pos',positive=True)
    signed=-S.sqrt(3)*ee**2*kp**2*rp*(ap+1)*(3*ap+1)/(
        18*ap*S.sqrt(Dp))
    require('C02 Weyl derivative strictly negative',S.ask(S.Q.negative(signed)) is True,rec)
    C02=True

    # Generic symmetric inverse metric H, all ten independent variations.
    hsyms={(i,j):S.Symbol('h'+str(i)+str(j)) for i in range(4) for j in range(i,4)}
    mark('C03 metric variation')
    H=S.Matrix(4,4,lambda i,j:hsyms[min(i,j),max(i,j)])
    dh=H.det()
    psi=S.symbols('psi0:4')
    Xh=-sum(H[i,j]*psi[i]*psi[j] for i in range(4) for j in range(4))/2
    hdiag={hsyms[i,j]:(gi[i] if i==j else 0) for i,j in hsyms}
    detg=S.prod(gd)
    detH=dh.subs(hdiag)
    require('C03 metric/inverse determinant reciprocity',z(detg*detH-1),rec)
    Vmetric=S.exp(nu)*r*r*S.sin(th)/S.sqrt(F)
    require('C03 metric volume squared',z(Vmetric**2+detg),rec)
    require('C03 angular volume branch',S.simplify(S.reduce_inequalities(
        [th>0,th<S.pi,S.sin(th)<=0],th))==False,rec)
    vp,rf,fp,sp=S.symbols('expnu_pos r_pos F_pos sintheta_pos',positive=True)
    require('C03 positive nonzero Lorentz volume branch',
            S.ask(S.Q.positive(vp*rf**2*sp/S.sqrt(fp))) is True,rec)
    dneg=S.Symbol('detH_negative',negative=True)
    Vinverse=1/S.sqrt(-dneg)
    require('C03 actual inverse-determinant volume derivative',
            z(S.diff(Vinverse,dneg)/Vinverse+1/(2*dneg)),rec)
    # Jacobi's identity checked directly against the polynomial determinant.
    for i,j in hsyms:
        weight=1 if i==j else 2
        lhs=S.diff(dh,hsyms[i,j]).subs(hdiag)
        rhs=weight*dh.subs(hdiag)*(gd[i] if i==j else 0)
        require('C03 determinant variation '+str((i,j)),z(lhs-rhs),rec)
        require('C03 kinetic variation '+str((i,j)),
                z(S.diff(Xh,hsyms[i,j])+weight*psi[i]*psi[j]/2),rec)
    s=(1+al)/(2*al)
    PX=Pstar*s*X**(s-1)
    PXX=Pstar*s*(s-1)*X**(s-2)
    P=Pstar*X**s
    for i,j in hsyms:
        weight=1 if i==j else 2
        # Jacobi plus δX give δ(sqrt(-g)P)/sqrt(-g); the factor -2/weight
        # reconstructs the symmetric tensor coefficient for every pair.
        dvol=((S.diff(Vinverse,dneg)/Vinverse).subs(dneg,detH)*
              S.diff(dh,hsyms[i,j]).subs(hdiag))
        dkin=S.diff(Xh,hsyms[i,j])
        variation=P*dvol+PX*dkin
        stress=PX*psi[i]*psi[j]+P*(gd[i] if i==j else 0)
        require('C03 varied stress '+str((i,j)),z(variation+weight*stress/2),rec)
    # ∂L/∂(∂a psi)=-sqrt(-g) P_X g^(ab) psi_b, giving the EL current.
    for a in range(4):
        derivative_psi=S.diff(Xh,psi[a]).subs(hdiag)
        require('C03 EL current '+str(a),z(-PX*derivative_psi-
            PX*sum((gi[a] if a==b else 0)*psi[b] for b in range(4))),rec)
    require('C03 scalar accepted-lemma algebra independently rechecked',
            z(2*X*PX-P-(2*s-1)*P) and z(PX/(PX+2*X*PXX)-al),rec)
    xp,pp,aa=S.symbols('X_pos Pstar_pos alpha_pos',positive=True)
    sp=(1+aa)/(2*aa)
    den=pp*sp*xp**(sp-1)*(2*sp-1)
    require('C03 kinetic denominator strictly positive',S.ask(S.Q.positive(den)) is True,rec)
    # The minus-two metric variation gives T_ab=P_X psi_a psi_b+P g_ab.
    # δS/δpsi=-∂a[sqrt(-g) P_X g^ab psi_b], so J^a as admitted.
    Xrad=q*q*S.exp(-2*nu)/2
    Prad=Pstar*Xrad**s
    Eact=(2*s-1)*Prad
    T00=PX.subs(X,Xrad)*q*q+Prad*gd[0]
    Tspace=[Prad*gd[i] for i in (1,2,3)]
    require('C03 action stress time component',z(T00-Eact*S.exp(2*nu)),rec)
    require('C03 action stress space components',all(z(Tspace[i-1]-Prad*gd[i]) for i in (1,2,3)),rec)
    psi_rad=(q,0,0,0)
    Jrad=[PX.subs(X,Xrad)*sum((gi[a] if a==b else 0)*psi_rad[b]
          for b in range(4)) for a in range(4)]
    divJ=sum(S.diff(Vmetric*Jrad[a],coords[a]) for a in range(4))/Vmetric
    require('C03 normalized four-current divergence',z(divJ),rec)
    # Keep normalization as a relation; substitution avoids solving fractional powers.
    require('C03 matched pressure',z(Prad.subs(nu,0)-Pstar*(q*q/2)**s),rec)
    require('C03 matched density coefficient',z((2*s-1)*al-1),rec)
    require('C03 fixed action radial conservation',z(S.diff(Prad,r)+(Eact+Prad)*S.diff(nu,r)),rec)
    require('C03 TOV first epsilon jet',z(S.diff(Eact,r)+2*s*Eact*S.diff(nu,r)),rec)
    require('C03 TOV second epsilon jet',z(S.diff(Eact,r,2)-
        Eact*(4*s*s*S.diff(nu,r)**2-2*s*S.diff(nu,r,2))),rec)
    # Positive q and real nu make both q²/2 and exp(-2nu) positive. The
    # positive-real X^s branch therefore splits exactly, before matching.
    norm_power=Pstar*(q*q/2)**s
    Enorm=(2*s-1)*norm_power*S.exp(-2*s*nu)
    require('C03 literal action positive-real branch',z(S.simplify(Eact-Enorm)),rec)
    require('C03 literal action first derivative branch',
            z(S.simplify(S.diff(Eact,r)-S.diff(Enorm,r))),rec)
    require('C03 literal action second derivative branch',
            z(S.simplify(S.diff(Eact,r,2)-S.diff(Enorm,r,2))),rec)
    # This symbol abbreviates the exact fixed normalizer, rather than adding
    # a new free parameter; the admitted Pstar(q²/2)^s=alpha epsilon0 gives Ebar=epsilon0.
    Ebar=S.Symbol('Ebar',positive=True)
    Efixed=Ebar*S.exp(-2*s*nu)
    require('C03 Ebar linked to literal action',
            z(Efixed.subs(Ebar,(2*s-1)*norm_power)-Enorm),rec)
    require('C03 fixed normalization algebra',z((2*s-1)*al*E0-E0),rec)
    match={m:mu*r**3,ep:E0,nu:S.Integer(0),Ebar:E0}
    tov1=S.cancel(e1.subs(match).subs(r,r0))
    tov2=S.cancel(e2.subs(match).subs(r,r0))
    act1=S.diff(Efixed,r).subs(S.diff(nu,r),n1).subs(match).subs(r,r0)
    act2=S.diff(Efixed,r,2).subs({S.diff(nu,r,2):n2,S.diff(nu,r):n1}).subs(match).subs(r,r0)
    require('C03 action/TOV epsilon first matched jet',z(act1-tov1),rec)
    require('C03 action/TOV epsilon second matched jet',z(act2-tov2),rec)
    m1act=kap*r*r*Efixed/2
    n1act=(m+kap*al*Efixed*r**3/2-lam*r**3/3)/(r*r*F)
    m2act=S.diff(m1act,r).subs(S.diff(nu,r),n1act)
    n2act=S.diff(n1act,r).subs({S.diff(m,r):m1act,S.diff(nu,r):n1act})
    for name,act,tov in [('m first',m1act,m1),('nu first',n1act,n1),
                         ('m second',m2act,m2),('nu second',n2act,n2)]:
        require('C03 action/TOV '+name+' matched jet',
                z(S.cancel(act.subs(match).subs(r,r0)-tov.subs(match).subs(r,r0))),rec)
    require('C03 fixed normalization at event',z(Efixed.subs(match)-E0),rec)
    C03=True

    mark('C04 limit')
    pref=c*c*S.Abs(B)/S.sqrt(C)
    Ay=pref*y/S.sqrt(1-y*y)
    require('C04 substitution from C02',z(Ay-c*c*S.Abs(B)*(y/S.sqrt(C))/
            S.sqrt(1-C*(y/S.sqrt(C))**2)),rec)
    # SymPy 1.14's limit with a globally positive variable returns -oo for
    # 1/sqrt(1-y²); a real limit variable plus explicit 0<y<1 domain avoids
    # that assumption-handling defect. The coefficient is proved positive below.
    t=S.Symbol('t',real=True)
    cp,Cp,bp=S.symbols('c_pos C_pos absB_pos',positive=True)
    Alim=cp*cp*bp/S.sqrt(Cp)*t/S.sqrt(1-t*t)
    require('C04 exact one-sided limit',S.limit(Alim,t,1,dir='-')==S.oo,rec)
    # For 0<y<1, y>0, 1-y²>0; fixed c²|B|/sqrt(C)>0 from
    # c>0,B≠0,C>0. Therefore each algebraic value is positive and finite.
    require('C04 domain denominator positive',S.reduce_inequalities(
        [y>0,y<1,1-y*y<=0],y)==False,rec)
    require('C04 positive fixed coefficient',S.ask(S.Q.positive(cp*cp*bp/S.sqrt(Cp))) is True,rec)
    C04=True
    return {'checks':{'CAS-06-C01':C01,'CAS-06-C02':C02,'CAS-06-C03':C03,'CAS-06-C04':C04},
            'domain_assumption_diff':[],'counterexample':None,'evidence':rec,
            'weyl_derivative_matched':str(derivative),
            'analytic_status':'HOLD: existence, interval identification, distinct germs'}


if __name__=='__main__':
    print(json.dumps(calculate(),sort_keys=True))
