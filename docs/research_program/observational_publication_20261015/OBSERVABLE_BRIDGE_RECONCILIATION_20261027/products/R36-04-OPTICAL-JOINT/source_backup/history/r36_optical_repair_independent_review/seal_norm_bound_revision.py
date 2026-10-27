from pathlib import Path
import json,hashlib,datetime
P=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_repair_independent_review')
def rec(p):p=Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def save(n,x):(P/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
original=json.loads((P/'REVIEW_RESULT.json').read_text())
contract={
 'schema':'htt.r36.optical_norm_bound_repair_contract/1',
 'scope':'Read-only framing addendum for the same bounded R36-04 repair; no new experiment, verdict, source or tolerance.',
 'review_result_preimage':rec(P/'REVIEW_RESULT.json'),
 'norm_objective':'phi(d)=||O-A d||_2; r=O-A d; q=-A^T r/||r|| if r!=0.',
 'constraints':'g1(d)=||d-d_obs||-e_d; optional g2(d)=||d||-Dmax. Let n_i be a valid subgradient of g_i at the evaluation anchor d.',
 'diameter_upper_bound':'D=min(e_d+||d-d_obs||, Dmax+||d||) when both balls apply; use e_d+||d-d_obs|| if there is no physical ball. D is any conservatively rounded upper bound on sup_{z in C}||z-d||.',
 'lower_bound':'For arbitrary lambda_i>=0, LB=phi(d)+sum_i lambda_i*g_i(d)-||q+sum_i lambda_i*n_i||*D <= min_{z in C} phi(z). max(0,LB) is also a valid lower bound.',
 'proof':[
  'Convexity of phi yields phi(z)>=phi(d)+q dot (z-d).',
  'Convexity of g_i and g_i(z)<=0 yield n_i dot (z-d)<=-g_i(d). Multiplication by nonnegative lambda_i preserves that inequality.',
  'Write q dot v=(q+sum lambda_i*n_i) dot v-sum lambda_i*n_i dot v, then use Cauchy and ||v||<=D.',
  'The proof uses any evaluation anchor d and any nonnegative lambda. Neither solver convergence nor exact KKT/complementarity is assumed. A poor multiplier or anchor makes the bound weaker, never invalid in exact arithmetic.'
 ],
 'degenerate_cases':[
  'At a constraint center, any n_i with ||n_i||<=1 is a valid norm subgradient; n_i=0 is allowed. Do not divide by zero.',
  'At r=0, q=0 is valid; more generally q=-A^T u with ||u||<=1. Do not divide by zero.',
  'Singleton, tangent and empty intersections retain explicit set handling. For an empty set, no objective bound is needed; certify emptiness geometrically.',
  'Multipliers must be finite and nonnegative; no negative numerical least-squares multiplier may be used in the lower certificate.'
 ],
 'floating_point_contract':[
  'This exact-arithmetic proof does not itself certify binary64 calculations. Implement conservative enclosures for phi, g_i, q/n_i, multipliers, stationarity norm, D and the final arithmetic. Evaluate D as an upper bound and the final LB as a lower bound; include response and cancellation errors consistently. Higher precision or interval/outward arithmetic is allowed in a bounded ambiguous branch.',
  'Scale before norms and products; avoid squared dual constants or subtraction of large nearly equal O^T O terms. Dimensionless normalized objective bounds must be converted back to magnitude units with conservative range/error handling.',
  'A true verdict requires an independently verified primal witness inside the original closed balls and its actual seven-component residual upper bound <= the unchanged B, subject only to the existing justified cancellation allowance. No optimizer feasibility tolerance can enlarge e_d or Dmax.',
  'A false verdict for a nonempty feasible set requires the conservative lower bound to exceed B after accounting for any applicable allowed roundoff. For a global rejection the allowance/error envelope must cover every feasible candidate to which it could apply; do not use the current iterate as an unjustified global scale bound.',
  'If feasible upper and valid lower bounds do not decide membership, return typed NUMERICAL_FAILURE/unresolved. Finite easy cases must remain executable; do not replace the profile wholesale by an unconditional unresolved return.',
  'A small certificate residual does not prove an accurate minimum score. Report a certified score interval/upper bound when appropriate or require a justified objective gap before labelling a scalar as the profiled optimum.'
 ],
 'accepted_use':'Preferred norm-based alternative to the original review repair_plan squared-objective support/dual option. Keep the complete scope, failure preservation, exact cases, range guard and tests from that plan.',
 'requested_reviewer_runtime':{'model':'gpt-6-astra','reasoning_effort':'xhigh'},'observed_runtime':'UNKNOWN','actual_new_numerical_execution':False,'qualification':False
}
save('NORM_BOUND_CONTRACT.json',contract)
revision=dict(original)
revision['schema']='htt.r36.optical_repair_independent_review/2'
revision['review_revision']={'preimage':rec(P/'REVIEW_RESULT.json'),'kind':'Repair framing clarification only; same negative findings, frozen candidate and raw executions. Norm lower bound supplied as a parent proposal and independently validated algebraically by reviewer.','new_numerical_execution':False,'new_verdict':False,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
revision['repair_plan'] += '\n\nPreferred numerical certificate refinement: use the nonsquared norm-objective lower bound validated in '+str(P/'NORM_BOUND_CONTRACT.json')+' (sha256:'+rec(P/'NORM_BOUND_CONTRACT.json')['sha256']+'). For phi(d)=||O-A d||, q=-A^T r/||r|| (valid zero-residual subgradient at r=0), g1=||d-d_obs||-e_d, optional g2=||d||-Dmax, norm-constraint subgradients n_i and arbitrary finite lambda_i>=0, min_C phi >= phi(d)+sum lambda_i*g_i(d)-||q+sum lambda_i*n_i||*D, where D is an upper bound from the minimum of the applicable ball triangle bounds. This follows from convex supporting inequalities plus Cauchy, with no KKT convergence assumption. Use valid zero-center subgradients; conservatively enclose every quantity and accumulated arithmetic error, round D upward and the final certificate downward, and apply only the original justified signal-cancellation error policy. A verified primal upper bound decides true, a conservative lower bound above B decides false, and an undecided interval yields typed numerical unresolved. Strict original-ball feasibility is independent of normalized optimizer tolerances. All prior scope and preservation requirements remain.'
revision['norm_bound_contract']=rec(P/'NORM_BOUND_CONTRACT.json')
revision['raw_receipt']=str(P/'RAW_RECEIPT_002_NORM_BOUND.json')
save('REVIEW_RESULT_002_NORM_BOUND.json',revision)
raw=json.loads((P/'RAW_RECEIPT.json').read_text())
raw['schema']='htt.r36.optical_repair_review_raw_receipt/2';raw['prior_raw_receipt']=rec(P/'RAW_RECEIPT.json');raw['review_result']=rec(P/'REVIEW_RESULT_002_NORM_BOUND.json');raw['norm_bound_contract']=rec(P/'NORM_BOUND_CONTRACT.json');raw['new_numerical_execution']=False
save('RAW_RECEIPT_002_NORM_BOUND.json',raw)
seal={'schema':'htt.r36.review_seal/2','review_result':rec(P/'REVIEW_RESULT_002_NORM_BOUND.json'),'raw_receipt':rec(P/'RAW_RECEIPT_002_NORM_BOUND.json'),'norm_bound_contract':rec(P/'NORM_BOUND_CONTRACT.json'),'previous_seal':rec(P/'SEAL.json'),'revision_script':rec(P/'seal_norm_bound_revision.py')}
save('SEAL_002_NORM_BOUND.json',seal)
print(json.dumps(seal,indent=2))
