#!/usr/bin/env python3
"""Source/number/covariance/figure regressions and in-memory negative controls."""
import pathlib,json,hashlib,copy,re
H=pathlib.Path(__file__).resolve().parent
C=json.loads((H/'SOURCE_CONTRACT.json').read_text());D=pathlib.Path(C['destination']['candidate_overlay_root'])
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
P=json.load(open(C['source_bindings']['pm_result']['path'])); M=json.loads((H/'NUMBER_FIGURE_MAP.json').read_text()); S=(D/'science/MANUSCRIPT.md').read_text()
def check(c,m,s,figure_hashes):
 for k,b in c['source_bindings'].items():assert sha(b['path'])==b['sha256'],('source',k)
 for key,n in [('primary_spin_glide6',6),('all97_sensitivity',97)]:
  q=P['gram'][key];v=m['profiles'][key]
  assert q['profile']['rank']==5 and q['profile']['nuisance_rank']==n
  assert v['coefficients']==q['joint']['selected_sample_full5_coefficients_uasyr']
  assert v['eigenvalues']==q['profile']['eigenvalues']
  assert v['covariances']==q['joint']['full5_covariance']
  assert v['cross_covariance']==q['joint']['joint_signal_nuisance_covariance']
  assert len(v['cross_covariance'])==5 and all(len(row)==n for row in v['cross_covariance'])
  line='| '+str(n)+' | '+' | '.join(f'{x:.6f}' for x in v['coefficients'])+' |';assert line in s
 for key,file in [('pm_power_figure','pm_history_power.pdf'),('pm_information_figure','pm_history_information.pdf')]:assert figure_hashes[file]==c['source_bindings'][key]['sha256']
 assert set(re.findall(r'\\tag\{(\d+)\}',s))==set(map(str,range(1,36)))
 for h in P['history_images']:assert h['rank']==5 and h['null_residual_relative']<1e-12
 assert len(re.findall(r'\\includegraphics', (D/'report/main.tex').read_text()))==5
 assert not re.search(r'undefined|Overfull|^!',(D/'report/main.log').read_text(),re.M)
fig={f:sha(D/'report'/f) for f in ['pm_history_power.pdf','pm_history_information.pdf']}
check(C,M,S,fig); results=['positive candidate: PASS']
def negative(name,c=C,m=M,s=S,f=fig):
 try:check(c,m,s,f)
 except AssertionError:results.append(name+': rejected as required')
 else:raise AssertionError('negative control not caught: '+name)
x=copy.deepcopy(M);x['profiles']['primary_spin_glide6'],x['profiles']['all97_sensitivity']=x['profiles']['all97_sensitivity'],x['profiles']['primary_spin_glide6'];negative('transposed profiles',m=x)
x=copy.deepcopy(M);x['profiles']['primary_spin_glide6']['coefficients'][0]*=-1;negative('lost coefficient sign',m=x)
x=copy.deepcopy(M);x['profiles']['primary_spin_glide6']['cross_covariance'][0].pop();negative('changed nuisance dimension',m=x)
x=copy.deepcopy(M);x['profiles']['primary_spin_glide6']['cross_covariance']=[];negative('dropped cross covariance',m=x)
x=dict(fig);x['pm_history_power.pdf']='0'*64;negative('changed figure hash',f=x)
x=copy.deepcopy(C);x['source_bindings']['pm_result']['sha256']='0'*64;negative('wrong immutable source identity',c=x)
negative('wrong displayed coefficient',s=S.replace('-2.262422','2.262422'))
print('\n'.join(results));(H/'CHECKS.json').write_text(json.dumps({'checks':results,'scope':'retained-product assertions and assembly regressions; not independent science verification'},indent=2)+'\n')
