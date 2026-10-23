import hashlib, json, subprocess, sys
from pathlib import Path
import sympy as S
s,o,r,p,A,z,b,ell,rho=S.symbols('s o r p A z b ell rho', real=True)
endpoint=S.expand((2*s-o)-(s-o)-A*(s-r-p))
h=1+z-z*A
B=(1+z)*(1-A)
special=endpoint.subs({s:(1+z)*b,o:b+ell})
checks={
 'observer_endpoint_cancels': S.diff(endpoint,o),
 'same_observer_history': S.expand(special.subs({r:b+ell,p:0})-(h*b+A*ell)),
 'fixed_reference_history': S.expand(special.subs({r:0,p:0})-B*b),
 'radiation_reference_history': S.expand(special.subs({r:-rho*b,p:0})-(B-rho*A)*b),
 'quotient_column_difference': S.expand(B-(h-A)),
 'dimensionless_pv_sign': S.diff(endpoint,p)-A,
}
# Exact finite-dimensional illustration of the newly derived quotient identity.
# This is a rational algebra witness, not a retained-design or observational rank.
a=S.Matrix([1,2,3,4]); history=S.Matrix([2,-1,4,3]); identity=S.eye(4)
projector=identity-a*(a.T*a).inv()*a.T
checks['quotient_exact_annihilation']=(projector*a).norm()
checks['quotient_exact_history_equivalence']=(projector*(history-a)-projector*history).norm()
# Full nuisance quotient must include the combined response K-D E.
D=S.diag(S.Rational(2),S.Rational(3)); K=S.Matrix([1,0]); E=S.Matrix([0,1])
Q=K-D*E
Pq=S.eye(2)-Q*(Q.T*Q).inv()*Q.T
checks['combined_nuisance_annihilation']=(Pq*Q).norm()
# Splitting two channels belonging to one nuisance would remove an extra dimension.
combined_rank=Q.rank(); split_rank=S.Matrix.hstack(K,-D*E).rank()
# Retain empirical rank as NOT_EVALUATED; only the formal identities are tested.
assert all(v == 0 for v in checks.values()), checks
root=Path('docs/research_program/observational_publication_20261015')
paths=['FRONTIER_20261020/theory/THEORY.md','FRONTIER_20261020/theory/CLAIMS_AND_TRANSFER.json','FRONTIER_20261020/projection/RESULT.json','ADVERSARIAL_AUDIT_20261022/theory/THEORY_AUDIT.md','ADVERSARIAL_AUDIT_20261022/continuation/two_redshift_pipeline/REPORT.md','CONTINUOUS_RESEARCH_20261023/execution/R23-Q/RETURN.json','CONTINUOUS_RESEARCH_20261023/execution/R23-SN/RETURN.json']
print(json.dumps({'status':'PASS_FINITE_ALGEBRA_ONLY','python':sys.version.split()[0],'sympy':S.__version__,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'checks':{k:str(v) for k,v in checks.items()},'combined_single_parameter_nuisance_rank':combined_rank,'incorrectly_split_nuisance_rank':split_rank,'new_retained_design_rank':'NOT_EVALUATED_UNQUALIFIED_PHYSICAL_PROCESSING_RESPONSE','input_sha256':{str(root/x):hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths}},indent=2))
