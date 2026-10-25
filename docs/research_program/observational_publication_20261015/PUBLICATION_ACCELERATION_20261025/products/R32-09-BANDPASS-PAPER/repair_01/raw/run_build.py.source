from pathlib import Path
import datetime,hashlib,json,subprocess,time
p=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-09-BANDPASS-PAPER/repair_01')
command=['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','report/main.tex']
assert not (p/'raw/latexmk_repair.receipt.json').exists()
start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (p/'raw/latexmk_repair.stdout').open('wb') as stdout,(p/'raw/latexmk_repair.stderr').open('wb') as stderr:
    process=subprocess.run(command,cwd=p,stdout=stdout,stderr=stderr,timeout=600)
receipt={'command':command,'cwd':str(p),'started_utc':stamp,'duration_seconds':time.monotonic()-start,'exit_code':process.returncode,'main_tex_sha256':hashlib.sha256((p/'report/main.tex').read_bytes()).hexdigest(),'references_bib_sha256':hashlib.sha256((p/'report/references.bib').read_bytes()).hexdigest(),'stdout':str(p/'raw/latexmk_repair.stdout'),'stderr':str(p/'raw/latexmk_repair.stderr')}
(p/'raw/latexmk_repair.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2));print((p/'raw/latexmk_repair.stdout').read_text()[-1800:]);print((p/'raw/latexmk_repair.stderr').read_text()[-800:]);raise SystemExit(process.returncode)
