#!/usr/bin/env python3
"""Independent exact SymPy axis for the frozen R7 scalar-algebra contract.

Only reads its own assignment/context and the contract's cited mathematical inputs.
No historical operator recomputation, numerical-pixel certificate, or physical admission.
"""
from pathlib import Path
import hashlib
import itertools
import json
import platform
import sys
import traceback
import sympy as s

AXIS = Path(__file__).resolve().parent
ROOT = AXIS.parents[4]
RUN = ROOT / '.agent-harness/runs/TENSOR-JOINT-R7-20260908'
CONTRACT_SHA = '377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2'
CONTEXT_VERSION = '2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4'
checks = {}
diffs = []
counterexample = None
details = {'toolchain': {'python': platform.python_version(), 'python_executable':sys.executable, 'sympy':s.__version__}, 'scope':'exact stated algebraic implications; accepted rational certificate implication only', 'derivations':{}, 'files_read':[str(Path(__file__).relative_to(ROOT))]}

def read(path):
    rel = str(path.relative_to(ROOT))
    details['files_read'].append(rel)
    return path.read_bytes()

def z(expr):
    return s.simplify(expr) == 0

try:
    ctx = json.loads(read(ROOT / '.agent-harness/context/CONTEXT_INDEX.json'))
    assignment = json.loads(read(RUN / 'assignments/sympy.json'))
    contract_bytes = read(RUN / 'CAS_CONTRACT.json')
    contract = json.loads(contract_bytes)
    if hashlib.sha256(contract_bytes).hexdigest() != CONTRACT_SHA:
        diffs.append('CAS_CONTRACT sha256 mismatch')
    if ctx['context_version'] != CONTEXT_VERSION or assignment['context_version'] != CONTEXT_VERSION:
        diffs.append('context_version mismatch')
    if s.__version__ != '1.14.0':
        diffs.append('unpinned SymPy version: ' + s.__version__)
    if Path(sys.executable).absolute() != Path(contract['axes']['sympy']['pinned_toolchain']['python']).absolute():
        diffs.append('unpinned Python executable: ' + sys.executable)
    source_bytes = {}
    for item in contract['identity']['source_input_hashes']:
        raw = read(ROOT / item['path'])
        source_bytes[item['path']] = raw
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            diffs.append('immutable source identity mismatch: ' + item['path'])
    if diffs:
        raise ValueError('source/context/toolchain mismatch')
    cert = json.loads(source_bytes['docs/generated/tensor_joint_r7/axial_certificate_source.json'])
    details['source_hashes'] = contract['identity']['source_input_hashes']
    details['contract_sha256'] = CONTRACT_SHA

    # T1: build all 27 symmetric components from the ten given independent values.
    independent = list(itertools.combinations_with_replacement(range(3),3))
    vals = tuple(map(s.Integer, contract['target']['numeric_test_vectors'][0]['T1_O_entries']))
    lookup = dict(zip(independent, vals))
    O = s.MutableDenseNDimArray.zeros(3,3,3)
    for i,j,k in itertools.product(range(3),repeat=3):
        O[i,j,k] = lookup[tuple(sorted((i,j,k)))]
    Q = s.diag(-1,0,1)
    traces = s.Matrix([sum(O[i,i,k] for i in range(3)) for k in range(3)])
    v = s.Matrix([sum(O[i,j,k]*Q[j,k] for j,k in itertools.product(range(3),repeat=2)) for i in range(3)])
    chi = s.Matrix.hstack(v,Q*v,Q*Q*v).det()
    symmetry = all(O[i,j,k] == O[k,j,i] == O[j,i,k] for i,j,k in itertools.product(range(3),repeat=3))
    checks['T1_trace_and_contraction'] = bool(symmetry and s.trace(Q)==0 and traces==s.zeros(3,1) and v==s.Matrix([0,-1,1]) and chi==0)
    details['derivations']['T1_trace_and_contraction'] = {'Q_trace':str(s.trace(Q)),'O_traces':list(map(str,traces)),'O_colon_Q':list(map(str,v)),'chi_det_v_Qv_Q2v':str(chi),'independent_index_order':[[a+1 for a in ijk] for ijk in independent]}
    proper = []
    improper_maps = []
    for signs in itertools.product((-1,1),repeat=3):
        R = s.diag(*signs)
        assert R*Q*R.T == Q
        residuals = [signs[i]*signs[j]*signs[k]*O[i,j,k]+O[i,j,k] for i,j,k in itertools.product(range(3),repeat=3)]
        maps_to_negative = all(r==0 for r in residuals)
        if R.det()==1:
            proper.append({'signs':signs,'maps_to_negative':maps_to_negative,'first_nonzero_residual':str(next((r for r in residuals if r!=0),0))})
        elif maps_to_negative:
            improper_maps.append(signs)
    # Distinct eigenvalues imply RQ=QR has no off-diagonal entries; derive component factors.
    eig = [-1,0,1]
    commutator_factors = [eig[j]-eig[i] for i,j in itertools.product(range(3),repeat=2) if i!=j]
    checks['T1_no_proper_signed_stabilizer'] = bool(len(proper)==4 and all(not row['maps_to_negative'] for row in proper) and all(factor!=0 for factor in commutator_factors) and improper_maps==[(-1,-1,-1)])
    details['derivations']['T1_no_proper_signed_stabilizer'] = {'proper_signed_axes':proper,'improper_maps_to_negative':improper_maps,'off_diagonal_commutator_factors':commutator_factors,'assumption':'R in SO(3), R Q R^T = Q; simple Q spectrum forces diagonal orthogonal R'}

    # T3: the normalized derivative is computed before sign substitutions.
    tau = s.symbols('tau',real=True)
    Temp = s.Function('Tbar')(tau)
    X = s.Function('X')(tau)
    quotient = s.diff(X/Temp,tau)
    expected_quotient = s.diff(X,tau)/Temp-X*s.diff(Temp,tau)/Temp**2
    theta2dot, theta1grad, theta3div, Cpropdot, Cprop, Eprop = s.symbols('theta2dot theta1grad theta3div Cpropdot Cprop Eprop',real=True)
    qdot, dgrad, odiv, Coutdot, Cout, Eout = s.symbols('qdot dgrad odiv Coutdot Cout Eout',real=True)
    Theta = s.symbols('Theta',positive=True)
    sigma_prop = -theta2dot-theta1grad-s.Rational(3,7)*theta3div
    omega_prop = -3*Cpropdot/Theta-Cprop-s.Rational(6,5)*Eprop/Theta
    sigma_out = sigma_prop.subs({theta2dot:qdot,theta1grad:-dgrad,theta3div:-odiv})
    omega_out = omega_prop.subs({Cpropdot:-Coutdot,Cprop:-Cout,Eprop:Eout})
    odd_residuals = [s.diff(-s.Function(name)(tau)/Temp,tau)+s.diff(s.Function(name)(tau)/Temp,tau) for name in ('Dsky','Osky')]
    t3_residuals = [quotient-expected_quotient, sigma_out-(-qdot+dgrad+s.Rational(3,7)*odiv), omega_out-(3*Coutdot/Theta+Cout-s.Rational(6,5)*Eout/Theta), *odd_residuals]
    checks['T3_normalized_derivative_and_odd_signs'] = bool(all(z(r) for r in t3_residuals))
    details['derivations']['T3_normalized_derivative_and_odd_signs'] = {'normalized_derivative':str(quotient),'sigma_out':str(sigma_out),'omega_out':str(omega_out),'residuals':[str(s.simplify(r)) for r in t3_residuals],'scope':'componentwise formal differentiation and linear operator sign transformation only; Tbar>0 and Theta>0 assumed; no physical hierarchy derivation'}

    # T5: free noncommutative algebra preserves matrix multiplication order.
    # An inverse with constant coefficient I is determined to first order by
    # (I-tE)(I+tB)=I+t(B-E)+O(t^2), hence B=E. No target coefficient is assumed.
    t = s.symbols('t',real=True)
    E,A,C,B = s.symbols('E A C B',commutative=False)
    generic_product = s.expand((1-t*E)*(1+t*B))
    inverse_equation_residual = s.expand(generic_product.coeff(t,1)-(B-E))
    first_inverse = 1+t*E
    left_residual = s.expand((1-t*E)*first_inverse-(1-t**2*E**2))
    right_residual = s.expand(first_inverse*(1-t*E)-(1-t**2*E**2))
    Kseries = s.expand(-t*C*first_inverse*A)
    coeff = Kseries.coeff(t,1)
    checks['T5_first_order_inverse_coefficient'] = bool(inverse_equation_residual==0 and left_residual==0 and right_residual==0 and s.expand(coeff+C*A)==0 and Kseries.coeff(t,0)==0)
    details['derivations']['T5_first_order_inverse_coefficient'] = {'generic_inverse_linear_equation':str(generic_product.coeff(t,1)),'inverse_1st_order':'I+tE modulo t^2','both_inverse_residuals':[str(left_residual),str(right_residual)],'K_series':str(Kseries),'K_prime_zero':str(coeff),'representation':'free noncommutative ring, scalar 1 denotes each compatible identity map; valid for all compatible finite real matrices with inverse at t=0','implementation_note':'SymPy MatrixExpr automatic differentiation bug preserved in initial_matrixexpr_probe.log; formal algebra avoids the engine bug without changing the obligation'}

    # T5 scalar implication: x=(1-36f)/f is a bijection of stated f-domain onto x>0.
    f,c,d,x = s.symbols('f c d x',positive=True)
    h,k,b = s.symbols('h k b',nonnegative=True)
    slack = s.symbols('slack',nonnegative=True)
    bound = c*f/(1-36*f)
    threshold = d**2*(1-36*f)**2/(c**2*f**2)
    domain_sub = {f:1/(36+x)}
    Bx = s.simplify(bound.subs(domain_sub))
    qx = s.simplify(threshold.subs(domain_sub))
    # d<=kh, k<=Bx, h>=0 imply Bx*h-d >=0 by this exact sum.
    chain = s.expand((Bx-k)*h+(k*h-d)-(Bx*h-d))
    linear_solution = s.solve_univariate_inequality(s.Le(d,Bx*h),h)
    # h=d/Bx+slack exhausts feasible norm values; squared excess is nonnegative.
    square_excess = s.factor((d/Bx+slack)**2-qx)
    checks['T5_scalar_cost_implication'] = bool(z(Bx-c/x) and z(qx-d**2*x**2/c**2) and chain==0 and square_excess.is_nonnegative and z((Bx*h-d)/Bx-(h-d/Bx)) and s.limit(threshold,f,0,dir='+')==s.oo)
    details['derivations']['T5_scalar_cost_implication'] = {'domain_parameterization':'f=1/(36+x), x>0, inverse x=(1-36f)/f','norm_bound':str(Bx),'norm_chain_residual':str(chain),'linear_feasible_norm':str(linear_solution),'squared_threshold':str(qx),'squared_excess':str(square_excess),'square_excess_nonnegative':square_excess.is_nonnegative,'small_mask_limit':str(s.limit(threshold,f,0,dir='+')),'assumptions':'0<f<1/36; c,d>0; ||K||<=bound; d<=||K||h; h>=0. If ||K||=0 nonzero d is infeasible. This proves the implication, not the operator bound or physical nuisance budget.'}

    # T6 fixed scalar witness: directly compare Schur complements.
    U,V,Eval = s.Integer(1),s.Integer(1),s.Integer(1)
    G = s.Rational(1,4)
    Fbefore = U-V**2/Eval
    Fafter = U-V**2/(Eval+G)
    gain = s.simplify(Fafter-Fbefore)
    checks['T6_scalar_information_one_fifth'] = bool(gain==s.Rational(1,5) and s.simplify(gain-V**2*(1/Eval-1/(Eval+G)))==0)
    details['derivations']['T6_scalar_information_one_fifth'] = {'F_before':str(Fbefore),'F_after':str(Fafter),'gain':str(gain),'scope':'fixed U=V=E=1,G=1/4 scalar witness only'}

    # L10: accepted rational minors and column labels are inputs, not recomputed outputs.
    normal = [s.Rational(v) for v in cert['normal_block_determinants']]
    positive = all(v>0 for v in normal)
    expected_rows = [sum(1 for ell in range(2,6) if ell>=m) for m in range(6)]
    minor_details = []
    all_minors_valid = len(cert['pivot_minors'])==6
    numeric_ok = True
    cutoff_needed = 0
    for m,pivot in enumerate(cert['pivot_minors']):
        rat = s.Rational(pivot['determinant_squared'])
        cols = pivot['source_ells']
        valid = bool(pivot['m']==m and rat>0 and pivot['nonzero'] is True and len(cols)==expected_rows[m] and len(set(cols))==len(cols) and all(7<=ell<=10 and ell>=m for ell in cols))
        all_minors_valid = all_minors_valid and valid
        cutoff_needed = max(cutoff_needed,max(cols))
        # Evaluate rational at the contract's 80 digits and check supplied display numbers
        # under declared absolute plus relative tolerance; decimal displays are not exact data.
        numerical = s.N(rat,80)
        display = s.Float(pivot['determinant_squared_numeric_50d'],80)
        err = abs(numerical-display)
        tolerance = s.Float('1e-50',80)+s.Float('1e-40',80)*abs(numerical)
        numeric_ok = numeric_ok and bool(err<=tolerance)
        minor_details.append({'m':m,'source_ells':cols,'determinant_squared_exact_positive':bool(rat>0),'determinant_squared_80d':str(numerical),'display_absolute_error':str(err),'row_count':expected_rows[m]})
    # In an axial block, one complex source column exists for each ell=7,...,L.
    # At L<10 the m=0 four-row block has fewer than four columns, hence cannot
    # be onto. At L=10 the accepted nonzero minors fit entirely in 7..10 and
    # exhaust all retained row counts. Nonzero-m blocks occur twice in real storage.
    full_real = expected_rows[0]+2*sum(expected_rows[1:])
    l9_upper = min(expected_rows[0],3)+2*sum(min(rows,3) for rows in expected_rows[1:])
    checks['L10_accepted_minors_and_minimal_cutoff'] = bool(positive and all_minors_valid and numeric_ok and cert['complex_block_ranks']==expected_rows and cert['real_stored_rank']==full_real==32 and cutoff_needed==10 and l9_upper<32)
    details['derivations']['L10_accepted_minors_and_minimal_cutoff'] = {'normal_determinants_positive':positive,'pivot_minors':minor_details,'retained_rows_by_m':expected_rows,'real_rank_at_L10':full_real,'L9_real_rank_upper_bound':l9_upper,'L9_m0_columns':3,'m0_rows':4,'minimal_L':cutoff_needed,'premise':'accepted exact rational minor values and source-column identities of the supplied axial block certificate; no historical integral, operator, other-direction, or pixel recomputation'}

    obligations = contract['target']['exact_test_obligations']
    if set(checks) != set(obligations):
        diffs.append('implemented obligation set differs from contract')
    failed = [name for name,ok in checks.items() if not ok]
    if failed:
        counterexample = {'failed_obligations':failed,'details':'See axis details.json for exact residuals or identity violations.'}
except Exception as exc:
    details['exception'] = {'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    if counterexample is None:
        counterexample = {'execution_error':str(exc)}
    for name in ('T1_trace_and_contraction','T1_no_proper_signed_stabilizer','T3_normalized_derivative_and_odd_signs','T5_first_order_inverse_coefficient','T5_scalar_cost_implication','T6_scalar_information_one_fifth','L10_accepted_minors_and_minimal_cutoff'):
        checks.setdefault(name,False)

payload = {'checks':checks,'domain_assumption_diff':diffs,'counterexample':counterexample}
details['payload'] = payload
(AXIS/'details.json').write_text(json.dumps(details,indent=2,sort_keys=True)+'\n')
print(json.dumps(payload,sort_keys=True))
sys.exit(0 if all(checks.values()) and not diffs and counterexample is None else 1)
