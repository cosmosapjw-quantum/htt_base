import hashlib, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy, scipy, mpmath

OUT=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_exact_predicate_fresh_review')
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
REL=Path('docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_03')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
initial=json.loads((OUT/'IDENTITY_INITIAL.json').read_text())
final=[]
for r in initial['records']:
    p=Path(r['path']);actual=sha(p)
    final.append(dict(path=str(p),expected=r['expected'],actual=actual,match=actual==r['expected']))
assert all(r['match'] for r in final)
write('IDENTITY_FINAL.json',dict(checked_count=len(final),all_match=True,records=final))
checks=json.loads((OUT/'INDEPENDENT_CHECKS.json').read_text())
zero=json.loads((OUT/'NEAR_TANGENT_ZERO_COUNTEREXAMPLE.json').read_text())
nonzero=json.loads((OUT/'NEAR_TANGENT_NONZERO_COUNTEREXAMPLE.json').read_text())
binding=dict(packet_id='95e5a85a0b844f73611609f1b2d45d40320a3b89309ca558aa2b84f550c6b134',
    task_id='R36-04-OPTICAL-JOINT',agent_id='/root/r36_optical_exact_predicate_fresh_review',
    input_identity='sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43',
    candidate_identity='sha256:ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b')
finding=dict(id='R36-04-EPF1',severity='P2',class_='numeric',acceptance_blocking=True,
    file=str(REL/'optical_joint.py'),line=217,related_lines=[218,257,258,259,325,326,327,328],
    title='Fixed radial shrink discards an exactly representable witness in a one-ulp overlapping lens',
    impact='The required finite easy-case execution fails with NUMERICAL_FAILURE even for an identically zero response and zero objective. This is a candidate-construction defect; no false scientific rejection or invalid accepted witness was observed.',
    cause='The physical-ball radial proposal is multiplied by 1-16*eps before the unshrunk boundary point is tested. This moves farther than the overlap width and outside the direct ball. The zero-response path returns this absent anchor, and the certificate fallback repeats it before claiming no representable witness.',
    exact_oracle='center=(1/4-2^-55,0,0), e_d=Dmax=1/8; witness=(1/8,0,0). Direct squared slack is 2^-57-2^-110>0, physical squared slack is zero. With S=O=0 its residual is exactly zero and is strictly below B=.001.',
    counterexample=zero,corroborating_nonzero_case=nonzero,
    recommendation='Try exact-verified unshrunk radial/boundary candidates before an inward adjustment; any adjustment must retain both original-ball memberships. Keep a typed unsupported outcome only when the available proposal/certificate remains unresolved, not for this explicitly representable elementary witness.')
repair_plan=(
    'One bounded candidate-construction repair of the same R36-04-OPTICAL-JOINT task from candidate '
    'sha256:ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b. Preserve repair_03, '
    'all earlier candidates, failures, exact sources and cumulative task/attempt/cost limits. No Ultra escalation, '
    'budget reset, new physics or additional assurance ladder is requested. Restrict implementation to the next '
    'controller-designated immutable candidate optical_joint.py feasible-witness construction and its focused '
    'regression test; regenerate affected consumer artifacts only if necessary. For center=(nextafter(.25,0),0,0), '
    'e_d=Dmax=.125, O=0, B=.001, both S=0 and S=diag(.001,-.001,0) must return a compatible result with a '
    'binary64 witness satisfying both existing exact Fraction predicates. The explicit witness (.125,0,0) '
    'is available and has a residual safely below the unchanged budget. Test the unshrunk physical-boundary '
    'proposal before shrinking it, or construct another exact-verified representable witness in the overlap; '
    'do not use a fixed shrink that crosses the direct-ball boundary. Preserve exact tangency handling, '
    'the nonrepresentable tangent typed failure, NCF1 exact emptiness, directed endpoint/score enclosures, '
    'all seven signed components, shared budget, fixed frame/c/units and full covariance. Add the adjacent '
    'one-ulp exterior center as an exact-empty control. Run the focused suite and the actual consumer in an '
    'external small fixture; reuse unchanged passing evidence. Return the new candidate to a different fresh '
    'nonauthor reviewer. No production/STATE/Git writes by this reviewer, no native solver/ODE, original42 '
    'promotion or scientific admission follows.')
validation=[
    f'{len(final)} frozen source/candidate/historical/raw identities matched before and after review; IDENTITY_INITIAL.json and IDENTITY_FINAL.json',
    'External-fixture pytest: 18 passed, one unrelated Matplotlib Axes3D warning; PYTEST.stdout and EXECUTION_RECEIPTS.json',
    'Actual consumer in external small fixture exited 0; RESULT exact semantic equality and TABLE byte equality; CONSUMER_COMPARISON.json',
    'Independent checks: 25 PASS, 2 FAIL reproductions of one P2 defect; INDEPENDENT_CHECKS.json, INDEPENDENT.stdout and INDEPENDENT.stderr',
    'NCF1 exact Fraction emptiness, NCF2 directed sqrt2/sqrt3 and upper score, NCF3 tangent witness all passed',
    '18 exact rational one-axis interval cases passed at common output scales 1, 1e-30 and 1e-150, including unequal .0001 physical radius; exact witness memberships and residual bounds checked',
    'Independent full-tensor index formula, Gram identity, full correlated covariance including cross terms, all 8 response Jacobian columns and three-axis rotation passed',
    'Tiny nonzero S=1e-200, zero/singleton/empty sets and typed large-output/K-overflow controls passed',
    'Finite-z source control and shifted corrected observer chart passed; all three generated figures visually inspected and readable',
    'Primary chart source checked: https://arxiv.org/html/2312.09875v3; imported frozen HUBBLE_PROTOCOL.json reused; no unchanged theorem re-proving or exact CAS gate added'
]
claim_audit=dict(owner='common optical response; obsstat source estimator',scope='independent C0 conditional-method numerical review',
    transfer_source='none',claim_tier='C0',evidence_read=['NEXT_032 and ACK_032_GO','actual author RETURN and bound candidate','frozen Hubble protocol and approved norm-bound framing','candidate code/tests/result/interpretation','raw finite independent executions'],
    proposed_changes='No candidate edits. Return same-task bounded candidate-construction repair criterion.',tests_to_run='Completed focused suite, consumer replay and independent checks; repair regression belongs to the implementation owner.',
    risks_and_kill_switches='Source drift or changed scientific conventions stop the bounded review. General unresolved numerical cases remain typed; this explicit representable easy witness must execute.',
    artifacts_status='HOLD; no qualified product',upgraded_claims=[],downgraded_claims=['Candidate acceptance remains false pending P2 repair and fresh independent review'],
    forbidden_drift_detected=False,ledger_updates_needed='Host records this identity-bound review; no repository claim ledger or historical acceptance edits.',
    caveats=['CF4 direct-dipole law, empirical joint covariance and finite-z/selection/uncertain-S radii remain unavailable.','No native solver, ODE, original42 promotion or publication approval.','Requested gpt-6-astra/xhigh; actual model and effort remain UNKNOWN.'])
review={**binding,'review_decision':'HOLD','acceptance_met':False,'qualified_products':[],
    'findings':[finding],'validation_evidence':validation,'claim_audit':claim_audit,
    'independence':{'authored_candidate':False,'prior_reviewer_verdict_files_read':False,'previous_review_files_hashed_only':True,'framing_read':'NORM_BOUND_CONTRACT.json plus mandatory controller repair requirements','production_writes':False},
    'requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN',
    'environment':{'python':sys.version,'numpy':numpy.__version__,'scipy':scipy.__version__,'mpmath':mpmath.__version__,'platform':platform.platform()},
    'finished_utc':datetime.now(timezone.utc).isoformat()}
write('REVIEW_RESULT.json',review)
(OUT/'REVIEW.md').write_text('''# R36-04 repair_03 independent review: HOLD

Candidate `sha256:ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b` has one acceptance-blocking P2 execution defect. No candidate or production file was edited.

At `optical_joint.py:217`, the radial anchor is shrunk by `1-16*eps` before testing the unshrunk boundary candidate. Let `center=(nextafter(.25,0),0,0)`, `e_d=Dmax=.125`, `O=0`, and `B=.001`. Both `S=0` and `S=diag(.001,-.001,0)` raise `NUMERICAL_FAILURE: no representable feasible witness`. Yet `d=(.125,0,0)` is exactly representable and satisfies both original closed balls. Its direct squared slack is `2^-57-2^-110>0`; its physical squared slack is zero. The residual is zero for `S=0` and approximately `2.80336e-4` for the nonzero case, safely below `.001`. The fallback at lines 325–328 repeats the failed shrunken anchor.

This is a candidate-construction failure, distinct from a legitimate unsupported or nonrepresentable set. The current contract explicitly requires finite easy cases to execute. The exact ball predicates should remain unchanged. A bounded repair should test the unshrunk boundary proposal or another exact-verified feasible witness before shrinking, and verify that any inward adjustment remains inside the direct ball. Add the one-ulp interior/exterior controls while retaining all current numerical and physical requirements.

225 identities matched before and after review. The focused suite passed 18 tests. The actual consumer ran in a small copied external fixture: RESULT matched semantically and TABLE matched byte-for-byte. Independent checks passed 25 cases, with two reproductions of this one defect. Passing checks include the required exact-empty, directed square-root/score and exact-tangent controls; 18 rational one-axis interval cases across three common-unit scales; full tensor reconstruction; correlated covariance including cross terms; all eight response derivatives; rotation; tiny nonzero response; typed range errors; and finite-z/chart controls. All three replay figures were inspected. The unrelated Matplotlib Axes3D warning did not affect these 2D outputs.

The conditional chart interpretation is consistent with the checked [primary source](https://arxiv.org/html/2312.09875v3); the frozen Hubble protocol and norm-bound framing were reused. The candidate retains C0 conditional-method limits and unavailable empirical CF4 inputs. No native solver, ODE, old CAS or original42 acceptance is promoted.

Requested reviewer runtime: gpt-6-astra/xhigh. Observed runtime: UNKNOWN. Review execution and outputs are bound in REVIEW_RESULT.json, RAW_RECEIPT.json, CONTROLLER_RETURN.json and SEAL.json.
''')
issue={'class':'numeric','question':'Does finite easy closed-ball membership retain an available binary64 witness one ulp inside external tangency?',
    'exact_missing_or_defect':finding['title']+'; optical_joint.py:217 and certificate fallback at lines 325-328.',
    'input_identity':binding['input_identity'],'candidate_identity':binding['candidate_identity'],
    'substantive':True,'high_consequence':False,'severity':'P2','finding_ids':['R36-04-EPF1'],
    'risk':finding['impact']}
counterexample={'case_id':'R36-04-EPF1','zero_response':zero,'nonzero_response':nonzero,'expected':'compatible true with exact verified witness','observed':'typed NUMERICAL_FAILURE despite explicit available binary64 witness'}
result={**binding,'outcome':'blocker','review_decision':'HOLD','acceptance_met':False,'qualified_products':[],
    'validation_evidence':validation,'issue':issue,'substantive_failure':True,'counterexample':counterexample,'repair_plan':repair_plan,
    'requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN',
    'raw_receipt':str(OUT/'RAW_RECEIPT.json')}
def file_record(p): return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
evidence=[OUT/n for n in ['REVIEW_RESULT.json','REVIEW.md','IDENTITY_INITIAL.json','IDENTITY_FINAL.json','EXECUTION_RECEIPTS.json','PYTEST.stdout','PYTEST.stderr','CONSUMER.stdout','CONSUMER.stderr','CONSUMER_COMPARISON.json','INDEPENDENT_CHECKS.json','INDEPENDENT.stdout','INDEPENDENT.stderr','NEAR_TANGENT_ZERO_COUNTEREXAMPLE.json','NEAR_TANGENT_NONZERO_COUNTEREXAMPLE.json','independent_checks.py','prepare_and_run.py','JOINT_RESPONSE.png','SOURCE_AND_FINITE_Z.png','NORM_BOUND_DECISION.png']]
raw={**result,'raw_receipt_kind':'actual_fresh_independent_readonly_review','evidence':[file_record(p) for p in evidence],
    'acknowledgement':file_record(Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_032_GO.json')),
    'formal_packet':file_record(Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/NEXT_032.json')),
    'reviewer_source':file_record(OUT/'seal_review.py')}
write('RAW_RECEIPT.json',raw)
write('CONTROLLER_RETURN.json',{**result,'raw_receipt_sha256':sha(OUT/'RAW_RECEIPT.json')})
write('SEAL.json',{**binding,'files':[file_record(p) for p in evidence+[OUT/'RAW_RECEIPT.json',OUT/'CONTROLLER_RETURN.json',OUT/'seal_review.py']],
    'scope':'review evidence only; candidate unchanged; no admission'})
print(json.dumps({'review':'HOLD','finding':'R36-04-EPF1','severity':'P2','return':str(OUT/'CONTROLLER_RETURN.json'),'raw_sha256':sha(OUT/'RAW_RECEIPT.json'),'seal_sha256':sha(OUT/'SEAL.json')},indent=2))
