import subprocess, json, hashlib, difflib, datetime
from pathlib import Path
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review')
OLD=P/'raw/candidate_before_render_token_fix';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'RESULT.json':'018cf0d1f4ab322813da519106f3aa94a80f07e6fb1179362c7151c6c84df3db','OUTPUT_MANIFEST.json':'517850abb322271d6653552c2af5681e0f0ac2ff368c591f02e29eb12fef7f09','manuscript.pdf':'427ef5a1fc7786d4c02de70f74afc1d2b86433239c54f303938d09147ae5d0ac'}
binding={k:{'sha256':sha(P/k),'expected':v,'match':sha(P/k)==v} for k,v in expected.items()}
assert all(x['match'] for x in binding.values())
old=json.loads((OLD/'OUTPUT_MANIFEST.json').read_text());new=json.loads((P/'OUTPUT_MANIFEST.json').read_text())
bindings=[]
for x in new['files']:
    ok=sha(P/x['path'])==x['sha256'] and (P/x['path']).stat().st_size==x['bytes']
    bindings.append({'path':x['path'],'match':ok});assert ok,x
old_by={x['path']:x for x in old['files']};new_by={x['path']:x for x in new['files']}
changed=[k for k,v in old_by.items() if new_by[k]['sha256']!=v['sha256']]
numeric=[k for k in old_by if k in ('arrays.npz','joint_image.csv','generated_table.csv') or k.startswith('figures/')]
assert len(numeric)==15 and not set(numeric)&set(changed)
for name in ('RESULT.json','manuscript.tex','build_product.py'):
    if (OLD/name).exists():
        diff=''.join(difflib.unified_diff((OLD/name).read_text().splitlines(True),(P/name).read_text().splitlines(True),fromfile='old/'+name,tofile='new/'+name))
        (OUT/('raw/repaired_'+name.replace('.','_')+'.diff')).write_text(diff)
binding.update(manifest_entries=bindings,changed_old_entries=changed,additional_entries=[k for k in new_by if k not in old_by],unchanged_numerical_artifacts=numeric)
(OUT/'raw/repaired_candidate_identity.json').write_text(json.dumps(binding,indent=2)+'\n')
commands=[]
def run(name,args):
    r=subprocess.run(args,text=True,capture_output=True)
    (OUT/f'raw/{name}.stdout').write_text(r.stdout);(OUT/f'raw/{name}.stderr').write_text(r.stderr)
    commands.append({'argv':args,'exit_code':r.returncode,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    assert r.returncode==0
run('repaired_pdfinfo',['pdfinfo',str(P/'manuscript.pdf')])
run('repaired_pdftotext',['pdftotext','-layout',str(P/'manuscript.pdf'),str(OUT/'raw/repaired_manuscript_pdf.txt')])
run('repaired_pdf_pages',['pdftoppm','-png','-scale-to','1600',str(P/'manuscript.pdf'),str(OUT/'pages/repaired')])
changed_pages=[]
for n in range(1,10):
    if sha(OUT/f'pages/page-{n}.png')!=sha(OUT/f'pages/repaired-{n}.png'):changed_pages.append(n)
binding['changed_rendered_pages']=changed_pages;binding['commands']=commands
(OUT/'raw/repaired_candidate_identity.json').write_text(json.dumps(binding,indent=2)+'\n')
print(json.dumps({'status':'PASS','manifest_entries':len(bindings),'changed_old_entries':changed,'changed_rendered_pages':changed_pages,'unchanged_numerical_artifacts':len(numeric)},indent=2))
