"""Independent cached-evidence and disposable-document review; no source producers."""
import copy, hashlib, importlib.util, itertools, json, math, os, pathlib, re, shutil, subprocess, sys
from fractions import Fraction as F
import numpy as np

R=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
E=pathlib.Path(__file__).resolve().parent
P=R/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/optical_manuscript_candidate'
C=P/'candidate'
CP=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_manuscript_framing/EDITOR_CONTRACT.json')
c=json.loads(CP.read_text()); p=pathlib.Path(c['publication_plan']['root']); sr=p/c['publication_plan']['new_directory']
raw=E/'raw'; raw.mkdir(exist_ok=True)
commands=[]
def sha(f): return hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
def dump(f,j): f.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def run(name,args,expect=0):
    args=list(map(str,args)); q=subprocess.run(args,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    (raw/(name+'.stdout')).write_bytes(q.stdout);(raw/(name+'.stderr')).write_bytes(q.stderr)
    commands.append({'name':name,'argv':args,'exit_code':q.returncode,'expected_exit_code':expect})
    dump(E/'COMMANDS.json',commands)
    assert q.returncode==expect,(name,q.returncode,q.stderr[-1500:])
    return q.stdout
def ptr(d,where):
    for k in where.strip('/').split('/'): d=d[int(k)] if isinstance(d,list) else d[k]
    return d
def binding(b):
    q=pathlib.Path(b['path']);return q if q.is_absolute() else R/q

assert sha(CP)=='54362612409de22c86aebff678df11da462dc4fc38042deb382fa0582e55a22c'
assert sha(P/'RETURN.json')=='b12a34a6694e34b92f68f0946047caf41ab448796f10720585c4470ebd01ea5b'
assert sha(P/'PACKAGE_RECEIPT.json')=='882d3a24cb89d7cdf2fdfb7571ba41203f6f685049711a2393b2ae555f90db8e'
digest=sha(C/'OVERLAY_MANIFEST.json');assert digest=='53c00f723ea81cb88f2a63656444a0054470c422180a517b8ecf403d5373bcaa'
sealed=[]
for key,b in c['source_bindings'].items():
    f=binding(b); assert sha(f)==b['sha256'],key;assert f.stat().st_size==b['bytes'],key
    sealed.append({'key':key,'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size})
for b in json.loads((P/'PACKAGE_RECEIPT.json').read_text())['files']:
    f=P/b['path'];assert sha(f)==b['sha256'],str(f);assert f.stat().st_size==b['bytes']
manifest=json.loads((C/'OVERLAY_MANIFEST.json').read_text())
for b in manifest['files']:
    f=C/b['path'];assert sha(f)==b['postimage_sha256'];assert f.stat().st_size==b['bytes']
    sealed.append({'key':'candidate','path':str(f),'sha256':sha(f),'bytes':f.stat().st_size})
dump(E/'SOURCE_SEALS_INITIAL.json',sealed)
formal=json.loads(binding(c['source_bindings']['04_formal_return']).read_text())
assert all(formal.get(k)==v for k,v in c['qualification_gate']['required_exact_fields'].items())
pf=json.loads(binding(c['source_bindings']['p6_formal_return']).read_text())
assert pf['outcome']=='success' and pf['verdict']=='SCOPED_PASS' and pf['acceptance_met'] is True
assert pf['qualified_products']==['optical_inverse_note'] and pf['candidate_identity']==c['qualified_p6']['candidate_identity']
old=json.loads(binding(c['source_bindings']['p6_result']).read_text())['manifest']
assert hashlib.sha256(json.dumps(old,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==c['historical_manifest_resolution']['canonical_manifest_sha256']
for b in old['sources']: assert sha(R/b['path'])==b['sha256']
for b in old['outputs']: assert sha(R/p/'repair_01'/b['path'])==b['sha256']
original=binding(c['source_bindings']['p6_main']).read_bytes(); installed=(C/p/c['publication_plan']['main']).read_bytes()
anchor=c['publication_plan']['insertion_anchor'].encode(); replacement=c['publication_plan']['replacement'].encode()
assert installed.replace(replacement,anchor)==original
assert re.findall(rb'\\tag\{([^}]+)\}',original)==[str(i).encode() for i in range(1,36)]

d=json.loads((C/sr/'NUMERICAL_SUPPLEMENT.json').read_text());source=json.loads(binding(c['source_bindings']['04_result']).read_text())
for key in c['full_precision_supplement']['copy_subtrees']: assert d[key]==source[key]
B2=np.array(d['B2']);B3=np.array(d['B3']);S=np.array(d['tensor_S']);k=5/np.log(10)
assert B2.shape==(5,3,3) and B3.shape==(7,3,3,3)
assert np.allclose(B2.reshape(5,-1)@B2.reshape(5,-1).T,np.eye(5),rtol=0,atol=3e-15)
assert np.allclose(B3.reshape(7,-1)@B3.reshape(7,-1).T,np.eye(7),rtol=0,atol=3e-15)
for perm in itertools.permutations((1,2,3)): assert np.allclose(B3,B3.transpose((0,)+perm),rtol=0,atol=2e-15)
assert np.max(np.abs(np.einsum('aiik->ak',B3)))<2e-15
# Build the symmetrized, trace-subtracted Cartesian response independently.
unit=np.eye(3);tensor=[]
for e in unit:
    T=(np.einsum('i,jk->ijk',e,S)+np.einsum('j,ik->ijk',e,S)+np.einsum('k,ij->ijk',e,S))/3
    trace=np.einsum('iik->k',T)
    T-=(np.einsum('ij,k->ijk',unit,trace)+np.einsum('ik,j->ijk',unit,trace)+np.einsum('jk,i->ijk',unit,trace))/5
    tensor.append(T)
L=np.einsum('aijk,bijk->ab',B3,np.array(tensor)); Lsimple=np.einsum('aijk,jk->ai',B3,S)
assert np.allclose(L,Lsimple,rtol=1e-13,atol=1e-17)
assert np.allclose(Lsimple,d['L_S_7x3'],rtol=1e-13,atol=1e-17)
gram=L.T@L; theory=np.sum(S*S)*unit/3+2*S@S/5
assert np.allclose(gram,theory,rtol=2e-13,atol=1e-18)
assert np.all(np.linalg.eigvalsh(gram)>0)
C10=np.array(d['synthetic_source_design']['summary_covariance']);Cr=np.array(d['synthetic_source_design']['residual_covariance']);J=np.array(d['synthetic_source_design']['jacobian_d_S'])
assert C10.shape==(10,10) and Cr.shape==(7,7) and J.shape==(10,8)
assert np.allclose(C10,C10.T,rtol=0,atol=1e-22) and min(np.linalg.eigvalsh(C10))>0
A=np.column_stack((-k*Lsimple,np.eye(7)));calc=A@C10@A.T
assert np.allclose(calc,Cr,rtol=1e-12,atol=1e-22)
zero_cross=C10.copy();zero_cross[:3,3:]=0;zero_cross[3:,:3]=0
cross_impact=float(np.max(np.abs(A@zero_cross@A.T-Cr)));assert cross_impact>1e-16
assert d['coordinate_order']==['fitted d_x','fitted d_y','fitted d_z']+['O_'+str(i) for i in range(1,8)]
assert d['coordinate_units']==['dimensionless']*3+['mag']*7
assert len(d['synthetic_source_design']['full_signed_summary'])==10
checks=[]
for case in c['certificate_cases']:
    v=ptr(d,case['locator'])
    for key,val in case['expected_table'].items():assert v.get(key)==val
    if not v['physical_set_empty']:
        lo,hi,b=v['certified_lower_bound'],v['certified_upper_bound'],v['budget']; assert 0<=lo<=hi
        if b>0: assert F(v['score'])*F(b)>=F(hi)
        else: assert v['score'] is None
        # All printed accepted cases are strict upper-bound <= B, so the table
        # requires no unprinted cancellation allowance to support its label.
        assert (hi<=b) if v['compatible'] else (lo>b)
        assert v['profile_certificate']['witness']==v['profiled_d']
    checks.append({'case':case['label'],'endpoints_and_score':'PASS'})
fixed=d['exact_set_and_directed_certificate_controls']['NCF2_sqrt3_fixed_objective']
assert F(fixed['certified_lower_bound'])**2<=3<=F(fixed['certified_upper_bound'])**2
r=F(0.125);center=F(math.nextafter(.25,-math.inf));w=F(d['available_witness_controls']['EPF1_nonzero_response']['profiled_d'][0])
assert w*w<=r*r and (w-center)**2<=r*r
assert F(math.nextafter(.25,math.inf))**2>(2*r)**2
assert F(.125)**2+F(1e-60)**2>r*r
for v in d['reviewed_numeric_repair_controls'].values():
    if isinstance(v,dict) and v.get('budget')==0:
        assert v['compatible'] is False and v['residual_norm']>0 and v['score'] is None
maths={'source_bindings':len(c['source_bindings']),'overlay_files':len(manifest['files']),'formal_source_eligibility':'PASS','P6_formal_eligibility':'PASS','old_manifest_all_paths':'PASS','original35_equations_and_bytes':'PASS','STF_basis_orthonormal_symmetry_traces':'PASS','explicit_STF_response_and_Gram':'PASS','gram_max_absolute_error':float(np.max(abs(gram-theory))),'singular_values':np.linalg.svd(L,compute_uv=False).tolist(),'covariance_parity_max_abs_mag2':float(np.max(abs(calc-Cr))),'cross_block_norm':float(np.linalg.norm(C10[:3,3:])),'zeroing_cross_blocks_max_effect_mag2':cross_impact,'residual_covariance_trace_mag2':float(np.trace(Cr)),'certificate_controls':checks,'exact_binary64_geometry_and_directed_sqrt3':'PASS','B0_and_tiny_residual_semantics':'PASS'}
dump(E/'INDEPENDENT_CACHED_CHECKS.json',maths)

# Run the installed document consumer from a small external fixture only.
H=E/'publication_overlay.py'; shutil.copyfile(P/'publication_overlay.py',H)
shutil.copyfile(P/'MANUSCRIPT_ADDITIONS.md',E/'MANUSCRIPT_ADDITIONS.md')
fixture=E/'small_manuscript_fixture';assert not fixture.exists();fixture.mkdir()
(fixture/'.P6_DISPOSABLE_FIXTURE').write_text('Independent review fixture; no scientific admission.\n')
rels=[b['path'] for b in c['source_bindings'].values() if not pathlib.Path(b['path']).is_absolute()]
rels += [b['path'] for b in old['sources']]+[str(p/'repair_01'/b['path']) for b in old['outputs']]
prior=json.loads(binding(c['source_bindings']['prior_three_document_manifest']).read_text());rels += [b['path'] for b in prior['files']]
for folder in ['generated','figures']:
    rels += [str(f.relative_to(R)) for f in (R/p/'repair_01/report'/folder).rglob('*') if f.is_file()]
for rel in set(rels):
    target=fixture/rel;target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(R/rel)
fr=E/'FIXTURE_ONLY_RETURN.json';dump(fr,{'candidate_identity':'sha256:'+digest,'outcome':'success','acceptance_met':True,'review_status':'PASS_SCOPED_CONDITIONAL','agent_id':'INDEPENDENT_REVIEW_FIXTURE_PROTOCOL_TEST_ONLY','fixture_only':True,'fixture_root':str(fixture)})
py=R/'.venv/bin/python'
apply=[py,'-B',H,'apply','--manifest',C/'OVERLAY_MANIFEST.json','--repo',fixture,'--reviewed-manifest-sha256',digest,'--review-return',fr]
first=json.loads(run('01_apply',apply));assert first['changed_targets']==20
helper=fixture/sr/'publication_overlay.py';args=['--contract',fixture/sr/'EDITOR_CONTRACT.json','--repo',fixture,'--output-root',fixture]
run('02_installed_assemble',[py,'-B',helper,'assemble',*args])
run('03_installed_check_falsifiers',[py,'-B',helper,'check',*args,'--falsifiers'])
build=['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','-outdir=r36_optical/build',fixture/p/c['publication_plan']['main']]
run('04_build',build);pdf=fixture/p/c['publication_plan']['pdf'];shutil.copyfile(fixture/sr/'build/main.pdf',pdf)
run('05_installed_built_check',[py,'-B',helper,'check',*args,'--built-pdfs'])
txt=run('06_fixture_pdf_text',['pdftotext','-layout',pdf,'-']);candidate_text=run('07_candidate_pdf_text',['pdftotext','-layout',C/p/c['publication_plan']['pdf'],'-']);assert txt==candidate_text
again=json.loads(run('08_idempotent_apply',apply));assert again['changed_targets']==0
run('09_metadata_rebuild',[build[0],'-g',*build[1:]]);shutil.copyfile(fixture/sr/'build/main.pdf',pdf)
assert sha(pdf)!=sha(C/p/c['publication_plan']['pdf'])
run('10_metadata_check',[py,'-B',helper,'check',*args,'--built-pdfs'])
last=json.loads(run('11_metadata_idempotent_apply',apply));assert last['changed_targets']==0
assert run('12_metadata_pdf_text',['pdftotext','-layout',pdf,'-'])==candidate_text
dump(E/'FIXTURE_RESULT.json',{'first_apply':first,'installed_assemble_check_build_check':'PASS','PDF_text_parity':'PASS','second_apply':again,'metadata_only_rebuild_pdf_sha256':sha(pdf),'metadata_rebuild_byte_identity_differs':True,'metadata_text_parity':'PASS','metadata_reapply':last,'fixture':str(fixture)})

# Independent source-conclusion falsifiers through the actual installed checker.
supp=fixture/sr/'NUMERICAL_SUPPLEMENT.json';saved=supp.read_bytes()
for name,mutate in [('drop_O7',lambda b:b['synthetic_source_design']['full_signed_summary'].pop()),('swap_signed_O1_O2',lambda b:b['synthetic_source_design']['full_signed_summary'].__setitem__(slice(3,5),b['synthetic_source_design']['full_signed_summary'][3:5][::-1])),('zero_full_cross_block',lambda b:[b['synthetic_source_design']['summary_covariance'][i].__setitem__(j,0.0) for i in range(10) for j in range(10) if (i<3)!=(j<3)]),('change_basis_sign',lambda b:b['B3'].__setitem__(0,(-np.array(b['B3'][0])).tolist()))]:
    bad=json.loads(saved);mutate(bad);dump(supp,bad)
    run('negative_'+name,[py,'-B',helper,'check',*args],expect=1);supp.write_bytes(saved)
tex=fixture/p/c['publication_plan']['main'];savedtex=tex.read_bytes();tex.write_bytes(savedtex+b'\n% unreviewed edit\n')
run('negative_unreviewed_installed_tex',[py,'-B',helper,'check',*args],expect=1);tex.write_bytes(savedtex)
run('13_restored_fixture_check',[py,'-B',helper,'check',*args,'--built-pdfs'])
for b in sealed: assert sha(b['path'])==b['sha256'],b['path']
dump(E/'SOURCE_SEALS_FINAL.json',sealed)
print(json.dumps({'status':'PASS','maths':maths,'fixture':json.loads((E/'FIXTURE_RESULT.json').read_text()),'commands':len(commands)},indent=2))
