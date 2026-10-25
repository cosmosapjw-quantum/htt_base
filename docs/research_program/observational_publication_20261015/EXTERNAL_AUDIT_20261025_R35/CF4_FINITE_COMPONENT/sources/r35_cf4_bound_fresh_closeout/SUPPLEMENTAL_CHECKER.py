import io,json,hashlib,pathlib,time,traceback,sys
started=time.monotonic()
OUT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r35_cf4_bound_fresh_closeout')
BASE=pathlib.Path('/mnt/extdrive/workdir/htt_open_data')
RUN=BASE/'r30_cf4_pv_tensor_numeric/fast_window_fixture_repair/actual_run'
CORRECTED=BASE/'r35_cf4_saved_bound_repair/CORRECTED_BOUNDS.npz'
report={'scope':'Two omitted checks in the same unfinished independent closeout only','candidate_identity':'sha256:88b177047bd50170592f63f6454a957cd93c6540bcbf514d9a9a399c33d0359c','candidate_identity_basis':'controller-supplied; prior identity review reused','requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','first_command_conservative_charge_seconds':1.0,'preparation_conservative_charge_seconds':0.85,'supplemental_command_allocation_seconds':3.0,'same_closeout_allocation_seconds':5.0,'unchanged_bank_precharged_seconds':599.8927776466445,'input_reads':[],'producer_imported_or_executed':False,'new_windows_or_physical_transforms':False,'automatic_retry':False}

def check(ok,message):
    if not bool(ok):raise RuntimeError(message)

def deadline():
    if time.monotonic()-started>2.55:raise TimeoutError('Supplemental internal deadline; no retry')

try:
    import numpy as np
    initial=(OUT/'INITIAL_ASSESSMENT.json').read_bytes()
    report['initial_assessment_sha256']=hashlib.sha256(initial).hexdigest()
    intake=json.loads((OUT/'INTAKE.json').read_text())
    expected={p:d['sha256'] for p,d in intake['arrays'].items() if d.get('sha256')!='UNREAD_DUE_INTAKE_SIZE_LIMIT'}
    for f in intake['files'].values():
        if f.get('path','').endswith('/PREPARATION.json'):
            for r in f['content']['frozen_reads']:expected[r['path']]=r['sha256']
    expected[str(CORRECTED)]='93342f857b82fce28eb69b5b670f5fccac5a857652a09020698273a6bb9b6aba'
    def read_bytes(p):
        deadline()
        b=p.read_bytes(); digest=hashlib.sha256(b).hexdigest()
        check(str(p) in expected,'MISSING_FROZEN_INPUT_IDENTITY '+str(p))
        check(digest==expected[str(p)],'FROZEN_INPUT_DRIFT '+str(p))
        report['input_reads'].append({'path':str(p),'sha256':digest,'bytes':len(b)})
        return b
    def arrays(p,names):
        with np.load(io.BytesIO(read_bytes(p)),allow_pickle=False) as z:return {k:z[k] for k in names}
    z=arrays(CORRECTED,['roundoff','raw_corrected_roundoff','old_roundoff'])
    operative,raw,old=z['roundoff'],z['raw_corrected_roundoff'],z['old_roundoff']
    check(operative.shape==raw.shape==old.shape==(39282,5),'ROUNDING_ARRAY_SHAPES')
    check(all(np.all(np.isfinite(a)) and np.all(a>=0) for a in (operative,raw,old)),'ROUNDING_ARRAY_DOMAIN')
    constructed=np.nextafter(np.maximum(raw,old),np.inf)
    comparison={'elements':int(operative.size),'operative_below_raw_count':int(np.count_nonzero(operative<raw)),'operative_below_old_count':int(np.count_nonzero(operative<old)),'exact_upward_max_byte_values':bool(np.array_equal(operative.view(np.uint64),constructed.view(np.uint64))),'minimum_operative_minus_raw':float(np.min(operative-raw)),'minimum_operative_minus_old':float(np.min(operative-old)),'raw_greater_than_old_count':int(np.count_nonzero(raw>old)),'old_greater_than_raw_count':int(np.count_nonzero(old>raw))}
    check(comparison['operative_below_raw_count']==comparison['operative_below_old_count']==0 and comparison['exact_upward_max_byte_values'],'SAVED_OPERATIVE_ENCLOSURE_FAILED')
    report['saved_roundoff_check']=comparison
    inv=arrays(RUN/'TARGETS.npz',['targets','A_band0_indices','A_band1_indices','C_band0_indices','C_band1_indices'])
    target=inv['targets']
    high=arrays(RUN/'SENSITIVITY.npz',['high'])['high']
    prod=arrays(RUN/'PRODUCT.npz',['j','g','n_J2000'])
    fact=arrays(BASE/'r27_cf4_exact_calibration_factor_numeric/metadata_repair_run/actual_run/products/FACTOR.npz',['L_binary64','nonreference_row_index','difference_reference_row_index'])
    stageA=arrays(RUN/'STAGE_A.npz',['k1','k2'])
    check(target.shape==(39282,4) and high.shape==(39282,5),'TARGET_OR_WINDOW_SHAPE')
    check(np.all(np.isfinite(target)) and np.all(np.isfinite(high)),'TARGET_OR_WINDOW_DOMAIN')
    # Exact binary64 value keys, including signed zero, preserve the frozen convention.
    def key(row):return tuple(float(x).hex() for x in row)
    lookup={key(row):i for i,row in enumerate(target)}
    check(len(lookup)==len(target),'NONUNIQUE_SAVED_TARGETS')
    chosen=set(); sample_ids=[]; endpoint_ids=[]; extrema=[]
    samples=('o35_b0_k0x1.acd9661a17d9ep-7.npz','o35_b0_k0x1.b6450588a5f25p-7.npz','o35_b0_k0x1.b97353b4b2faap-7.npz')
    for name in samples:
        sample=arrays(BASE/'r30_cf4_pv_tensor_numeric/normalization_repair/actual_run/spectral'/name,['k','sample_u'])
        for direction in sample['sample_u']:
            idx=lookup[key((float(sample['k']),*direction))]
            chosen.add(idx);sample_ids.append(idx)
    for bi in (0,1):
        idx=inv[f'A_band{bi}_indices']
        check(np.array_equal(target[idx,0],np.broadcast_to(stageA[f'k{bi+1}'][:,None],idx.shape)),'SAVED_STAGE_A_K_BINDING')
        # Frozen endpoint rule: both radial endpoints, first four saved directions.
        for i in list(idx[0,:4])+list(idx[-1,:4]):
            chosen.add(int(i));endpoint_ids.append(int(i))
    L=np.abs(fact['L_binary64']); nr=fact['nonreference_row_index']; ref=fact['difference_reference_row_index']
    check(L.shape==(5,35019) and nr.shape==ref.shape==(35019,),'FACTOR_SHAPE')
    normals=prod['n_J2000']; radial_weight=prod['j']*prod['g']
    n_non=normals[nr]; n_ref=normals[ref]; j_non=radial_weight[nr,None];j_ref=radial_weight[ref,None]
    for label in ('A','C'):
        deadline()
        maps=[inv[f'{label}_band{bi}_indices'] for bi in (0,1)]
        directions=target[maps[0][0],1:]
        for ids in maps:
            check(np.array_equal(target[ids,1:].view(np.uint64),np.broadcast_to(directions,target[ids,1:].shape).view(np.uint64)),'SAVED_DIRECTION_MAP '+label)
        indices=np.unique(np.concatenate([ids.ravel() for ids in maps]))
        # Recompute only the deterministic cancellation selector from cached coefficients.
        # This does not evaluate a Fourier window, physical transform, or producer function.
        scales=np.empty((len(directions),5))
        for lo in range(0,len(directions),32):
            deadline()
            dirs=directions[lo:lo+32]
            left=np.abs(j_non*(n_non@dirs.T))
            right=np.abs(j_ref*(n_ref@dirs.T))
            scales[lo:lo+len(dirs)]=(L@(left+right)).T
        direction_lookup={key(u):i for i,u in enumerate(directions)}
        check(len(direction_lookup)==len(directions),'DUPLICATE_SAVED_DIRECTION')
        direction_indices=np.fromiter((direction_lookup[key(target[i,1:])] for i in indices),dtype=np.int64,count=len(indices))
        check(np.all(np.isfinite(scales)) and np.all(scales>=0),'SELECTOR_SCALE_DOMAIN')
        for component in range(5):
            magnitude=np.abs(high[indices,component])
            denominator=scales[direction_indices,component]
            score=np.divide(magnitude,denominator,out=np.full_like(magnitude,np.inf),where=denominator>0)
            maximum=int(indices[np.argmax(magnitude)])
            minimum=int(indices[np.argmin(score)])
            chosen.update((maximum,minimum))
            extrema.append({'stage':label,'component':component,'first_maximum_magnitude_index':maximum,'first_minimum_cancellation_ratio_index':minimum})
    # The oracle index list is read only after independently reconstructing the set.
    controls=json.loads(read_bytes(RUN/'DIRECT_CONTROLS.json'))
    checked_list=[int(row['index']) for row in controls['oracle_targets']]
    checked=set(checked_list)
    target_report={'reconstructed_count':len(chosen),'original_control_rows':len(checked_list),'original_unique_control_count':len(checked),'exact_set_equal':chosen==checked,'missing_from_original_controls':sorted(chosen-checked),'extra_original_controls':sorted(checked-chosen),'reconstructed_ids':sorted(chosen),'original_control_ids':sorted(checked),'sample_ids':sample_ids,'endpoint_ids':endpoint_ids,'extrema':extrema,'original_controls_used_only_for_final_comparison':True}
    report['independent_target_set_check']=target_report
    check(len(chosen)==len(checked)==len(checked_list)==42 and chosen==checked,'INDEPENDENT_42_TARGET_SET_MISMATCH')
    report['status']='MISSING_CHECKS_PASS_PENDING_EXTERNAL_WALL_OBSERVATION'
except BaseException as exc:
    report['status']='SCOPED_HOLD'
    report['first_failure']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    report['elapsed_before_serialization_seconds']=time.monotonic()-started
    report['reasoning_and_unobserved_host_intervals']='UNKNOWN_NOT_ZERO'
    raw=json.dumps(report,indent=2,allow_nan=False)+'\n'
    with (OUT/'SUPPLEMENTAL_RAW_OUTCOME.json').open('x') as f:f.write(raw)
    receipt={'status':report['status'],'outcome_sha256':hashlib.sha256(raw.encode()).hexdigest(),'elapsed_through_outcome_serialization_seconds':time.monotonic()-started,'external_timeout_seconds':2.85,'external_kill_grace_seconds':0.05,'whole_command_cap_seconds':3.0,'whole_command_wall_observation_required':True,'first_command_conservative_charge_seconds':1.0,'preparation_conservative_charge_seconds':0.85,'aggregate_reserved_command_seconds':4.85,'unchanged_closeout_cap_seconds':5.0,'bank_precharged_seconds':599.8927776466445,'refund':False,'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN'}
    with (OUT/'SUPPLEMENTAL_EXECUTION_RECEIPT.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({'status':report['status'],'initial_assessment_sha256':report.get('initial_assessment_sha256'),'saved_roundoff_check':report.get('saved_roundoff_check'),'independent_target_set_check':report.get('independent_target_set_check'),'first_failure':report.get('first_failure'),'receipt':receipt}),flush=True)
    if report['status']=='SCOPED_HOLD':sys.exit(1)
