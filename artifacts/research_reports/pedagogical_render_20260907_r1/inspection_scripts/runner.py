from pathlib import Path
import subprocess,json,hashlib,datetime,time
RUN=Path(__file__).resolve().parent
REPO=RUN/'worktree';E=RUN/'evidence';OUT=RUN/'build'
BASE='f666b244f7061451a6941f5a57aa2d721bbfa81d'
SRC=REPO/'docs/research_reports/pedagogical_20260907'
BIB=REPO/'docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib'
PANDOC='/mnt/sn850x2t/htt_base_e2e/HTT_REPORT_A_R3_RENDER_AND_RETURN_20260907T033957Z/tools/pandoc-3.1.3/bin/pandoc'
FMT='markdown+tex_math_single_backslash+raw_tex+citations+fenced_code_blocks+pipe_tables'
def ident(b): return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
def write(n,v): (E/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def run(name,args,timeout=180,cwd=REPO,expected=0):
 p=E/(name+'.command.json');assert not p.exists(),name
 start=time.monotonic();r={'argv':[str(x) for x in args],'cwd':str(cwd),'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_seconds':timeout}
 with (E/(name+'.stdout')).open('wb') as so,(E/(name+'.stderr')).open('wb') as se:
  try:
   result=subprocess.run(args,cwd=cwd,stdout=so,stderr=se,timeout=timeout);r['exit_code']=result.returncode;r['timed_out']=False
  except subprocess.TimeoutExpired:r['exit_code']=124;r['timed_out']=True
 r['elapsed_seconds']=time.monotonic()-start;r['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p.write_text(json.dumps(r,indent=2)+'\n');print(name,r['exit_code'],round(r['elapsed_seconds'],3),flush=True)
 if expected is not None:assert r['exit_code']==expected,(name,r)
 return r['exit_code']
