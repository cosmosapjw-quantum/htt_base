import os, subprocess, json, hashlib, pathlib, datetime
root=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
p=root/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report'
out=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review')
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
expected={'RESULT.json':'ab7aa3679dbf28cb1e8e9a94e050f6b2d4fbb40037b96bcbfde5c3860e9c980f','OUTPUT_MANIFEST.json':'305d4be3be809bd2764c9e3a7328459858e509ccee5b20387ed2b811e0db2278','manuscript.pdf':'c511514110ca606b9b293d9ea6710d97956df65bca477949e0f8d6212cb76110'}
identities={k:{'sha256':sha(p/k),'expected':v,'match':sha(p/k)==v} for k,v in expected.items()}
assert all(x['match'] for x in identities.values())
manifest=json.loads((p/'OUTPUT_MANIFEST.json').read_text())
identities['outputs']=[{'path':x['path'],'match':sha(p/x['path'])==x['sha256'] and (p/x['path']).stat().st_size==x['bytes']} for x in manifest['files']]
assert all(x['match'] for x in identities['outputs'])
sources=json.loads((p/'inputs/P5_SOURCE_IDENTITIES.json').read_text())
identities['sources']=[{'path':x['path'],'sha256':sha(root/x['path']),'match':sha(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['bytes']} for x in sources['files']]
assert all(x['match'] for x in identities['sources'])
(out/'raw/identity_check.json').write_text(json.dumps(identities,indent=2)+'\n')
env=os.environ.copy();env['MPLCONFIGDIR']=str(out/'mplconfig');env['PYTHONDONTWRITEBYTECODE']='1'
records=[]
def run(label,args):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    r=subprocess.run(args,cwd=root,env=env,text=True,capture_output=True)
    (out/f'raw/{label}.stdout').write_text(r.stdout);(out/f'raw/{label}.stderr').write_text(r.stderr)
    records.append({'label':label,'argv':args,'cwd':str(root),'start_utc':start,'exit_code':r.returncode})
    (out/'raw/commands.json').write_text(json.dumps(records,indent=2)+'\n')
    assert r.returncode==0,(label,r.stderr)
run('validate_only',['python3','-B',str(p/'build_product.py'),'--validate-only'])
run('pdfinfo',['pdfinfo',str(p/'manuscript.pdf')])
run('pdf_text',['pdftotext','-layout',str(p/'manuscript.pdf'),str(out/'raw/manuscript_pdf.txt')])
run('pdf_pages',['pdftoppm','-png','-scale-to','1600',str(p/'manuscript.pdf'),str(out/'pages/page')])
print(json.dumps({'status':'PASS','candidate_identity_matches':True,'manifest_files':len(manifest['files']),'source_entries':len(sources['files']),'commands':records},indent=2))
