#!/usr/bin/env python3
"""Independent R8 SymPy axis: exact algebra plus explicit conditional proofs."""
import hashlib
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import sympy as s

ROOT = Path(__file__).resolve().parents[5]
RUN = ROOT / '.agent-harness/runs/R8-AC-20260909'
CONTRACT_SHA = '5ff7f84db01b6871f74f7c60b5c36430a4cae93735466e277bd9c4019ab22723'
checks = {}


def zero(value):
    values = list(value) if isinstance(value, s.MatrixBase) else [value]
    assert all(s.simplify(s.expand(v)) == 0 for v in values), values


def record(key, scope, proof, details):
    checks[key] = dict(status='PASS', scope=scope, proof=proof, details=details,
                       domain_assumption_diff=[], counterexample=None)


def verify():
    assert s.__version__ == '1.14.0', s.__version__
    assert hashlib.sha256((RUN/'CAS_CONTRACT.json').read_bytes()).hexdigest() == CONTRACT_SHA
    contract = json.loads((RUN/'CAS_CONTRACT.json').read_text())
    for ref in contract['identity']['source_input_hashes']:
        assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest() == ref['sha256']
    assert json.loads((ROOT/'.agent-harness/context/CONTEXT_INDEX.json').read_text())['context_version'] == '2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4'

    # O1: the two named perturbation lemmas are pointwise in the SAME R.
    # Parameterize each nonnegative residual by bound + nonnegative slack.
    bq, bo, eq, eo = s.symbols('bq bo eq eo', nonnegative=True)
    q0, o0 = s.symbols('q0 o0', positive=True)
    excess = ((bq+eq)**2-bq**2)/q0**2 + ((bo+eo)**2-bo**2)/o0**2
    sos = (2*bq*eq+eq**2)/q0**2 + (2*bo*eo+eo**2)/o0**2
    zero(excess-sos)
    assert s.ask(s.Q.nonnegative(sos)) is True
    Q = s.diag(-1, 0, 1)
    assert s.trace(Q) == 0
    assert sum(a*a for a in Q) == 2
    A = s.zeros(3, 9)
    for i,j,k in itertools.product(range(3), repeat=3):
        idx = sorted((i,j,k))
        A[i,3*j+k] = 2 if idx == [0,0,0] else (-1 if idx in ([0,1,1],[0,2,2]) else 0)
    for k in range(3):
        assert sum(A[i,3*i+k] for i in range(3)) == 0
    assert A*A.T == s.diag(6,2,2)
    assert sum(a*a for a in A) == 10
    qspec = [v for v,n in Q.eigenvals().items() for _ in range(n)]
    ospec = [v for v,n in (A*A.T).eigenvals().items() for _ in range(n)]
    assert sum((v-2*v)**2 for v in qspec) == 2
    assert s.simplify(sum((s.sqrt(v)-s.sqrt(4*v))**2 for v in ospec)) == 10
    record('O1_weighted_lower_and_scaling',
           'Generic weighted bound conditional on named pointwise Hoffman-Wielandt/Mirsky lemmas; two exact STF scaling fixtures.',
           'For every common R set residual_Q=bq+eq and residual_O=bo+eo, with all four nonnegative by the named lemmas. The symbolic difference of weighted squared residual and weighted squared lower bound is a sum of nonnegative monomials. Nonnegative square-root monotonicity and taking min_R preserve this lower bound. In the two fixtures R=I attains exactly the lower bound, proving the minimum. No simultaneous attainment is assumed for arbitrary Q/O.',
           {'nonnegative_excess':str(sos), 'Q_norm_squared':2, 'O_norm_squared':10,
            'O_gram':[[6,0,0],[0,2,0],[0,0,2]], 'distances':['sqrt(2)/q0','sqrt(10)/o0'],
            'multiplicity':'all 27 rank-three entries retained; repeated eigenvalue 2 retained'})

    # Homogeneous unit-quaternion rotation: numerator has norm n and determinant n^3.
    w,a,b,c = s.symbols('w a b c', real=True)
    n = w*w+a*a+b*b+c*c
    H = s.Matrix([[w*w+a*a-b*b-c*c, 2*(a*b-w*c), 2*(a*c+w*b)],
                  [2*(a*b+w*c), w*w-a*a+b*b-c*c, 2*(b*c-w*a)],
                  [2*(a*c-w*b), 2*(b*c+w*a), w*w-a*a-b*b+c*c]])
    zero(H.T*H-n*n*s.eye(3))
    zero(H.det()-n**3)
    # Four charts all have the same Gram matrix; calculate each rather than
    # relying on an untested chart label permutation.
    x = s.Matrix(s.symbols('x1:4', real=True))
    nn = 1+x.dot(x)
    v = s.Matrix(s.symbols('v1:4', real=True))
    for chart in range(4):
        entries = list(x)
        entries.insert(chart, s.Integer(1))
        q = s.Matrix(entries)/s.sqrt(nn)
        J = q.jacobian(x)
        zero(J.T*J-(s.eye(3)/nn-x*x.T/nn**2))
        zero(v.dot(v)/nn-(J*v).dot(J*v)-x.dot(v)**2/nn**2)
    # Rational full quaternion and proper planar rotation.
    R = H.subs({w:2,a:0,b:0,c:1})/5
    assert R == s.Matrix([[s.Rational(3,5),s.Rational(-4,5),0],
                          [s.Rational(4,5),s.Rational(3,5),0],[0,0,1]])
    assert s.Rational(7,4)**2-3 == s.Rational(1,16)
    record('O2_quaternion_rotation_and_chart_derivative',
           'Generic real homogeneous quaternion identity for n>0 and all four normalized-chart derivatives; geometric radius conditional on named angular-distance and path-length lemmas.',
           'H^T H=n^2 I and det H=n^3 prove H/n is SO(3) for every nonzero quaternion. All four charts give J^T J=I/n-xx^T/n^2, so ||Jv||^2=||v||^2/n-(x.v)^2/n^2 <= ||v||^2/n. In a rectangular cell, n>=m_C^2; its center-to-point segment is inside the cell and has Euclidean length <=r_C. Integrating gives spherical length <=r_C/m_C. The named quaternion angle relation gives rotation angle <=2r_C/m_C and every principal angle <=pi, hence min(pi,2r_C/m_C). Every unit quaternion has a maximal nonzero absolute component; sign reversal makes it positive and component ratios lie in [-1,1], establishing four-chart coverage including ties. Grid spacing 1/m gives half-width 1/(2m), m_C>=1 and radius <=sqrt(3)/m <=7/(4m).',
           {'orthogonality_residual':0,'determinant_residual':0,'charts_verified':4,
            'gram':'I/(1+x.x)-x*x.T/(1+x.x)^2', 'rational_radius_square_gap':'1/16'})

    # O3 generic indicator implications reduce to positive slack sums.
    aa,bb,cc = s.symbols('aa bb cc', nonnegative=True)
    strict = s.symbols('strict', positive=True)
    assert s.ask(s.Q.nonnegative(aa+bb+cc)) is True
    assert s.ask(s.Q.positive(aa+strict+cc)) is True
    Li,Ui,L0,U0,si,s0 = s.symbols('Li Ui L0 U0 si s0', real=True)
    zero((si-Li)+(Li-U0)+(U0-s0)-(si-s0))
    zero((s0-L0)+(L0-Ui)+(Ui-si)-(s0-si))
    # Exhaustive finite endpoint regression supplements, never replaces, proof.
    finite_cases = 0
    for row in itertools.product((-1,0,1), repeat=6):
        li,ui,l0,u0,score_i,score_0 = row
        if li<=score_i<=ui and l0<=score_0<=u0:
            assert int(li>=u0) <= int(score_i>=score_0) <= int(ui>=l0)
            finite_cases += 1
    points = [0,1,2,3,10]
    scores = [sorted(abs(p-q) for j,q in enumerate(points) if i!=j)[1] for i,p in enumerate(points)]
    assert scores == [2,1,1,2,8]
    assert s.Rational(1+sum(v>=scores[-1] for v in scores[:-1]),5) == s.Rational(1,5)
    assert s.Rational(1+sum(3>=7 for _ in range(4)),5) == s.Rational(1,5)
    assert s.Rational(1+sum(0>=0 for _ in range(4)),5) == 1
    thresholds = {}
    for M,expected in ((1000,(32,49,50)),(301,(18,14,15))):
        k = int(s.ceiling(s.sqrt(M-1)))
        reject_max = M//20-1
        nonreject_min = M//20
        assert (k,reject_max,nonreject_min) == expected
        assert s.Rational(1+reject_max,M)<=s.Rational(1,20)
        assert s.Rational(1+nonreject_min,M)>s.Rational(1,20)
        thresholds[str(M)] = dict(k=k,reject_max_possible=reject_max,nonreject_min_certain=nonreject_min)
    record('O3_interval_inclusive_counts',
           'Generic pointwise interval-count inequality; generic conditional rank argument stated; exact finite fixtures and integer thresholds.',
           'Assume Li<=si<=Ui and L0<=s0<=U0. If Li>=U0 then si-s0=(si-Li)+(Li-U0)+(U0-s0)>=0. If Ui<L0 then s0-si=(s0-L0)+(L0-Ui)+(Ui-si)>0. These prove 1[Li>=U0]<=1[si>=s0]<=1[Ui>=L0], including equality ties. Sum over references, add 1, divide by positive M. kth monotonicity: at least k coordinates s_j<=s_(k); their L_j<=s_j<=s_(k), hence L_(k)<=s_(k); apply same argument to s<=U. For conditional superuniformity, sort scores decreasingly in tie blocks: every member of a block has inclusive rank equal to its last position. Blocks with rank<=t occupy at most t positions. Exchangeability makes the distinguished position uniform conditional on the multiset, giving probability <=floor(alpha*M)/M<=alpha. Every adaptive-time p_upper still bounds this fixed exact p pointwise. This uses fixed permutation-equivariant scores and exchangeability as declared premises; no product-law admission.',
           {'endpoint_cases_checked':finite_cases,'scalar_scores':scores,'wide_interval_p':'1/5','all_zero_tie_p_upper':'1','thresholds':thresholds})

    # J2 exact rational structural factor; generic z and off-support component.
    B = s.Matrix([s.Rational(3,5),s.Rational(4,5)])
    N = s.Matrix([s.Rational(-4,5),s.Rational(3,5)])
    vv = s.symbols('V', positive=True)
    z,eta = s.symbols('z eta', real=True)
    assert (B.T*B)[0] == 1 and (N.T*N)[0] == 1 and (N.T*B)[0] == 0
    C = vv*B*B.T
    Cp = B*B.T/vv
    zero(C*Cp*C-C)
    zero(Cp*C*Cp-Cp)
    zero((C*Cp).T-C*Cp)
    zero((Cp*C).T-Cp*C)
    assert C.rank() == 1
    r = B*z + N*eta
    zero((s.eye(2)-B*B.T)*r-N*eta)
    zero((B.T*r)[0]-z)
    zero((r.T*Cp*r)[0]-z*z/vv)
    r_on = 2*B
    r_off = r_on+N
    assert (N.T*r_on)[0] == 0 and (N.T*r_off)[0] == 1
    assert (r_on.T*Cp.subs(vv,4)*r_on)[0] == 1
    assert (r_off.T*Cp.subs(vv,4)*r_off)[0] == 1
    record('J2_rational_factor_support',
           'Exact declared rational B fixture, with arbitrary V>0 and r=B*z+N*eta; not a general floating support detector.',
           'B and N form an exact orthonormal basis. For C=V*B*B.T, the displayed Cp satisfies all four Moore-Penrose equations; range(C)=span(B), rank=1. Projection onto its orthogonal complement gives N*eta, so support is equivalent to eta=0. Reduced coordinate B^+r=z and reduced quadratic z^2/V. At V=4, r=2B is supported with quadratic 1; r=2B+N has nonzero null projection although its pseudoinverse quadratic remains 1. Thus the explicit support condition cannot be dropped.',
           {'B':['3/5','4/5'],'V_fixture':4,'rank':1,'on_support_quadratic':1,
            'off_support_null_projection':1,'off_support_pseudoinverse_quadratic':1})

    # Construct a probability law, never assume a joint Gaussian law from marginals.
    # X~N(0,1), S independent with P(S=+/-1)=1/2, Y=S*X.
    t,u = s.symbols('t u', real=True)
    phi = (s.exp(-(t+u)**2/2)+s.exp(-(t-u)**2/2))/2
    phi_gauss = s.exp(-(t*t+u*u)/2)
    zero(phi.subs(u,0)-s.exp(-t*t/2))
    zero(phi.subs(t,0)-s.exp(-u*u/2))
    assert s.diff(phi,t,u).subs({t:0,u:0}) == 0
    assert -s.diff(phi,t,2).subs({t:0,u:0}) == 1
    assert -s.diff(phi,u,2).subs({t:0,u:0}) == 1
    mixed_fourth = s.diff(phi,t,2,u,2).subs({t:0,u:0})
    gaussian_fourth = s.diff(phi_gauss,t,2,u,2).subs({t:0,u:0})
    assert mixed_fourth == 3 and gaussian_fourth == 1
    record('J2_gaussian_marginal_counterexample',
           'One explicit probability-law counterexample, verified through exact joint characteristic function.',
           'Let X be standard Gaussian and S independent fair sign, Y=S*X. Conditioning on S derives phi(t,u)=0.5 exp(-(t+u)^2/2)+0.5 exp(-(t-u)^2/2). Axis restrictions are standard-normal characteristic functions; second derivatives give unit variances and zero covariance. A bivariate Gaussian with those moments would have characteristic function exp(-(t^2+u^2)/2). The mixed fourth derivatives are 3 versus 1, proving inequivalence. Also X+Y has a probability-1/2 atom at zero but variance 2, so it cannot be Gaussian. The target theorem itself is not an assumption.',
           {'characteristic_function':str(phi),'covariance':[[1,0],[0,1]],
            'E_X2Y2_actual':3,'E_X2Y2_joint_gaussian':1,'atom_X_plus_Y_at_zero':'1/2'})
    assert set(checks) == set(contract['target']['exact_test_obligations'])


if __name__ == '__main__':
    started = time.monotonic()
    error = None
    try:
        verify()
    except Exception as exc:
        error = {'type':type(exc).__name__,'message':str(exc)}
    out = dict(contract_id='R8-ORBIT-RANK-JOINT-JET-V1', contract_sha256=CONTRACT_SHA,
               axis='sympy',status='PASS' if error is None else 'ERROR',checks=checks,
               domain_assumption_diff=[],counterexample=None,error=error,
               tool_versions={'python':platform.python_version(),'sympy':s.__version__,
                              'executable':sys.executable},
               numeric_precision='Exact symbolic/rational; no approximate comparisons used',
               wall_seconds=time.monotonic()-started)
    print(json.dumps(out,indent=2,sort_keys=True))
    sys.exit(0 if error is None else 1)
