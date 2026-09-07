from pathlib import Path
import datetime, hashlib, json, os, subprocess, time
RUN=Path(__file__).resolve().parent
REPO=RUN/'worktree'; OUT=RUN/'build'; E=RUN/'evidence'
BASE='c105c1456e2de919f0927adb12995cfeb0357f9c'
MAN=REPO/'docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md'
OLD=REPO/'docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md'
BIB=REPO/'docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib'
PANDOC=str(RUN/'tools/pandoc-3.1.3/bin/pandoc')
FMT='markdown+tex_math_single_backslash+raw_tex+citations+fenced_code_blocks+pipe_tables'
def write(name,value): (E/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def ident(raw): return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO)
def run(name,args,timeout=180,cwd=REPO,expected=0):
 assert not (E/(name+'.command.json')).exists(),name
 start=time.monotonic(); began=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (E/(name+'.stdout')).open('wb') as stdout,(E/(name+'.stderr')).open('wb') as stderr:
  try: p=subprocess.run(list(map(str,args)),cwd=cwd,stdout=stdout,stderr=stderr,timeout=timeout); rc=p.returncode; timed=False
  except subprocess.TimeoutExpired: rc=None; timed=True
 record={'name':name,'argv':list(map(str,args)),'cwd':str(cwd),'started_at':began,'elapsed_seconds':time.monotonic()-start,'timeout_seconds':timeout,'timed_out':timed,'exit_code':rc,'expected_exit':expected,'invocation':1}
 write(name+'.command.json',record); print(name,rc,round(record['elapsed_seconds'],3),flush=True)
 if expected is not None: assert rc==expected and not timed,(name,rc,expected)
 return rc
if __name__=='__main__':
 run('pandoc-release',['gh','api','repos/jgm/pandoc/releases/tags/3.1.3'])
 release=json.loads((E/'pandoc-release.stdout').read_text())
 asset=next(x for x in release['assets'] if x['name']=='pandoc-3.1.3-linux-amd64.tar.gz')
 (RUN/'tools').mkdir()
 run('pandoc-download',['curl','--fail','--location','--silent','--show-error',asset['browser_download_url'],'--output',str(RUN/'tools'/asset['name'])],timeout=180)
 run('pandoc-extract',['tar','-xzf',str(RUN/'tools'/asset['name']),'-C',str(RUN/'tools')])
 write('pandoc-acquisition.json',{'reason':'Pandoc absent in PATH and bounded known local tool locations. Prior K5 used 3.1.3 on another environment. Install official portable 3.1.3 only in this run directory; no system/environment changes.','source_url':asset['browser_download_url'],'release_tag':release['tag_name'],'archive':ident((RUN/'tools'/asset['name']).read_bytes()),'binary':ident(Path(PANDOC).read_bytes())})
 for label,cmd in [('pandoc',[PANDOC,'--version']),('latexmk',['latexmk','-v']),('xelatex',['xelatex','--version']),('pdfinfo',['pdfinfo','-v']),('pdftoppm',['pdftoppm','-v']),('python',['python3','--version'])]:run('version-'+label,cmd)
