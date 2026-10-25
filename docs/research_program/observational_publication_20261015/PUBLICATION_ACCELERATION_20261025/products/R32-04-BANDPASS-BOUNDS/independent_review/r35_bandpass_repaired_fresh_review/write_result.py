from pathlib import Path
import json,hashlib,datetime,collections
O=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_repaired_fresh_review')
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_01')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'raw/independent_probe.json').read_text());m=json.loads((P/'ARTIFACT_MANIFEST.json').read_text())
assert H(P/'ARTIFACT_MANIFEST.json')=='6567e6a41858b7d549656cd078fcbcc815a04ffa804db5e0c9882bef6a7b252b'
for x in m['files']:assert H(P/x['path'])==x['sha256']
for f in ['budgets.tex','residuals.tex']:
 assert (P/'report/generated'/f).read_bytes()==(P.parent/'report/generated'/f).read_bytes()==(O/'replay/report/generated'/f).read_bytes()
witness=next(x for x in r['pure_cmb_false_empty_cases'] if x['branch']=='A_BT_1e-07' and x['metric']=='common_reference' and x['scale']==1 and x['rho']==0)
repair_plan=(
 'Same-task bounded lower-tier BP-03 repair of candidate sha256:6567e6a41858b7d549656cd078fcbcc815a04ffa804db5e0c9882bef6a7b252b under a future actual formal repair packet; preserve all earlier candidates, raw failures, task identity, cumulative costs and existing allowances. '
 'Reuse the exact retained R31 source sha256:b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f, all six 7x9 matrices, a=ones(7), both fixed metrics, signed full24 carrier, corrected Nc/Nz transport, ell/c values and unchanged rank/Fc/KKT/full24 gates. '
 'Correct only identified-set boundary evaluation, its narrow regressions, corresponding prose/result fields and required generated packaging. '
 'First exploit structural facts that are exactly decidable for this frozen finite input: with verified a=ones(7), finite Y has J0=0 exactly iff all seven rows agree entrywise as binary64 values interpreted as exact supplied reals. In that exact repeated-row case take s0 from that common row, J0=0, rho=0 gives an exact singleton, and rho>0 gives a ball of radius rho/ell without first squaring rho; never use approximate row equality to force a nonzero residual to zero. At rho=0, any exactly unequal finite rows prove the set empty for this a=ones model. This handles the nonzero pure-target counterexample and zero data algebraically without changing the model. '
 'For rho>0 with genuinely nonzero or unresolved residual, account for projection/whitening cancellation in homogeneous amplitude units. With K=L L^T, let Z=L^-1 Y, b=L^-1 a, q=b/||b||, E=(I-q q^T)Z; exact J0=||E||_F^2. If the implemented whitened residual Ehat has a justified total norm-error bound delta_E (including factorization, triangular solves and projection, with dependence on the retained matrix conditioning), then J0 lies between max(0,||Ehat||_F-delta_E)^2 and (||Ehat||_F+delta_E)^2; equivalently its squared error is at most 2||Ehat||_F delta_E+delta_E^2. Use this inequality to cover the cancellation error, together with the existing relative squared-budget tolerance1e-9 and the rounding error in rho^2. delta_E must scale linearly with ||Z||_F or an equivalent conservative whitened-data norm; the resulting squared error and decision tolerance must scale quadratically under Y,rho -> alpha Y,alpha rho. Do not restore max(1,...) or a dimensionful floor. An implementable conservative numerical-policy scale is1e-9*max(rho^2,Jhat,||Z||_F^2), provided the factor/solve/projection error is checked to be covered; this policy alone must not be advertised as a rigorous all-input interval certificate. If that coverage cannot be established or the gap/error interval overlaps zero, return an explicit NUMERIC_BOUNDARY_HOLD/BOUNDARY_UNCERTAIN with radius=None and the uncertainty/error-scale explanation, rather than EMPTY, zero-radius singleton, clipping J0, or truncating a direction. Resolve any larger factor/rank error with a typed numeric refusal; do not relax the fixed scientific gates. '
 'Retain the exact-equality singleton theorem separately from finite-precision boundary classification. Under fixed binary64 input, exact repeated rows and zero-budget row inequality are structural certificates; general computed near-equality is only a numerical uncertainty unless separately established. '
 'Add regressions for exactly repeated nonzero rows (single coordinate and mixed signed24 vector), rho=0 and tinypositive/ordinary rho, across all six branches and both metrics at amplitude scales1e-6,1,1e6; test exact unequal-row zero-budget EMPTY so the shortcut cannot erase a real residual. Add near-pure-target perturbations at positive rho on both sides of the uncertainty region, accepting typed uncertainty when precision is insufficient and comparing resolvable cases to an independent SVD or bounded high-precision solve on the same cached matrices. Preserve the existing generic EMPTY/equality/BALL, zero-data, domain-rejection, radius/center scaling and all12 null-lift tests. '
 'Re-execute only the cached consumer and affected tests/report packaging, show numerical parity of unchanged ell/c/old branch values, and return the exact new candidate plus first raw outcomes to fresh independent review. No reintegration, WMAP/row extension, sky/catalogue/noise/ODE/native run, new physical model, new ultra allocation, accounting reset, full provenance rerun or original42 promotion. Unavailable formal binding blocks admission, not preservation of this review preparation.'
)
find={
 'id':'BP-03','severity':'P1','status':'REPRODUCED_BLOCKER',
 'path':str(P/'consumer.py'),'line_start':116,'line_end':130,
 'title':'Relative-to-residual tolerance certifies false emptiness after pure-target cancellation',
 'description':'For the exact frozen a=ones input, Y[:,0]=1 and all remaining entries0, rho=0 is feasible with s=e0,U=0, and positive-definite M forces U=0 at zero budget, so the exact identified set is the singleton {e0}. The helper computes center0=1.0000000000000016 and J0=2.349281189348694e-29 from projection roundoff, then tol=1e-9*J0 and returns EMPTY. The same input with rho=1e-20 is also incorrectly EMPTY. This is a finite wrong classification with an exact witness, not a valid ambiguity or missing physical input. A homogeneous floor based only on rho squared and computed J0 cannot cover cancellation against the nonzero data norm.',
 'counterexample':witness,
 'expected':'SINGLETON_EXACT_STRUCTURAL at rho=0, or conservative BOUNDARY_UNCERTAIN pending structural recognition; never EMPTY. For exactly repeated rows and rho>0, BALL with center equal to the shared row and radius rho/ell.',
 'affected_probe_count':68,'total_pure_target_probes':72,
 'affected_branch_metric_pairs':len(set((x['branch'],x['metric']) for x in r['pure_cmb_false_empty_cases'])),
 'raw_evidence':str(O/'raw/independent_probe.json'),
 'minimal_fix':'Handle exactly pure-target data structurally for frozen a=ones, and include a homogeneous whitened-data projection-error bound for the remaining boundary decision; return typed uncertainty for unresolved nonzero residuals.'}
maxima={k:max(x['independent_checks'][k] for x in r['rows']) for k in ['G_Nz_relative','F_Nc_relative','Nc_M_Nc_error','Nc_M_c_relative','full24_null_lift_relative','ell_vs_independent_SVD_relative','c_vs_independent_SVD_relative','Fc_relative']}
result={
 'task_id':'R32-04-BANDPASS-BOUNDS','review_phase':'REPAIRED_CANDIDATE_FRESH_INDEPENDENT_PREPARATION',
 'formal_packet_binding':'NOT_YET_SELECTED','formal_admission':False,'verdict':'HOLD','outcome':'blocker','acceptance_met':False,
 'candidate_identity':r['candidate_identity'],'candidate_manifest':str(P/'ARTIFACT_MANIFEST.json'),'input_identity':r['input_identity'],
 'source_input_sha256':r['source_sha256'],'prior_candidate_identity':r['old_candidate_identity'],
 'prior_repair_plan_binding':{'path':'/mnt/extdrive/workdir/htt_open_data/r35_bandpass_fresh_independent_review/FORMAL_BINDING_RESULT.json','repair_plan_sha256':'780083816f83305686fe93538c381f8630a784cf66d5e31bebb55c279474e556'},
 'agent_id':'/root/r35_bandpass_repaired_fresh_review','requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN',
 'independence':{'implemented_candidate':False,'framed_original_contract':False,'candidate_raw_and_old_repair_findings_read':True,'project_harness_or_test_pass_used_as_verdict_oracle':False,'nested_agents':False,'repository_or_state_or_git_writes':False},
 'acceptance_scope':'bounded_moment_frontier only','qualified_products':[],'proposed_qualified_products':[],'original42_acceptance':False,'original_acceptance_met':False,'R32_09_qualified':False,
 'findings':[find],'repair_plan':repair_plan,'repair_plan_sha256':hashlib.sha256(repair_plan.encode()).hexdigest(),
 'assumptions_and_conventions':{
  'model':'Y=a s^T+F U; a=ones7; full-row-rank frozen F7x9; U9x24; no observedY',
  'coordinates':'E2,E3,B2,B3 with m0 then sqrt2Re and -sqrt2Im positive-m coordinates; frequency-major row vectorization',
  'metrics':'common fixed M=diag(d^2) from nominal A1e-7 column scales; raw sensitivity M=I9',
  'units':'Y,s,U,rho share target harmonic amplitude unit; F,d dimensionless; J0 and rho squared have amplitude-squared units',
  'claim_ceiling':'finite conditional free nine-signed-moment class; no physical foreground bound, posterior/confidence/null calibration, observed quotient tensor, tilt/family/native or original42 admission'},
 'equation_audit':{
  'minimum_norm_and_null_orthogonality':'Derived directly from Fc=a and Mc=F^T lambda; exact decomposition ell^2+n^T M n.',
  'identified_set':'Completing the square yields J0+ell^2||s-s0||^2<=rho^2; exact theorem is correct.',
  'pair_factor_two':'Triangle inequality proves necessity, s1=v/2,s2=-v/2 and opposite minimum compensators attain the bound at Y=0.',
  'boundary_implementation':'HOLD: pure-target cancellation counterexample BP-03 violates the exact theorem.',
  'nullspace_coordinate_repair':'PASS within all12 retained branch/metric cases; Nc=Nz/d, original and whitened null equations and full24 lift verified independently.'},
 'validation':{
  'manifest_sha_verified':True,'candidate_files_verified':29,'post_review_candidate_and_file_hashes_unchanged':True,
  'independent_branch_metric_pairs':12,'independent_metrics_max_errors':maxima,
  'generic_empty_equality_ball_scales':[1e-6,1,1e6],'generic_center_radius_scaling':'PASS',
  'zero_data_zero_positive_radius':'PASS for requested ordinary/scaled budgets','negative_nonfinite_overflow_budget_rejection':'PASS across all12 pairs',
  'near_nonzero_residual_boundary':'PASS on retained generic +/-1e-11 relative gap uncertainty and +/-1e-7 resolved sides',
  'exact_nonzero_pure_target_zero_budget':'FAIL BP-03','pure_target_false_empty_count':68,
  'old_core_branch_numerical_values':'exactly unchanged for six branches and both metrics',
  'old_all6_npz_arrays':'exactly unchanged','old_tables':'byte-identical; also identical to independent cached replay',
  'changed_result_fields':'106 changes/additions/removals only in corrected null coordinate/roundoff diagnostics, constructed equality labels/uncertainty, and relocated binary output paths; raw full diff preserved',
  'unmodified_cached_consumer_replay':'SUCCESS; output root relocated to reviewer ownership; exact result parity except six output paths; allNPZ arrays equal',
  'worker_targeted_test_receipt':'29PASS retained; read as execution evidence, not verdict oracle',
  'review_probe_first_attempt':'Reviewer-only harness formula error included an extra singular-value division in independent c reconstruction; raw script/stdout/stderr preserved, corrected to c=V*(U^T a/sigma)/d; second full probe succeeded and exposed BP-03.',
  'warnings':'Existing Matplotlib Axes3D import warning; two-dimensional figures generated successfully.'},
 'pdf_and_claim_review':{
  'pdf_sha256':H(P/'report/main.pdf'),'pages':6,'all_pages_visually_inspected':True,'figures':2,'generated_tables':2,
  'layout':'All equations, tables, two frontier plots and captions visible; no clipping or missing figures observed.',
  'build_evidence':'Retained latexmk execution exit0 produced six-page297463-byte PDF; initial reference warnings resolve on final compile. No reviewer rebuild needed or performed.',
  'equations_and_plot_slopes':'Consistent with rho/ell and2rho/ell; separate raw-I metric sensitivity; plotted overlaps explicitly explained.',
  'claim_language':'Free signed9-moment class, no observedY/physical moment bound/noise law/native solver; frequency is not depth; all diagnostic HOLD/NOT_MEASURED ceilings retained.',
  'required_change':'Boundary implementation explanation must match corrected error-aware classifier; exact theorem itself needs no relaxation.'},
 'raw_evidence':[str(O/'raw/independent_probe.json'),str(O/'raw/probe.stdout'),str(O/'raw/probe.stderr'),str(O/'raw/consumer_replay.stdout'),str(O/'review_probe.py')],
 'not_run':['response reintegration','new external data or literature intake','sky/catalogue/ODE/native solver','full provenance campaign','Git commands','candidate or controller-state mutation','new CAS/admission campaign'],
 'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
(O/'RESULT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
receipt={'status':'REVIEW_PREPARATION_COMPLETE','verdict':'HOLD','formal_binding':'NOT_YET_SELECTED','candidate_identity':r['candidate_identity'],'source_sha256':r['source_sha256'],'result_sha256':H(O/'RESULT.json'),'probe_source_sha256':H(O/'review_probe.py'),'probe_raw_sha256':H(O/'raw/independent_probe.json'),'commands':[{'command':'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR=<owned>/mpl python3 -B <owned>/review_probe.py','cwd':'/home/cosmosapjw/Dropbox/bianchi/htt_base','completion':'second probe completed; first reviewer-harness failure preserved','stdout':str(O/'raw/probe.stdout'),'stderr':str(O/'raw/probe.stderr')},{'command':'pdftoppm -scale-to 1500 -png <exact candidate>/report/main.pdf <owned>/raw/pdf-page','exit_code':0,'rendered_pages':6},{'command':'pdfinfo <exact candidate>/report/main.pdf','exit_code':0,'pages':6}],'all_mutations_within':str(O),'requested_runtime':result['requested_runtime'],'observed_runtime':'UNKNOWN'}
(O/'RAW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'verdict':'HOLD','finding':'BP-03','result':str(O/'RESULT.json'),'result_sha256':H(O/'RESULT.json'),'repair_plan_sha256':result['repair_plan_sha256'],'formal_binding':'NOT_YET_SELECTED'},indent=2))
