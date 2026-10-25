"""Single bounded metadata host; final external tool settlement belongs to root."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):
    with (R/n).open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def syncall():
    for p in R.iterdir():
        if p.is_file():
            with p.open('rb') as f:os.fsync(f.fileno())
    fd=os.open(R,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
def main():
    if len(sys.argv)!=3 or sys.argv[1]!='--ack':raise RuntimeError('REQUIRE_ROOT_ACK_PATH')
    start=time.monotonic_ns();utc_start=time.time_ns();p=None
    put('STARTED.json',{'status':'ONE_REPAIR_ATTEMPT_STARTED','host_pid':os.getpid(),'start_monotonic_ns':start,'start_epoch_ns':utc_start,'ack_path':sys.argv[2],'ack_sha256':sha(sys.argv[2]),'cap_seconds':10,'cleanup_reserve_seconds':2})
    try:
        with (R/'writer.stdout').open('xb') as out,(R/'writer.stderr').open('xb') as err:
            p=subprocess.Popen([sys.executable,'-B',str(R/'metadata_writer.py'),sys.argv[2]],stdout=out,stderr=err,start_new_session=True)
            try:rc=p.wait(timeout=max(.001,8-(time.monotonic_ns()-start)/1e9))
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);p.wait();raise RuntimeError('REPAIR_WORK_PHASE_CAP')
            out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
        if rc:raise RuntimeError('METADATA_WRITER_FAILED:'+str(rc))
        try:os.killpg(p.pid,0)
        except ProcessLookupError:pass
        else:raise RuntimeError('OWNED_GROUP_NOT_EMPTY')
        candidate=json.loads((R/'CANDIDATE.json').read_text())
        writer=json.loads((R/'WRITER_RECEIPT.json').read_text())
        put('RESULT.json',{'schema':'htt.native_agent_result/1','task_id':'R27-EIGHT-MAP-SAVED-TENSOR-COMPARISON','packet_id':candidate['packet_id'],'agent_id':'/root/r27_eight_map_metadata_closeout_code','input_identity':candidate['input_identity'],'candidate_identity':candidate['candidate_identity'],'original_source_candidate_identity':candidate['original_source_candidate_identity'],'repair_source_candidate_sha256':candidate['repair_source_candidate_sha256'],'outcome':'success','status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','raw_receipt':str(R/'RAW_RECEIPT.json'),'requested_runtime':{'model':'gpt-6.1-sol','reasoning_effort':'medium'},'observed_runtime':'UNKNOWN','validation_evidence':[str(R/'WRITER_RECEIPT.json'),str(R/'CANDIDATE.json')],'qualified_products':[dict({'name':n},**v) for n,v in candidate['products'].items()],'latest_account_head':writer['latest_account_head'],'account_settlement':'PENDING_ROOT_AUTHENTIC_EXTERNAL_WHOLE_CALL_MAX_SETTLEMENT','scientific_admission':'HOLD','checker':'RESERVED_NOT_RUN','preserved_first_failure':str(R.parent/'run/FIRST_FAILURE.json')})
        syncall();finish=time.monotonic_ns();elapsed=(finish-start)/1e9
        if elapsed>8:raise RuntimeError('REPAIR_FINALIZATION_RESERVE_EXHAUSTED')
        # This observation encloses child, reap, products and directory fsync.
        # Its own receipt/exit tail is externally observed, with no fabricated exact tail.
        put('RAW_RECEIPT.json',{'status':'EXECUTED_PENDING_INDEPENDENT_REVIEW','host_pid':os.getpid(),'writer_pid':p.pid,'writer_returncode':rc,'child_reaped':True,'owned_group_empty':True,'host_start_monotonic_ns':start,'post_owned_fsync_reap_monotonic_ns':finish,'measured_monotonic_seconds':elapsed,'start_epoch_ns':utc_start,'finish_epoch_ns':time.time_ns(),'receipt_exit_tail':'PENDING_EXTERNAL_WHOLE_CALL_OBSERVATION_ROOT_SETTLEMENT','clock':'time.monotonic_ns; external provider/caller clocks recorded separately','repair_cap_seconds':10,'cleanup_reserve_seconds':2,'scientific_admission':'HOLD','checker':'RESERVED_NOT_RUN'})
        syncall()
        terminal=time.monotonic_ns()
        print(json.dumps({'raw_receipt':str(R/'RAW_RECEIPT.json'),'candidate':str(R/'CANDIDATE.json'),'host_monotonic_through_receipt_fsync_seconds':(terminal-start)/1e9,'external_settlement':'ROOT_MUST_CHARGE_MAX_ONCE_AFTER_AUTHENTIC_TOOL_RETURN'}),flush=True)
        if (terminal-start)/1e9>10:raise RuntimeError('REPAIR_HARD_CAP_BREACH')
    except BaseException as e:
        if p is not None and p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
        put('FIRST_FAILURE.json',{'status':'HOLD_FIRST_REPAIR_FAILURE','exception':repr(e),'elapsed_monotonic_seconds':(time.monotonic_ns()-start)/1e9,'scientific_admission':'HOLD','second_attempt':'FORBIDDEN'})
        syncall();raise
if __name__=='__main__':main()
