from pathlib import Path
import datetime,hashlib,json
p=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-03-H03-STRUCTURED')
o=Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_fresh_independent_review')
n=json.loads((o/'INDEPENDENT_NUMERICS.json').read_text());ad=json.loads((o/'ADDITIONAL_PROBES.json').read_text());build=json.loads((o/'BUILD_RESULT.json').read_text())
manifest_hash=hashlib.sha256((p/'ARTIFACT_MANIFEST.json').read_bytes()).hexdigest();assert manifest_hash==n['candidate_identity']
findings=[
 {'id':'H03-R1','severity':'P2','blocking':True,'issue_class':'FEASIBILITY_TOLERANCE_PROMOTED_TO_EXACT_ATTAINMENT','path':str(p/'consumer.py'),'lines':[88,103],'contract_lines':[82,93],'summary':'A numerical band around the floor is promoted to exact equality and a finite minimum budget. A floor strictly above tau cannot attain tau, irrespective of closeness.','counterexample':{'call':'threshold(np.array([1.]), np.array([1.]), tau+5e-10, 1., tau+1.+5e-10, tau)','tau':12.591587243743977,'returned_status':'FINITE_FLOOR_EQUALITY','returned_rho95':1.0,'true_irreducible_T':12.591587244243977,'true_attainability':False},'fix':'Keep numerical-boundary qualification separate from exact synthetic equality. Never issue a finite budget when the certified floor is above tau. For a finite-precision floor within 1e-9 without an exact equality identity, return NUMERIC_BOUNDARY_FLOOR/HOLD with no finite budget; known exact floor=tau fixtures attain at rho_sat.'},
 {'id':'H03-R2','severity':'P2','blocking':True,'issue_class':'PROJECTED_ROUNDOFF_SELF_NORMALIZED_AS_SIGNAL_RANK','path':str(p/'consumer.py'),'lines':[40,54],'related_lines':[171,174],'contract_lines':[80,95],'summary':'The projected-zero design D=X becomes rank six when numerical projection noise is normalized by its own maximum singular value. The existing control does not call the production SVD/curve path for D=X.','counterexample':{'case':'Retained source, D=X, B=(I-Q Q.T) @ solve_triangular(L,X,lower=True)','expected_rank':0,'observed_rank':6,'projected_frobenius_norm':2.2883204606165413e-15,'T0':23.39672052266718,'false_floor':22.491757346596945,'false_saturation_budget':1.9830537191258547e17,'independent_numpy_solve_false_floor':ad['zero_design_solver_false_gain']['solver_T_at_saturation']},'fix':'Handle known exact signal-span/zero designs through the same analysis path, with a positive unprojected reference scale and explicit roundoff uncertainty handling. Do not infer new physical directions or zero a genuinely nonzero small response.'},
 {'id':'H03-R3','severity':'P2','blocking':True,'issue_class':'ATTAINED_EQUALITY_IMAGE_BUDGET_DROPPED','path':str(p/'consumer.py'),'lines':[110,110],'contract_lines':[91,91],'summary':'The secondary image-budget calculation uses floor<tau rather than the contracted floor<=tau and reports None at an attained equality.','counterexample':{'T0':'tau+1','floor':'tau','exact_minimum_coefficient_budget':1.0,'exact_minimum_image_budget':1.0,'returned_q_min_restricted':None},'fix':'Use the same exact-equality/qualified-boundary classification for both coefficient and image budgets; an analytically established floor=tau has q_min=sqrt(T0-tau), not None.'}
]
repair_plan=(
 'Authorize one bounded lower-tier repair preparation in a NEW sibling directory designated by the controller; preserve the entire first candidate and manifest 85ac1bfdfc71dea645c01421811ed1e5d95df617034077c532feee6052a769ba. Actual repair execution and candidate regeneration require the later formal current-controller repair packet; this review is not a packet, ACK, execution record, or publication decision. Modify only the numerical boundary/rank handling and their controls in consumer.py, then regenerate directly dependent evidence/manuscript assets as needed. '
 'Keep immutable source hashes, full 36D-to-12D covariance extraction, all off-diagonals, X, all three D designs, M=I, units/frame, fixed df=6, tau=12.591587243743977, baseline and unrestricted comparator unchanged. '
 'Boundary policy: distinguish analytically specified equality from uncertain floating-point proximity. A floor above tau must never receive a finite budget because abs(floor-tau)<=1e-9. For actual numerical floors inside that band without an exact equality identity, return a numerical-boundary HOLD and no finite rho/q. For a declared exact floor=tau<T0 fixture, return the finite minimum-norm least-squares radius rho_sat and q_min=sqrt(T0-tau); preserve zero budget for an established already-adequate baseline. '
 'Rank repair: preserve CONTRACT.md:93 relative-to-largest-B resolved-rank rules for a certified nonzero projected response, but precede them with a positive global reference that cannot self-normalize projection roundoff: E=W D M^(-1/2), s_ref=||E||_2. D=0 is exact zero. For s_ref>0, inspect singular values of B relative to s_ref; >=1e-10 certifies resolved directions, (1e-12,1e-10) is NUMERIC_RANK_HOLD, and <=1e-12 is only a candidate numerical-null band. Treat that band as zero only when an independently known exact structural identity supplies the nullity (in particular D=X implies P W D=0; or the rank-six projector supplies the six null directions of D=L); otherwise preserve uncertainty as NUMERIC_RANK_HOLD rather than inventing a lower physical rank. Also verify the known-zero projected norm against the same reference. Once nonzero response is certified, apply the original B-relative retained-spectrum rule and fail closed on any unresolved rank. This is a guard for the existing separately specified B=0 case, not a new physical truncation. The three current unprojected references are 15.628950975784491, 2.8817784361013654, 15.806548843230516 and their smallest projected/global ratios are 0.17669957, 0.09004754, 0.01280879, so this guard must preserve ranks 3,3,6. '
 'Run the actual production analysis path for D=X at rho=0, finite rho and saturation/no-improvement; do not replace it by a manually empty singular-value vector. Add deterministic exact floor=tau, floor=tau+5e-10, floor=tau-5e-10 and materially above/below cases, checking coefficient budget, image budget and boundary status together. Keep the full signed witness/refit and KKT checks. Recheck only the affected cached-matrix controls and all three actual frontiers against the preserved candidate within original tolerances; no raw catalogue, sky, source reintegration, native solver, ODE, CAS relaunch, new task, attempt reset or ultra. Return the new exact candidate to this independent reviewer for targeted closeout; do not repeat the entire provenance analysis. No structured_frontier qualification or R32-08 dependency release until that closeout passes.'
)
review='''# Fresh independent H03 review

## Physics/math audit verdict

**SCOPED_HOLD** for exact manifest `{manifest}`. The three actual fixed-design numerical results independently reproduce, but the frozen acceptance also requires exact attainment and the zero-response control. Three concrete edge defects remain. No stronger physical null, calibration Jacobian, or original42 acceptance was made a condition of this review.

The reviewer did not frame or implement this candidate and did not read another review verdict. Requested runtime: gpt-6-astra/xhigh; independently observed runtime: UNKNOWN. The formal controller review packet is PENDING. No packet/ACK/completion or publication decision is created here.

## Assumptions and conventions

Window-major signed ICRS J2000 Cartesian dipoles were re-extracted from the source theta9 arrays. The 12D covariance is the marginal submatrix of the full released 36D working covariance, with all cross-window and cross-axis entries retained. Bulk response is the saved 9x3 response restricted to dipole rows. The inherited Gaussian law gives a rank-six fitted signal and six residual degrees of freedom. D_z, D_FP and D_joint are conditional finite-window sensitivity designs with one joint M=I coefficient norm, not calibration Jacobians or estimated physical errors. Their unit rate is 1 km/s/Mpc; rho is dimensionless and q is a dimensionless whitened image magnitude.

## Equation and definition audit

| Item | Status | Evidence |
|---|---|---|
| Full carrier, marginal extraction, unchanged working law | PASS | Exact source/artifact hashes and independent matrix reconstruction |
| Whitening, signal projection, fixed six-degree threshold | PASS | Symmetric eigen whitening and six-dimensional left-nullspace implementation |
| Ellipsoid support and pseudoinverse attainment | PASS | Direct derivation plus independent signed support/out-of-image witness |
| Actual trust-region crossings and nonspanning floors | PASS | Independent normal-equation roots and separate SLSQP minimum-budget solve |
| Exact floor equality in derivation | PASS | Finite rho_sat and q_min follow directly; manuscript equations are correct |
| Numerical floor boundary handling | HOLD | H03-R1 |
| Projected-zero rank handling through production path | HOLD | H03-R2 |
| Equality secondary image budget | HOLD | H03-R3 |

## Independently reproduced actual results

T0 = {T0:.16g}; tau95 = {tau:.16g}; unrestricted eta95 = {eta:.16g}. The dipole covariance minimum eigenvalue is 0.0038312674410547853. The forbidden block-diagonal substitution gives 8.925712182985656, demonstrating why full covariance must remain in use.

| Design | Rank | Floor | rho95 | q95 |
|---|---:|---:|---:|---:|
| Depth slope | 3 | 15.31600239641719 | unattainable | not applicable |
| FP composition | 3 | 6.660568527209009 | 5.750880608573573 | 1.710846265106953 |
| Joint | 6 | 2.96e-30 numerical residual | 1.5896711740651495 | 2.7479514141865926 |

All 363 exported curve points agree with a separate computation to below 8.6e-14. Both full signed coefficient/correction/refitted-signal/residual witnesses reproduce. Direct refitted T agrees with tau to below 4e-14. A dense orthogonal Cartesian rotation preserves floors/budgets to below 2.1e-14. Numerical zero floors differ by floating arithmetic and are not an immutable-source identity issue.

## Fatal blockers for this candidate's qualification

1. **H03-R1, consumer.py:92-95:** floor=tau+5e-10 returns FINITE_FLOOR_EQUALITY and rho=1 for sigma=alpha=1, even though its irreducible floor is strictly above tau. This violates CONTRACT.md:85 and its numerical-boundary clause at line93.
2. **H03-R2, consumer.py:40-54 and 171-174:** D=X has algebraically B=0. The actual Cholesky/QR projected matrix has Frobenius norm 2.29e-15 but is self-normalized into rank6; the helper returns floor22.491757346596945 instead of T0. A separate equally valid NumPy solve changes the false floor to13.972250012168807, demonstrating roundoff dependence. The current zero-design control manually bypasses this path with empty singular values. CONTRACT.md:80,93,95 require no gain and separate zero handling.
3. **H03-R3, consumer.py:110:** at exact floor=tau and T0=tau+1, the contracted finite image minimum is1 but the implementation returns None. CONTRACT.md:91 and manuscript Eq.(8) include equality.

These do not invalidate the three fixed-design numbers above. They prevent declaring the entire frozen structured_frontier acceptance complete.

## Build status and figure audit

The selected TeX source, generated table and three manifested vector figures were copied into a disposable directory under this review path. `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` succeeded in {build_seconds:.6f}s. It produced five pages. All five original candidate pages were visually inspected. No missing figures, overfull boxes, undefined references/citations or final compilation errors were found. Two underfull bibliography boxes are cosmetic. The initial missing-bbl message is resolved by the successful latexmk sequence. Table values, labels, curve data and figure captions match the numerical carrier. Figures are scalar summaries backed by full signed matrices and vectors; the candidate does not substitute a scalar for the covariance calculation.

## Claim-tier implications and safe claims

The conditional sensitivity interpretation, independent actual three-design values, and analytical ellipsoid/trust-region formulas are supported. Physical x,F,Pi,Q,G_F remain undefined. Original42 remains false. The absence of a physical response Jacobian and survey-null law is branch-local and does not itself block this conditional task. No native-solver, Bianchi-family, posterior or truth-certificate claim is made. No publication decision is authorized.

## Required tests or artifacts and bounded repair

{repair}

## Evidence read and provenance

Read the actual FRONTIER task acceptance, HANDOFF_CURRENT_SESSION, frozen framer CONTRACT, immutable H03_SOURCE_TOMOGRAPHY and physical_results inputs, candidate RESULT/RAW_RECEIPT/CONTROLLER_RETURN/manifest, consumer source, full generated carrier/analysis, table/CSV, claim map, README, TeX/PDF and figures. No prior review verdict, raw catalogue/sky, full old history, repository audit harness, native solver, ODE or CAS run was used. Only this review directory was written. The unrelated ongoing BANDPASS writer and controller state were untouched.

Evidence files: INDEPENDENT_NUMERICS.json, ADDITIONAL_PROBES.json, independent_probe.py, additional_probes.py, probe.stdout/stderr, additional.stdout/stderr, BUILD_RESULT.json, build.stdout/stderr, paper_build/main.log, candidate_pdf.txt and candidate_page-1.png through candidate_page-5.png. The original artifact hashes were verified again before finalization. Exact review wall duration was not independently measured; command timings below are observed, not requested limits.
'''.format(manifest=manifest_hash,T0=n['T0'],tau=n['tau95'],eta=n['eta95'],build_seconds=build['elapsed_seconds'],repair=repair_plan)
(o/'REVIEW.md').write_text(review)
files=['REVIEW.md','INDEPENDENT_NUMERICS.json','ADDITIONAL_PROBES.json','independent_probe.py','additional_probes.py','probe.stdout','probe.stderr','additional.stdout','additional.stderr','BUILD_RESULT.json','build.stdout','build.stderr','candidate_pdf.txt','paper_build/main.log']
paths={name:{'path':str(o/name),'exists':(o/name).is_file(),'bytes':(o/name).stat().st_size,'sha256':hashlib.sha256((o/name).read_bytes()).hexdigest()} for name in files}
raw={'schema':'H03_FRESH_INDEPENDENT_REVIEW_RAW_v1','reviewer_agent':'/root/r35_h03_fresh_independent_review','requested_model':'gpt-6-astra','requested_effort':'xhigh','observed_runtime':'UNKNOWN','candidate_identity':'sha256:'+manifest_hash,'formal_review_packet_status':'PENDING','source_code_products_state_git_writes':False,'writes_confined_to':str(o),'read_only_checkout_head_observed':'7f313d6c4f2794c484791ed108a7ce231eb824b0','branch_observed':'research/htt-adaptive-methods-20261023','remote_observed':'https://github.com/cosmosapjw-quantum/htt_base.git','commands':[{'command':'python '+str(o/'independent_probe.py'),'cwd':'/home/cosmosapjw/Dropbox/bianchi/htt_base','exit_status':0,'calculation_duration_seconds':n['elapsed_seconds'],'stdout':str(o/'probe.stdout'),'stderr':str(o/'probe.stderr')},{'command':'python '+str(o/'additional_probes.py'),'cwd':'/home/cosmosapjw/Dropbox/bianchi/htt_base','exit_status':0,'calculation_duration_seconds':ad['elapsed_seconds'],'stdout':str(o/'additional.stdout'),'stderr':str(o/'additional.stderr')},build],'first_execution_failure':None,'first_candidate_defects_preserved':findings,'review_wall_duration':'NOT_INDEPENDENTLY_MEASURED','path_validation':paths,'final_manifest_sha256':manifest_hash,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(o/'RAW_RECEIPT.json').write_text(json.dumps(raw,indent=2)+'\n')
result={'schema':'H03_FRESH_INDEPENDENT_REVIEW_RESULT_v1','task_id':'R32-03-H03-STRUCTURED','verdict':'SCOPED_HOLD','status':'HOLD','candidate_identity':'sha256:'+manifest_hash,'candidate_manifest':str(p/'ARTIFACT_MANIFEST.json'),'candidate_unchanged':True,'acceptance_met':False,'acceptance_scope':'structured_frontier only','proposed_qualified_products':[],'original42_acceptance':False,'formal_review_packet_status':'PENDING','publication_decision':'NOT_MADE','reviewer_agent':'/root/r35_h03_fresh_independent_review','requested_model':'gpt-6-astra','requested_effort':'xhigh','observed_runtime':'UNKNOWN','independence':{'framed_candidate':False,'implemented_candidate':False,'prior_verdict_read':False,'excluded_authors':['/root/rc_0a81e3b1b567331','/root/r35_h03_bandpass_contract_intake']},'issue_class':'H03_STRUCTURED_BOUNDARY_AND_PROJECTED_ZERO_NUMERICS','counterexample':findings[0]['counterexample'],'counterexamples':[f['counterexample'] for f in findings],'findings':findings,'repair_plan':repair_plan,'bounded_lower_tier_preparation_authorized':True,'repair_execution_requires_formal_current_controller_packet':True,'actual_three_design_results_independently_confirmed':True,'physical_missing_inputs_used_as_base_blocker':False,'review_report':str(o/'REVIEW.md'),'raw_receipt':str(o/'RAW_RECEIPT.json'),'validation_evidence':[str(o/x) for x in files],'next_executable_checkpoint':'Bind this exact verdict to the actual formal review packet when issued; record HOLD and route the bounded repair under the existing task/account. No R32-08 structured_frontier dependency qualification yet. Continue independent BANDPASS work.'}
(o/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'verdict':result['verdict'],'candidate_identity':result['candidate_identity'],'result':str(o/'RESULT.json'),'raw_receipt':str(o/'RAW_RECEIPT.json'),'findings':[f['id'] for f in findings]},indent=2))
