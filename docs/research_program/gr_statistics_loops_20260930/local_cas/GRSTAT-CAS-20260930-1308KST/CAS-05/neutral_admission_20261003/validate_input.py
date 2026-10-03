"""Exact, source-bound CAS05 input diagnostic. Not a blind campaign axis.

Run with --candidate a managed model's JSON polynomial payload. Only rational
polynomials in declared names are parsed, never model-generated executable code.
The full metric has g(0)=eta, dg(0)=0. Its inverse is eta+O(x^2), Gamma=O(x),
and Gamma*Gamma=O(x^2). Consequently the degree <=2 connection needed for j1 R
is computed with eta inverse alone; contraction corrections also start at O(x^2).
This proves why the cubic metric representative suffices, not a flat-background
assumption about the full metric away from the origin.
"""
import argparse
import ast
import hashlib
import itertools
import json
from pathlib import Path
import platform

import sympy as s


HERE = Path(__file__).resolve().parent
X = s.symbols('t x y z', real=True)
B = s.Symbol('b', positive=True)
Q = s.symbols('q1 q2 q3', real=True)
M = s.Matrix(3, 3, lambda i, j: s.Symbol(f'm{i+1}{j+1}', real=True))
NAMES = {str(v): v for v in (*X, B, *Q, *M)}
SIGN = (-1, 1, 1, 1)
UPPER = [f'{a}{b}' for a in range(4) for b in range(a, 4)]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def polynomial(text):
    """Closed rational-polynomial parser (no calls, attributes, floats or eval)."""
    def parse(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return s.Integer(n.value)
        if isinstance(n, ast.Name) and n.id in NAMES:
            return NAMES[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            return -parse(n.operand) if isinstance(n.op, ast.USub) else parse(n.operand)
        if isinstance(n, ast.BinOp):
            a, b = parse(n.left), parse(n.right)
            if isinstance(n.op, ast.Add): return a+b
            if isinstance(n.op, ast.Sub): return a-b
            if isinstance(n.op, ast.Mult): return a*b
            if isinstance(n.op, ast.Div) and b.is_Integer and b != 0: return a/b
            if isinstance(n.op, ast.Pow) and b.is_Integer and 0 <= b <= 3: return a**b
        raise ValueError('not an allowed rational polynomial')
    if not isinstance(text, str) or len(text) > 4000:
        raise ValueError('invalid polynomial text')
    return s.Poly(s.expand(parse(ast.parse(text, mode='eval').body)), *NAMES.values()).as_expr()


def matrix(payload):
    if set(payload) != set(UPPER): raise ValueError('exact upper-triangle keys required')
    h = s.zeros(4)
    for key, val in payload.items():
        a, b = map(int, key)
        h[a, b] = h[b, a] = polynomial(val)
    return h


def first_einstein_jet(g):
    # Christoffel formula, followed by contracted Riemann in the stated convention.
    gamma = [[[s.expand(SIGN[a]*(s.diff(g[a,c], X[b])+s.diff(g[a,b], X[c])-s.diff(g[b,c], X[a]))/2)
               for c in range(4)] for b in range(4)] for a in range(4)]
    ric = s.Matrix(4, 4, lambda a,b: s.expand(sum(s.diff(gamma[c][a][b], X[c])-s.diff(gamma[c][a][c], X[b]) for c in range(4))))
    scalar = sum(SIGN[a]*ric[a,a] for a in range(4))
    return s.Matrix(4, 4, lambda a,b: s.expand(ric[a,b]-(SIGN[a]*scalar/2 if a==b else 0)))


def evaluate(spec, payload):
    h = matrix(payload)
    expected = matrix(spec['EF3_H_upper_triangle'])
    checks = {}
    def zeros(name, values):
        values = list(values)
        bad = [str(s.expand(v)) for v in values if s.expand(v) != 0]
        checks[name] = {'count':len(values), 'status':'FAIL' if bad else 'PASS', 'nonzero':bad}
    zeros('neutral_component_binding', h-expected)
    # A separate tensor construction checks upper-triangle transcription too.
    r2 = sum(v*v for v in X[1:]); sym = (M+M.T)/2; skew = (M-M.T)/2
    tensor = s.zeros(4)
    for i in range(3):
        tensor[0,i+1] = tensor[i+1,0] = -X[0]*r2*Q[i]/2-r2*sum(skew[i,j]*X[j+1] for j in range(3))/5
        tensor[i+1,i+1] = -X[0]*sum(sym[k,l]*X[k+1]*X[l+1] for k in range(3) for l in range(3))/2
    zeros('neutral_expansion_matches_tensor_definition', expected-tensor)
    at0 = dict.fromkeys(X, 0)
    derivatives = [()] + [(i,) for i in range(4)] + list(itertools.combinations_with_replacement(range(4), 2))
    zeros('all_ten_components_j2H', (s.diff(h[a,b], *(X[i] for i in multi)).subs(at0) if multi else h[a,b].subs(at0)
          for a in range(4) for b in range(a,4) for multi in derivatives))
    phi0 = polynomial(spec['definitions']['phi0'])
    g = s.diag(*SIGN)*(1+2*phi0)+h
    ein = first_einstein_jet(g)
    baseline = first_einstein_jet(s.diag(*SIGN)*(1+2*phi0))
    delta = ein-baseline
    zeros('baseline_einstein', baseline-s.diag(6*B,0,0,0))
    zeros('origin_metric', g.subs(at0)-s.diag(*SIGN))
    zeros('origin_metric_first_derivatives', (s.diff(v,x).subs(at0) for v in g for x in X))
    zeros('universal_mixed_right_inverse', (delta[0,i+1]-Q[i]*X[0]-sum(M[i,j]*X[j+1] for j in range(3)) for i in range(3)))
    zeros('all_four_bianchi_first_jet', (sum(SIGN[a]*s.diff(ein[a,b],X[a]) for a in range(4)) for b in range(4)))
    basis = []
    for mu in range(4):
        for i in range(3):
            sub = {Q[j]: -6*B if mu==0 and i==j else 0 for j in range(3)}
            sub.update({M[j,k]: -6*B if mu==k+1 and i==j else 0 for j in range(3) for k in range(3)})
            image = delta.subs(sub)
            residuals = [s.diff(image[0,j+1],X[nu])-(-6*B if mu==nu and i==j else 0) for nu in range(4) for j in range(3)]
            residuals += [sum(SIGN[a]*s.diff(image[a,b],X[a]) for a in range(4)) for b in range(4)]
            zeros(f'basis_k{mu}{i+1}', residuals)
            basis.append({'basis':f'k{mu}{i+1}', 'einstein_derivative_upper':{f'{a}{b}':[str(s.diff(image[a,b],x)) for x in X] for a in range(4) for b in range(a,4)}})
    return {'status':'PASS' if all(c['status']=='PASS' for c in checks.values()) else 'FAIL', 'checks':checks,
            'full_einstein_jet_upper':{f'{a}{b}':str(ein[a,b]) for a in range(4) for b in range(a,4)}, 'basis_images':basis}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    spec=json.loads((HERE/'NEUTRAL_INPUT.json').read_text());payload=json.loads(args.candidate.read_text())
    result=evaluate(spec,payload)
    # Meaningful negative controls: the original omitted component and a wrong mixed coefficient.
    controls={}
    for name,key,change in [('missing_H00','00','x**3'),('wrong_right_inverse','01','t*x**2')]:
        altered=dict(payload);altered[key]=f'({altered[key]})+({change})'
        controls[name] = evaluate(spec,altered)['status']=='FAIL'
    assert all(controls.values())
    result.update(schema='htt.cas05.input-diagnostic.v1',scope='INPUT_ALIGNMENT_DIAGNOSTIC_ONLY_NOT_CAMPAIGN_AXIS',
                  scientific_admission='HOLD',CAS_4AXIS_PASS=False,python=platform.python_version(),sympy=s.__version__,
                  candidate_sha256=digest(args.candidate),neutral_sha256=digest(HERE/'NEUTRAL_INPUT.json'),
                  validator_sha256=digest(__file__),negative_controls=controls)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':sum(v['count'] for v in result['checks'].values()),'basis_images':len(result['basis_images']),'negative_controls':controls,'scope':result['scope'],'out':str(args.out)}))
    raise SystemExit(0 if result['status']=='PASS' else 1)


if __name__=='__main__':main()
