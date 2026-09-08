#!/usr/bin/env python3
"""Independent R7 algebra axis, Sage 10.9 and explicit system Singular 4.3.2."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from sage.all import QQ, SR, FreeAlgebra, matrix, vector, var, function, diff
import sage.version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RUN = '.agent-harness/runs/TENSOR-JOINT-R7-20260908'
OBLIGATIONS = [
    'T1_trace_and_contraction', 'T1_no_proper_signed_stabilizer',
    'T3_normalized_derivative_and_odd_signs', 'T5_first_order_inverse_coefficient',
    'T5_scalar_cost_implication', 'T6_scalar_information_one_fifth',
    'L10_accepted_minors_and_minimal_cutoff',
]
checks = {key: False for key in OBLIGATIONS}
domain_diff = []
counterexample = None
details = {}
files_read = [
    '.agent-harness/context/CONTEXT_INDEX.json', RUN + '/assignments/sage_singular.json',
    RUN + '/CAS_CONTRACT.json', 'docs/generated/tensor_joint_r7/axial_certificate_source.json',
    'docs/research_program/tensor_joint_r7/THEORY.md',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, explanation):
    if not bool(value):
        raise AssertionError(explanation)


def conv(a, b, max_degree=1):
    """Coefficient convolution in the free associative algebra modulo t^2."""
    return {k: sum((a.get(i, 0)*b.get(k-i, 0) for i in range(k+1)), 0)
            for k in range(max_degree+1)}


try:
    contract_path = ROOT / RUN / 'CAS_CONTRACT.json'
    contract = json.loads(contract_path.read_text())
    require(sha(contract_path) == '377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2', 'CAS contract changed')
    context = json.loads((ROOT / files_read[0]).read_text())
    assignment = json.loads((ROOT / files_read[1]).read_text())
    require(context['context_version'] == assignment['context_version'] == '2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4', 'context mismatch')
    for item in contract['identity']['source_input_hashes']:
        require(sha(ROOT / item['path']) == item['sha256'], 'source pin mismatch: ' + item['path'])
    cert = json.loads((ROOT / files_read[3]).read_text())
    require(sage.version.version == '10.9', 'Sage toolchain mismatch')
    sysenv = dict(os.environ)
    # Use the separately pinned system executable, never Sage's 4.4.1 interface.
    sysenv.pop('LD_LIBRARY_PATH', None)
    version = subprocess.run(['/usr/bin/Singular', '--version'], capture_output=True, text=True, env=sysenv, timeout=30)
    (HERE / 'singular_version.txt').write_text(version.stdout + version.stderr)
    require(version.returncode == 0 and re.search(r'version 4\.3\.2\b', version.stdout), 'Singular toolchain mismatch')
    details['tool_versions'] = {'sage': sage.version.version, 'singular_executable': '/usr/bin/Singular', 'singular': '4.3.2', 'python': sys.version.split()[0]}

    # T1: build all 27 entries solely by the given independent symmetric entries.
    triples = [(0,0,0),(0,0,1),(0,0,2),(0,1,1),(0,1,2),(0,2,2),(1,1,1),(1,1,2),(1,2,2),(2,2,2)]
    independent = [1,0,0,-2,1,1,1,-1,-1,1]
    od = dict(zip(triples, map(QQ, independent)))
    tensor = {(i,j,k): od[tuple(sorted((i,j,k)))] for i,j,k in itertools.product(range(3), repeat=3)}
    Qm = matrix(QQ, [[-1,0,0],[0,0,0],[0,0,1]])
    traces = [sum(tensor[i,j,j] for j in range(3)) for i in range(3)]
    v = vector(QQ, [sum(tensor[i,j,k]*Qm[j,k] for j,k in itertools.product(range(3),repeat=2)) for i in range(3)])
    chi = matrix(QQ, [v, Qm*v, Qm*Qm*v]).det()
    require(Qm.trace() == 0 and Qm == Qm.transpose(), 'Q not STF')
    require(traces == [0,0,0] and v == vector(QQ,[0,-1,1]) and chi == 0, 'T1 witness mismatch')
    require(all(tensor[x] == tensor[tuple(reversed(x))] for x in tensor), 'O not symmetric')
    checks[OBLIGATIONS[0]] = True
    details[OBLIGATIONS[0]] = {'O_trace': list(map(str,traces)), 'O_contract_Q': list(map(str,v)), 'chi': str(chi)}
    stabilizers = []
    signed_maps_to_negative = []
    for signs in itertools.product([-1,1], repeat=3):
        Sm = matrix.diagonal(QQ, signs)
        require(Sm*Qm*Sm.transpose() == Qm, 'signed axis fails Q stabilizer')
        maps_negative = all(signs[i]*signs[j]*signs[k]*tensor[i,j,k] == -tensor[i,j,k] for i,j,k in tensor)
        if maps_negative:
            signed_maps_to_negative.append({'signs':list(signs), 'determinant':str(Sm.det())})
        if Sm.det() == 1:
            stabilizers.append({'signs':list(signs),'maps_negative':maps_negative})
    require(len(set(Qm.eigenvalues())) == 3, 'Q eigenvalues not distinct')
    require(len(stabilizers) == 4 and not any(row['maps_negative'] for row in stabilizers), 'proper signed stabilizer counterexample')
    require(signed_maps_to_negative == [{'signs':[-1,-1,-1],'determinant':'-1'}], 'negative-map enumeration mismatch')
    checks[OBLIGATIONS[1]] = True
    details[OBLIGATIONS[1]] = {'proper_Q_stabilizers':stabilizers,'all_signed_negative_maps':signed_maps_to_negative,'extension_to_SO3':'Distinct ordered eigenvalues force every Q-stabilizing rotation to preserve each one-dimensional eigenspace.'}

    # T3: differentiate normalized coefficients from functions, retaining Tdot.
    x = var('x')
    Tf, Qf, Df, Of = [function(name)(x) for name in ['Temp','Qcoef','Dcoef','Ocoef']]
    quotient_residual = diff(Qf/Tf,x) - (diff(Qf,x)*Tf-Qf*diff(Tf,x))/Tf**2
    odd_residuals = [diff(-F/Tf,x)+diff(F/Tf,x) for F in [Df,Of]]
    require(quotient_residual.simplify_full() == 0 and all(z.simplify_full() == 0 for z in odd_residuals), 'normalized derivative failure')
    Th, qd, gd, go, Co, Cod, Eab = var('Th qd gd go Co Cod Eab')
    sig_e = -qd - (-gd) - QQ(3)/7*(-go)
    sig_n = -qd + gd + QQ(3)/7*go
    omg_e = -3*(-Cod)/Th - (-Co) - QQ(6)/5/Th*Eab
    omg_n = 3*Cod/Th + Co - QQ(6)/5/Th*Eab
    require((sig_e-sig_n).simplify_full() == 0 and (omg_e-omg_n).simplify_full() == 0, 'odd-sign conversion failure')
    checks[OBLIGATIONS[2]] = True
    details[OBLIGATIONS[2]] = {'normalized_derivative_residual':str(quotient_residual.simplify_full()),'odd_derivative_residuals':list(map(str,odd_residuals)),'sigma_residual':str(sig_e-sig_n),'omega_residual':str((omg_e-omg_n).simplify_full()),'scope':'Coefficient normalization and parity substitution only; geodesic hierarchy is a premise, not rederived.'}

    # T5: formal two-sided inverse to first order in a central t; E,A,C do not commute.
    F = FreeAlgebra(QQ, 3, names=('EE','AA','CC'))
    EE, AA, CC = F.gens()
    gram = {0:F.one(),1:-EE}
    inverse = {0:F.one(),1:EE}
    left, right = conv(gram,inverse), conv(inverse,gram)
    require(left == right == {0:F.one(),1:F.zero()}, 'first-order inverse failed')
    # Coefficient equations from (1-tE)N=1 determine N0=1 and N1=E uniquely.
    response = conv({1:-CC}, conv(inverse,{0:AA}))
    require(response == {0:F.zero(),1:-CC*AA}, 'first-order response coefficient failed')
    checks[OBLIGATIONS[3]] = True
    details[OBLIGATIONS[3]] = {'left_inverse_coefficients':{str(k):str(v) for k,v in left.items()},'right_inverse_coefficients':{str(k):str(v) for k,v in right.items()},'K_coefficients':{str(k):str(v) for k,v in response.items()},'generality':'Free associative algebra preserves matrix ordering for every compatible finite size; inverse identity is modulo t^2.'}

    # T5: all f in (0,1/36) uniquely have p=f/(1-36f)>0.
    # Norm premises d<=k*h and 0<=k<=c*p imply h=d/(c*p)+s with s>=0.
    p, c, dd, s, ff = var('p c dd s ff')
    fparam = p/(1+36*p)
    bound = dd*(1-36*ff)/(c*ff)
    lower = dd/(c*p)
    require((bound.subs(ff=fparam)-lower).simplify_full() == 0, 'cost reparameterization failed')
    gap = ((lower+s)**2-lower**2).expand()
    positive_factor = s*(2*dd+c*p*s)/(c*p)
    require((gap-positive_factor).simplify_full() == 0, 'nonnegative slack factorization failed')
    require((1-36*fparam-1/(1+36*p)).simplify_full() == 0, 'domain parameterization failed')
    checks[OBLIGATIONS[4]] = True
    details[OBLIGATIONS[4]] = {'domain_map':'p=f/(1-36f)>0, inverse f=p/(1+36p); c,d>0; s=h-d/(c*p)>=0 follows from the norm premises.', 'nonnegative_cost_gap':str(positive_factor), 'proof_order':'d<=k*h<=c*p*h; divide by positive c*p; write nonnegative slack s; factor h^2-(d/(c*p))^2. This is scalar order algebra; it does not establish the assumed operator bound.'}

    U,V,E,G = QQ(1),QQ(1),QQ(1),QQ(1)/4
    before = U-V*V/E
    after = U-V*V/(E+G)
    gain = V*(1/E-1/(E+G))*V
    require(before == 0 and after == gain == QQ(1)/5, 'T6 fixed scalar witness failed')
    checks[OBLIGATIONS[5]] = True
    details[OBLIGATIONS[5]] = {'before':str(before),'after':str(after),'gain':str(gain),'scope':'Fixed scalar information example; no empirical shared-calibration premise established.'}

    # L10: accepted minor/source-column data, with exact rational positivity.
    row_dims = [sum(ell >= m for ell in range(2,6)) for m in range(6)]
    require(row_dims == [4,4,4,3,2,1], 'row dimensions mismatch')
    normals = [QQ(value) for value in cert['normal_block_determinants']]
    require(len(normals) == 6 and all(value > 0 for value in normals), 'normal determinant not positive')
    require(cert['complex_block_ranks'] == row_dims, 'accepted rank record mismatch')
    require([row['m'] for row in cert['pivot_minors']] == list(range(6)), 'minor labels mismatch')
    minors = []
    for row, dim in zip(cert['pivot_minors'], row_dims):
        cols = row['source_ells']
        rational = QQ(row['determinant_squared'])
        require(rational > 0 and rational.denominator() > 0, 'minor square not positive')
        require(cols == list(range(7,7+dim)) and max(cols) <= 10 and len(set(cols)) == dim, 'minor source-column identity mismatch')
        minors.append({'m':row['m'],'row_dimension':dim,'source_ells':cols,'exact_minor_square_positive':bool(rational>0)})
    real_rank = row_dims[0]+2*sum(row_dims[1:])
    require(real_rank == cert['real_stored_rank'] == 32, 'real rank implication mismatch')
    upper_below = {L:min(4,max(0,L-6))+2*sum(min(dim,max(0,L-6)) for dim in row_dims[1:]) for L in range(0,10)}
    require(all(r < 32 for r in upper_below.values()), 'lower cutoff upper-bound failure')
    checks[OBLIGATIONS[6]] = True
    details[OBLIGATIONS[6]] = {'accepted_minor_implications':minors,'normal_determinants_exact_positive':True,'L10_real_rank':real_rank,'lower_cutoff_rank_upper_bounds':upper_below,'m0_obstruction':'At L<=9, at most source ell 7,8,9 gives only three m=0 columns for four retained rows.','scope':'Implication from accepted rational minors and source-column identities. Historical operator/integrals were not recomputed.'}

    singular_script = r'''
print("SINGULAR_VERSION="+string(system("version")));
ring r=0,(Q,Qd,T,Td,q,qd,p,c,d,s,Th,gd,go,Co,Cod,Eab),dp;
ideal product_rule=Q-q*T,Qd-qd*T-q*Td;
ideal gb=std(product_rule);
poly derivative_res=reduce(T^2*qd-Qd*T+Q*Td,gb);
print("NORMALIZED_DERIVATIVE_RES="+string(derivative_res));
poly cost_res=c*p*((d+c*p*s)^2-d^2)-c^2*p^2*s*(2*d+c*p*s);
print("COST_FACTOR_RES="+string(cost_res));
poly sigma_res=7*(-qd+gd)+3*go-(-7*qd+7*gd+3*go);
print("SIGMA_PARITY_RES="+string(sigma_res));
poly omega_res=15*Cod+5*Th*Co-6*Eab-(-15*(-Cod)-5*Th*(-Co)-6*Eab);
print("OMEGA_PARITY_RES="+string(omega_res));
print("SINGULAR_DONE");
quit;
'''
    singular_path = HERE / 'verify.sing'
    singular_path.write_text(singular_script)
    singular_run = subprocess.run(['/usr/bin/Singular','-q','--no-tty',str(singular_path)],capture_output=True,text=True,env=sysenv,timeout=60)
    transcript = singular_run.stdout + singular_run.stderr
    (HERE / 'singular_transcript.txt').write_text(transcript)
    files_read.append(str(singular_path.relative_to(ROOT)))
    require(singular_run.returncode == 0 and 'SINGULAR_VERSION=4330' in transcript and 'SINGULAR_DONE' in transcript, 'Singular did not complete with pinned version')
    for label in ['NORMALIZED_DERIVATIVE_RES','COST_FACTOR_RES','SIGMA_PARITY_RES','OMEGA_PARITY_RES']:
        require(label+'=0' in transcript, 'Singular residual failed: '+label)
    require('?' not in transcript, 'Singular diagnostic error detected')
    details['singular_exact_checks'] = {'product_rule_ideal_reduction':0,'cost_polynomial_identity':0,'sigma_parity':0,'omega_parity':0,'version_numeric':4330}
except Exception as exc:
    details['error'] = {'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    if isinstance(exc,AssertionError):
        counterexample = {'kind':'verification_failure','detail':str(exc)}
    else:
        domain_diff.append({'kind':'axis_execution_error','detail':str(exc)})

payload = {'checks':checks,'domain_assumption_diff':domain_diff,'counterexample':counterexample}
(HERE/'engine_result.json').write_text(json.dumps(payload,indent=2)+'\n')
(HERE/'verification_details.json').write_text(json.dumps(details,indent=2)+'\n')
files_read.extend(str((HERE/name).relative_to(ROOT)) for name in ['attempt_01.stdout.json','attempt_01.stderr.txt','engine_result.json','verification_details.json','singular_version.txt','singular_transcript.txt'] if (HERE/name).exists())
files_read = list(dict.fromkeys(files_read))
status = 'pass' if all(checks.values()) and not domain_diff and counterexample is None else 'error'
envelope = {
    'schema_version':2,'run_id':'TENSOR-JOINT-R7-20260908','assignment_id':'sage_singular',
    'context_version':'2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4',
    'independence_mode':'blind-results','status':status,'axis':'sage_singular',
    'claim_id':'RUN-TENSOR-JOINT-R7-20260908-V01','cas_contract_sha256':'377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2',
    'files_read':files_read+[str(Path(__file__).resolve().relative_to(ROOT))],
    'assumptions_used':contract['semantics']['assumptions'] if 'contract' in globals() else [],
    'claim_ceiling':'Exact stated algebraic implications and fixed witnesses; L10 accepted-certificate implication only, with no empirical admission.',
    'checks':checks,'domain_assumption_diff':domain_diff,'counterexample':counterexample,
    'findings':[{'claim_id':'RUN-TENSOR-JOINT-R7-20260908-V01','obligation':key,'verdict':'pass' if value else 'inconclusive','evidence_fingerprint':hashlib.sha256(('377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2:'+key).encode()).hexdigest(),'evidence_ref':str((HERE/'verification_details.json').relative_to(ROOT))+'#'+key} for key,value in checks.items()],
    'evidence':[{'path':str((HERE/name).relative_to(ROOT)),'sha256':sha(HERE/name)} for name in ['verify.py','engine_result.json','verification_details.json','singular_version.txt','verify.sing','singular_transcript.txt'] if (HERE/name).exists()],
    'reproduce_argv':['/usr/local/bin/sage','-python',str(Path(__file__).resolve())],
    'tool_versions':details.get('tool_versions',{}),
    'correlation_disclosure':'Independent script authored by a Codex agent; other axes may use the same LLM family. No sibling result or derivation was read.',
    'operational_notes':['Canonical injected cwd and active-run header referred to an older run; actual explicit R7 assignment/context and source hashes were validated.','Default Sage Singular interface is 4.4.1; all Singular checks here use separately installed /usr/bin/Singular 4.3.2.'],
    'completed_at':datetime.now(timezone.utc).isoformat(),
}
(ROOT/RUN/'results/sage_singular.json').write_text(json.dumps(envelope,indent=2)+'\n')
print(json.dumps(payload,separators=(',',':')))
sys.exit(0 if status=='pass' else 1)
