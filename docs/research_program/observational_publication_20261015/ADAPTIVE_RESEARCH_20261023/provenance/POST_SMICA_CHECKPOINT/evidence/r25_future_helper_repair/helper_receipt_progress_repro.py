"""Two controlled progress boundaries; no network/process execution."""
import importlib.util,runpy,json,tempfile,contextlib,io
from pathlib import Path
prefix=Path('docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/frequency_acquisition').resolve()
s=importlib.util.spec_from_file_location('review_helper',prefix/'cooperative_resume.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    root=Path(d);m.TARGET=root
    (root/'fixture.fits.part').write_bytes(b'abc')
    spec={'filename':'fixture.fits','band_GHz':143,'url':'https://fixture.invalid/map','advisor_head_content_length':10}
    for sequence,data in ((1,b'de'),(2,b'f')):
        binding={k:'fixture' for k in m.BINDING_FIELDS};binding['sequence']=sequence
        request=m.Request(binding,root/f'request-{sequence}.json')
        class FakeRunner:
            def __init__(self):self.request=request
            def transfer(self,command,stdout_path,stderr_path,receipt_path,is_bulk=True,on_started=None):
                self.request.before_action()
                if on_started:on_started({'pid':1,'scope':'controlled fixture only'})
                offset=int(command[command.index('--range')+1].split('-')[0])
                Path(command[command.index('--output')+1]).write_bytes(data)
                Path(command[command.index('--dump-header')+1]).write_text(f'HTTP/1.1 206 Partial Content\r\nContent-Range: bytes {offset}-9/10\r\nContent-Length: {10-offset}\r\n\r\n')
                Path(stdout_path).write_text(json.dumps({'url_effective':spec['url'],'time_total':.01,'size_download':len(data),'exitcode':28}))
                m.write_json(request.path,{'binding':binding,'action':'checkpoint'});self.request.poll()
                return {'exit_code':28}
        engine=runpy.run_path(str(prefix/'cooperative_engine.py'));g=engine['acquire'].__globals__
        g.update(TARGET=root,EXECUTING_SOURCE_SHA256=m.sha(prefix/'cooperative_engine.py'),subprocess=m.EngineProxy(FakeRunner(),root/'runtime'))
        with contextlib.redirect_stdout(io.StringIO()):result=engine['acquire'](spec,cooperative_check=request.before_action)
        receipt=m.seal(root/'fixture.fits.receipt.json')
        if sequence==1:old_receipt=receipt
    try:m.check_seal(old_receipt);old_seal_survived=True
    except ValueError:old_seal_survived=False
    result={'same_receipt_path':old_receipt['path']==receipt['path'],'old_seal_survived_next_authorized_progress':old_seal_survived,'old_hash':old_receipt['sha256'],'new_hash':receipt['sha256'],'retained_part':(root/'fixture.fits.part').read_text(),'actual_attempts_in_receipt':len(result['partial_or_failure_history']),'controller_next_checkpoint_effect':'old seal retained by helper raw_evidence/sources fails verification'}
    print(json.dumps(result,indent=2))
    Path('/mnt/extdrive/workdir/htt_open_data/r25_checkpoint_review_scratch/helper_receipt_progress_result.json').write_text(json.dumps(result,indent=2)+'\n')
