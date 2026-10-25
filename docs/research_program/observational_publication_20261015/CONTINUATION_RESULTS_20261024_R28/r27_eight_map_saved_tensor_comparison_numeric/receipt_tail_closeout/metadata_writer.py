"""One additive metadata-only attempt. No numerical/scientific execution."""
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent
PLAN=Path('/mnt/extdrive/workdir/htt_open_data/r27_eight_map_receipt_tail_repair_research/REPAIR_CONTRACT.json')
PLAN_SHA='41997d7265ada25569fabdf215eeb32d252c7194d75acf19b1674f64bdb1e4e7'
PACKET='4983f915af8b447e96dd2a9b067d43f4e9a376882cb3dfef3c7241781c26bd73'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def check(p,h):
    if sha(p)!=h: raise RuntimeError('IDENTITY_DRIFT:'+str(p))
def put(name,obj):
    data=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode() if not isinstance(obj,str) else obj.encode()
    with (ROOT/name).open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
def syncdir():
    fd=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
def ref(p): return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def main():
    started=time.monotonic_ns()
    ackpath=Path(sys.argv[1]); ack=load(ackpath); desc=load(ROOT/'PREPARED_DESCRIPTOR.json')
    if ack['status']!='GO' or ack['packet_id']!=PACKET: raise RuntimeError('MISSING_ACTUAL_ACK_GO')
    if ack['repair_source_candidate_sha256']!=desc['repair_source_candidate_sha256']: raise RuntimeError('ACK_SOURCE_DRIFT')
    for n,h in desc['source_sha256'].items(): check(ROOT/n,h)
    check(PLAN,PLAN_SHA); plan=load(PLAN)
    check(OLD/'INPUT.json',plan['input_identity'].split(':',1)[1]); inp=load(OLD/'INPUT.json')
    if ack['input_sha256']!=inp['contract'].get('input_sha256',plan['input_identity'].split(':',1)[1]): raise RuntimeError('ACK_INPUT_DRIFT')
    check(inp['contract']['path'],inp['contract']['sha256']); contract=load(inp['contract']['path'])
    for n,h in inp['source_sha256'].items(): check(OLD/n,h)
    if inp['source_candidate_sha256']!=plan['original_source_candidate_identity'].split(':',1)[1]: raise RuntimeError('SOURCE_CANDIDATE_DRIFT')
    for r in inp['frozen_inputs'].values(): check(r['path'],r['sha256'])
    ev=plan['original_evidence']
    for k in ('receipt','first_failure','account_proposal','base_head'): check(ev[k]['path'],ev[k]['sha256'])
    check(plan['raw_invocation_evidence']['path'],plan['raw_invocation_evidence']['sha256'])
    originalack=load(ev['ack_path']); originalstart=load(ev['started_path'])
    check(ev['ack_path'],originalstart['ack_sha256'])
    if originalack['packet_id']!=ev['original_execute_packet'] or originalstart['packet_id']!=ev['original_execute_packet']: raise RuntimeError('ORIGINAL_PACKET_DRIFT')
    if originalstart['input_sha256']!=plan['input_identity'].split(':',1)[1] or originalstart['source_sha256']!=inp['source_sha256']: raise RuntimeError('ORIGINAL_START_DRIFT')
    products=OLD/'run/products'
    for n,h in plan['frozen_original_products'].items(): check(products/n,h)
    check(ack['latest_head']['path'],ack['latest_head']['sha256']); head=load(ack['latest_head']['path'])
    # Only a known frozen base or explicit event-indexed descendant is accepted.
    if ack['latest_head']['sha256']==ev['base_head']['sha256']: settled=[]
    else:
        ancestry=json.dumps(head,sort_keys=True)
        if ev['base_head']['sha256'] not in ancestry: raise RuntimeError('MISSING_BASE_ANCESTRY')
        if 'settled_event_ids' not in head: raise RuntimeError('AMBIGUOUS_EVENT_ACCOUNTING')
        settled=head['settled_event_ids']
    events=plan['accounting']['known_disjoint_debits']
    if len(set(settled))!=len(settled): raise RuntimeError('DUPLICATE_SETTLED_EVENT')
    newevents=[e for e in events if e['id'] not in settled]
    base=head['cumulative_charged_seconds']
    if set(base)!=set(plan['accounting']['accounts']): raise RuntimeError('ACCOUNT_SET_DRIFT')
    if max(base.values())+26.767/8>900: raise RuntimeError('ACCOUNT_HEADROOM_HOLD')
    orig=load(products/'DESCRIPTIVE_RESULT.json'); d=dict(orig)
    d['metadata_closeout']={
      'owner':'obsstat','scope':'Finite saved delivered-map coordinates; descriptive diagnostic only',
      'claim_tier':'C0','claim_status':'DIAGNOSTIC_ONLY','transfer_source':'none; no transfer-dependent or native-solver claim',
      'input_identity':plan['input_identity'],'contract':inp['contract'],
      'original_source_candidate_identity':plan['original_source_candidate_identity'],
      'source_sha256':inp['source_sha256'],'frozen_inputs':contract['frozen_inputs'],
      'input_authority':contract['input_authority'],'operator':contract['operator'],
      'smica_condition':contract['smica_condition'],'preserved_holds':plan['preserved_holds'],
      'generating_procedure':'metadata_writer.py under outer_host.py; direct stored-field copies, no numerical recomputation',
      'sky_support_status':contract['operator']['support'],'null_mock_status':'NOT_CALIBRATED',
      'original_failure':ev['first_failure'],'scientific_admission':'HOLD',
      'checker':'RESERVED_NOT_RUN'}
    if any(d[k]!=v for k,v in orig.items()): raise RuntimeError('NUMERICAL_COPY_DRIFT')
    put('DESCRIPTIVE_RESULT.json',d)
    labels=orig['coordinate_labels']; si=orig['map_ids'].index('SMICA'); fi=orig['map_ids'].index('353')
    quotes=[]
    for label in ('E2:m0','B2:m0'):
        j=labels.index(label)
        quotes.append(f"SMICA {label}: saved carrier {orig['carrier_8x24_K_CMB'][si][j]!r} K_CMB; saved 143-relative entry {orig['D143_8x24_K_CMB'][si][j]!r} K_CMB.")
    j=labels.index('B2:-sqrt2Im2')-12; fit=orig['SMICA_fit']
    quotes.append(f"SMICA 143-relative B2:-sqrt2Im2: stored target {fit['target_B_12_K_CMB'][j]!r}, E-fit prediction {fit['prediction_B_12_K_CMB'][j]!r}, target-minus-prediction {fit['residual_B_12_K_CMB'][j]!r} K_CMB. This is a coordinate mismatch of the fixed finite rule; it has no statistical null significance or physical-law interpretation.")
    for label in ('E2:m0','E2:-sqrt2Im2'):
        j=labels.index(label); quotes.append(f"353 saved carrier {label}: {orig['carrier_8x24_K_CMB'][fi][j]!r} K_CMB, on the shared unnormalized carrier scale.")
    report=(products/'REPORT.md').read_text()+ '\nAdditive metadata qualification (original report retained above)\n\n'
    report+='Owner obsstat; descriptive diagnostic only; scientific_admission HOLD. Frozen input '+plan['input_identity']+'; contract sha256:'+inp['contract']['sha256']+'; original source '+plan['original_source_candidate_identity']+'.\n\n'
    report+=contract['input_authority']+'\n\n'+contract['operator']['finite_definition']+'\n\n'+contract['operator']['support']+'\n\n'
    report+='Native NSIDE: 30/44/70=1024; 100/143/217/353/SMICA=2048. Galactic COSMO; no U flip; K_CMB. These are finite native-child pixel-centre sums, not continuum true-sky E/B recovery. Beam, transfer, noise and quadrature responses remain unmatched. '+contract['operator']['meaning']+'\n\n'
    report+='Qualified PR3 R3.00 full SMICA source/profile: '+contract['smica_condition']['profile']+'. '+contract['smica_condition']['assumption']+' '+contract['smica_condition']['benchmark']+' '+contract['smica_condition']['historical_status']+'\n\n'
    report+='\n\n'.join(quotes)+'\n\n'+contract['method']['holdout_scope']+'\n\nPreserved holds: '+'; '.join(plan['preserved_holds'])+'.\n'
    put('REPORT.md',report)
    selection={n:ref(ROOT/n if n in ('DESCRIPTIVE_RESULT.json','REPORT.md') else products/n) for n in plan['frozen_original_products']}
    candidate=hashlib.sha256(json.dumps(selection,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    put('CANDIDATE.json',{'candidate_identity':'sha256:'+candidate,'products':selection,'original_products':plan['frozen_original_products'],'input_identity':plan['input_identity'],'original_source_candidate_identity':plan['original_source_candidate_identity'],'repair_source_candidate_sha256':desc['repair_source_candidate_sha256'],'packet_id':PACKET})
    put('WRITER_RECEIPT.json',{'status':'METADATA_WRITER_COMPLETE','writer_start_monotonic_ns':started,'writer_finish_before_receipt_monotonic_ns':time.monotonic_ns(),'ack':ref(ackpath),'repair_contract':ref(PLAN),'source_sha256':desc['source_sha256'],'checked_original_start':ref(ev['started_path']),'original_ack':ref(ev['ack_path']),'all_original_numerical_fields_preserved':True,'original_product_hashes_verified':True,'unsettled_original_events':newevents,'already_settled_event_ids':settled,'latest_account_head':ack['latest_head'],'original_failure_preserved':True,'scientific_admission':'HOLD'})
    syncdir()
if __name__=='__main__': main()
