import datetime
import hashlib
import json
from pathlib import Path
import subprocess

H = Path(__file__).resolve().parent
R = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
P = R/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-03-H03-STRUCTURED'
N = P/'repair_01'
num = json.loads((H/'INDEPENDENT_NUMERICS.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
dump = lambda p,j: Path(p).write_text(json.dumps(j,indent=2)+'\n')
expected='4a31b981231a10b449bee2b7be65d0efc181dbd077f35ea55cb23ac38caf4c9d'
assert sha(N/'ARTIFACT_MANIFEST.json')==expected
for folder in (P,N):
    for item in json.loads((folder/'ARTIFACT_MANIFEST.json').read_text())['artifacts']:
        assert sha(folder/item['path'])==item['sha256']

report = '''The repaired candidate receives SCOPED_PASS for the conditional structured_frontier repair scope. This is independent review preparation for manifest 4a31b981231a10b449bee2b7be65d0efc181dbd077f35ea55cb23ac38caf4c9d, pending the actual formal controller review packet. It is not an ACK, controller admission, publication decision, or original42 acceptance. Requested reviewer is gpt-6-astra/xhigh; observed runtime remains UNKNOWN. This reviewer did not frame or implement the candidate. The original review and its repair plan were read as the governing targeted closeout scope; no harness or skill verdict was used as a correctness oracle.

Evidence read: both candidate manifests and their bound artifacts; immutable H03 tomography and physical-results inputs; the original contract's H03 sections; the preserved original review/repair plan; repaired consumer, tests, manuscript, figures, RESULT and CONTROLLER_RETURN. All manifested artifacts for both candidates and all repaired source identities were rehashed successfully. The source carrier is byte-identical between candidates. The prior HOLD and its formal binding were preserved.

The three blocking defects are closed within this scope:

- H03-R1: consumer.py:109-129 separates an asserted analytical equality identity from finite-precision proximity. Independent rank-one samples at floor=tau without that identity and at tau+/-5e-10 return NUMERIC_BOUNDARY_FLOOR with no finite rho or q. Materially above is unattainable; materially below has the correct finite crossing. No feasibility tolerance was relaxed.
- H03-R2: consumer.py:41-75 and 142-151 compare projected singular values to ||WD|| before relative-to-largest-B classification. With the actual retained matrices, D=X has projected Frobenius norm 2.2883204606165413e-15 and unprojected norm 7.83391107141197. Its exact structural identity produces rank zero and T=T0 for rho=0,1,10,1e100; the unqualified call returns NUMERIC_RANK_HOLD. Uncertified small nonzero responses at relative scales 1e-14,1e-12,5e-11 are held, not declared zero. The actual three designs retain ranks 3/3/6, with minimum projected/global ratios 0.17669957,0.09004754,0.01280879.
- H03-R3: consumer.py:132-139 uses the boundary status consistently for both budgets. For B=(1,0)^T, r=(1,sqrt(tau)), the established equality floor=tau<T0 gives rho_sat=1 and q_min=1. The exact already-adequate baseline gives zero for both budgets.

The actual repaired consumer was imported from the bound product source and run with only HERE redirected into this review directory. It consumed the same frozen inputs and exercised its full controls, including D=L radial recovery and signed witness/refit/KKT checks. All 363 output curve points, floors, saturation radii, threshold radii, q minima and crossing multipliers equal both original and repaired saved results exactly. The original irreducible-floor figure was reused rather than regenerated.

An independent calculation re-extracted y from theta9 and C from all 36D source coordinates, retaining every 12D marginal entry, including 108 nonzero cross-window entries. It used symmetric eigen whitening, a six-dimensional left-null basis, and coefficient normal equations instead of the author's Cholesky/projector/SVD implementation. It gives T0=23.396720522667138, minimum covariance eigenvalue 0.003831267441054777, and the fixed tau=12.591587243743977. The independent design results are:

| Design | Rank | Floor | rho95 | Max curve error |
|---|---:|---:|---:|---:|
| Depth slope | 3 | 15.31600239641714 | unattainable | 4.27e-14 |
| FP composition | 3 | 6.660568527209009 | 5.750880608573553 | 4.27e-14 |
| Joint | 6 | 1.281898970984144e-30 | 1.589671174065129 | 4.98e-14 |

The two independent direct GLS witness refits reach tau within 3e-14. Existing tolerances, X, D definitions, M=I, units/frame, df=6, and the conditional covariance law were retained. The nine candidate tests were rerun with bytecode/cache writing disabled: 9 passed. Their success is corroborating evidence, not the mathematical oracle. A Matplotlib Axes3D import warning is unrelated to the two-dimensional figures.

All five pages of the exact manifested PDF were rendered at 120 dpi and visually inspected. The new paragraph on page 2 accurately states the numerical-boundary and unprojected-scale guard. Figures, captions, and Table I match the consumed generated values; no clipping, missing figures, broken equations, or unresolved references were seen. The retained final TeX log reports five pages and no overfull/undefined errors; two underfull bibliography boxes are cosmetic. Compilation was not repeated because the assigned affected PDF was already manifested and rendered successfully; the unchanged derivations and previous build evidence were reused.

No new physical calibration, null-coverage, native-solver, family-identification, or full x/F/Pi/Q/G_F claim follows. The interpretation remains a sensitivity calculation for declared finite-window designs under the retained Gaussian working covariance. Original42 stays false. No additional physical covariance model or tolerance relaxation was introduced.

Proposed changes: none in the assigned repair scope. Required next artifact/action: bind this exact review result and candidate to the actual controller review packet, verify the packet's candidate/input identity and acknowledgement, and let the controller decide scoped structured_frontier admission. No product, Git, STATE, or historical review file was written. A changed candidate/source identity or broader physical claim is outside this verdict and requires its own bounded review.
'''
(H/'REVIEW.md').write_text(report)
preserved = []
for name in ('RESULT.json','RAW_RECEIPT.json','RAW_FORMAL_BINDING.json','FORMAL_BINDING_RESULT.json'):
    path = Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_fresh_independent_review')/name
    if path.exists():
        preserved.append({'path':str(path),'sha256':sha(path),'modified_by_this_reviewer':False})
evidence=[H/'REVIEW.md',H/'INDEPENDENT_NUMERICS.json',H/'review_probe.py',H/'raw/independent_probe.stdout',
    H/'raw/independent_probe.stderr',H/'raw/consumer.stdout',H/'raw/consumer.stderr',
    H/'raw/pytest.stdout',H/'raw/pytest.stderr',H/'raw/pdfinfo.stdout',H/'rendered/main.txt']
evidence += sorted((H/'rendered').glob('page-*.png'))
raw={'schema':'H03_REPAIRED_FRESH_INDEPENDENT_REVIEW_RAW_v1',
    'task_id':'R32-03-H03-STRUCTURED','reviewer_agent':'/root/r35_h03_repaired_fresh_review',
    'requested_model':'gpt-6-astra','requested_effort':'xhigh','observed_runtime':'UNKNOWN',
    'candidate_identity':'sha256:'+expected,'candidate_input_identity':num['input_identity'],
    'candidate_manifest':str(N/'ARTIFACT_MANIFEST.json'),
    'formal_packet_id':None,'formal_input_identity':None,'formal_review_packet_status':'PENDING',
    'cwd':str(R),'checkout_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
    'checkout_branch':subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip(),
    'environment':num['environment'],
    'commands':[
        {'command':'python -B '+str(H/'review_probe.py'),'exit_status':0,
         'stdout':str(H/'raw/independent_probe.stdout'),'stderr':str(H/'raw/independent_probe.stderr'),
         'consumer_elapsed_seconds':num['consumer_seconds'],
         'description':'exact consumer with external output root plus independently authored numerical falsifiers'},
        {'command':'PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -q -p no:cacheprovider '+str(N/'test_boundary_repair.py'),
         'exit_status':0,'result':'9 passed, one unrelated Matplotlib Axes3D import warning',
         'stdout':str(H/'raw/pytest.stdout'),'stderr':str(H/'raw/pytest.stderr')},
        {'command':'pdftoppm -r 120 -png '+str(N/'main.pdf')+' '+str(H/'rendered/page'),
         'exit_status':0,'rendered_pages':5,'visually_inspected_pages':[1,2,3,4,5]},
        {'command':'pdftotext -layout '+str(N/'main.pdf')+' '+str(H/'rendered/main.txt'),'exit_status':0},
        {'command':'pdfinfo '+str(N/'main.pdf'),'exit_status':0,'stdout':str(H/'raw/pdfinfo.stdout')}],
    'candidate_and_original_manifest_artifacts_verified_unchanged_at_closeout':True,
    'preserved_first_failure_evidence':preserved,
    'implementation_writes':False,'git_writes':False,'controller_state_writes':False,
    'write_scope':str(H),'new_covariance_law':False,'tolerance_relaxation':False,
    'source_reintegration':False,'full_campaign_rerun':False,'CAS_relaunch':False,
    'evidence':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence],
    'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
dump(H/'RAW_RECEIPT.json',raw)
result={'schema':'H03_REPAIRED_FRESH_INDEPENDENT_REVIEW_RESULT_v1',
    'task_id':'R32-03-H03-STRUCTURED','verdict':'SCOPED_PASS','status':'SCOPED_PASS',
    'review_scope':'affected rank/boundary repair, original-three-design output equality, full covariance, five-page manuscript',
    'candidate_identity':'sha256:'+expected,'candidate_manifest':str(N/'ARTIFACT_MANIFEST.json'),
    'candidate_input_identity':num['input_identity'],
    'original_candidate_identity':'sha256:85ac1bfdfc71dea645c01421811ed1e5d95df617034077c532feee6052a769ba',
    'candidate_unchanged':True,'conditional_candidate_scope_satisfied':True,
    'acceptance_met':False,'acceptance_scope':'structured_frontier only; formal controller admission pending',
    'proposed_qualified_products':['structured_frontier'],'qualified_products':[],
    'original42_acceptance':False,'formal_review_packet_status':'PENDING',
    'formal_packet_id':None,'formal_input_identity':None,'formal_acknowledgement':'NOT_MADE',
    'publication_decision':'NOT_MADE','reviewer_agent':'/root/r35_h03_repaired_fresh_review',
    'requested_model':'gpt-6-astra','requested_effort':'xhigh','observed_runtime':'UNKNOWN',
    'independence':{'framed_candidate':False,'implemented_candidate':False,
        'prior_targeted_review_and_repair_plan_read':True,'harness_or_skill_verdict_used_as_oracle':False,
        'independent_calculation':'symmetric eigen whitening plus 6D left-null basis and normal equations'},
    'findings':[],
    'closed_findings':['H03-R1','H03-R2','H03-R3'],
    'counterexample':None,'bounded_repair':None,
    'numerical_checks':{'D_equals_X_rank':0,'D_equals_X_no_gain':True,
        'uncertain_floor_plus_minus_5e_minus_10':'NUMERIC_BOUNDARY_FLOOR with no rho/q',
        'exact_floor_equality_rho':1.0,'exact_floor_equality_q_min':1.0,
        'actual_design_ranks':[3,3,6],'curve_points_checked':363,
        'actual_consumer_original_curve_max_abs_error':0.0,
        'independent_curve_max_abs_error':max(d['curve_max_abs_error'] for d in num['independent_designs'].values()),
        'full12_covariance_exact':True,'fixed_df':6,'tau':12.591587243743977,
        'candidate_tests':'9 passed'},
    'rendered_pdf':{'pages':5,'all_pages_visually_inspected':True,'blocking_findings':[],
        'cosmetic_notes':['two retained underfull bibliography boxes'],
        'build_rerun':False,'reason':'manifested PDF rendered; final existing build log reused'},
    'scientific_ceiling':'conditional finite-window sensitivity design; physical x/F/Pi/Q/G_F undefined',
    'raw_receipt':str(H/'RAW_RECEIPT.json'),'review_report':str(H/'REVIEW.md'),
    'validation_evidence':[str(p) for p in evidence],
    'next_executable_checkpoint':'Bind this result to the later exact formal controller review packet; verify candidate/input/ACK identity before controller-scoped structured_frontier admission. Preserve the first HOLD and original42.'}
dump(H/'RESULT.json',result)
print(json.dumps({'verdict':result['verdict'],'result':str(H/'RESULT.json'),
    'result_sha256':sha(H/'RESULT.json'),'candidate_identity':result['candidate_identity'],
    'formal_review_packet_status':result['formal_review_packet_status']},indent=2))
