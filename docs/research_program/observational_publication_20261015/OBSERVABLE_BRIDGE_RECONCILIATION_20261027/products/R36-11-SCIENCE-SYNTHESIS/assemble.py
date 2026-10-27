#!/usr/bin/env python3
"""Bounded source-bound P4 manuscript assembly; never runs a science consumer."""
import hashlib,json,pathlib,re,shutil,subprocess,math
HERE=pathlib.Path(__file__).resolve().parent
CONTRACT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_science_synthesis_framing/EDITOR_CONTRACT.json')
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def validate(c,p):
 for key,b in c['source_bindings'].items(): assert sha(b['path'])==b['sha256'],('source identity',key)
 for name,n in [('primary_spin_glide6',6),('all97_sensitivity',97)]:
  q=p['gram'][name];assert q['profile']['rank']==5 and q['profile']['nuisance_rank']==n
  assert len(q['joint']['full5_covariance'])==5
  assert len(q['joint']['joint_signal_nuisance_covariance'])==5
  assert len(q['joint']['joint_signal_nuisance_covariance'][0])==n
 for h in p['history_images']:assert h['rank']==5 and h['null_residual_relative']<1e-12
 assert p['response']['near_limit']=='+sigma_o' and p['response']['distant_fixed_endpoint_limit']=='-sigma_o'
c=json.loads(CONTRACT.read_text());assert sha(CONTRACT)=='a08fb04382885c4ba7f62cd213a10de6a5755e609a47ca27d982629ec0e27ebf'
p=json.load(open(c['source_bindings']['pm_result']['path']));validate(c,p)
old=pathlib.Path(c['destination']['existing_root']); dest=pathlib.Path(c['destination']['candidate_overlay_root']);(dest/'report').mkdir(parents=True,exist_ok=True);(dest/'science').mkdir(exist_ok=True)
# Retain only the companion's bounded support artifacts, not a repository copy.
for f in (old/'report').iterdir():
 if f.suffix in ['.json','.pdf'] or f.name in ['reproduce.py','build_tex.py']:shutil.copyfile(f,dest/'report'/f.name)
a=pathlib.Path(c['source_bindings']['scientific_prose']['path']).read_text()
def unit(start,end):return a.split(start+'\n\n',1)[1].split('\n## '+end,1)[0].strip()
title=unit('## Replacement title','Replacement abstract');abstract=unit('## Replacement abstract','Inserted section:')
section=unit('## Inserted section: A proper-motion endpoint and history response','Replacement physical interpretation section')
disc=unit('## Replacement physical interpretation section','Numerical appendix amendment').replace('A_PM',r'\(A_{\rm PM}\)')
# Generated numerical table, signed estimates and every information eigenvalue retained.
coefs=[]; profiles=[]; number_map={}
for name,n in [('primary_spin_glide6',6),('all97_sensitivity',97)]:
 q=p['gram'][name];v=q['joint']['selected_sample_full5_coefficients_uasyr'];ev=q['profile']['eigenvalues']; radii=[math.sqrt(p['power_frontier']['lambda80']/ev[-1]),math.sqrt(p['power_frontier']['lambda80']/ev[0])]
 coefs.append('| '+str(n)+' | '+' | '.join(f'{x:.6f}' for x in v)+' |')
 profiles.append('| '+str(n)+' | 5 | '+', '.join(f'{x:.6g}' for x in ev)+' | '+f'{radii[0]:.5f} / {radii[1]:.5f}'+' |')
 number_map[name]={'coefficients':v,'eigenvalues':ev,'radii':radii,'json_prefix':'gram.'+name,'covariances':q['joint']['full5_covariance'],'cross_covariance':q['joint']['joint_signal_nuisance_covariance']}
t1='\n\n| Nuisance dimension | $a_1$ | $a_2$ | $a_3$ | $a_4$ | $a_5$ |\n|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(coefs)+'\n\nSigned common electric-quadrupole coefficients in the basis (2), in microarcseconds per year, from the same selected sample under two nuisance profiles. The complete covariances and signal–nuisance cross covariances accompany the numerical supplement. These coefficients describe the selected optical proper-motion field under the stipulated error law; they are not calibrated matter-shear estimates.\n'
t2='\n\n| Nuisance dimension | Information rank | Five information eigenvalues | Best / worst 80-percent-power radius |\n|---:|---:|:---|:---|\n'+'\n'.join(profiles)+'\n\nInformation eigenvalues have units $(\\mu\\mathrm{as}\\,\\mathrm{yr}^{-1})^{-2}$; radii are in microarcseconds per year. Eigenvectors need not coincide between profiles.\n'
t2=t2.replace('Nuisance dimension | Information rank | Five information eigenvalues | Best / worst 80-percent-power radius','Nuisance | Rank | Information eigenvalues | Best / worst radius')
section=re.sub(r'\[Insert generated Table 1.*?\]',lambda m:t1,section,flags=re.S)
section=re.sub(r'\[Insert generated Table 2.*?\]',lambda m:t2,section,flags=re.S)
for marker,file in [('POWER_FRONTIER.pdf','pm_history_power.pdf'),('INFORMATION.pdf','pm_history_information.pdf')]:
 pat=r'\[Insert the sealed '+re.escape(marker)+r'.*?Caption: (.*?)\]';m=re.search(pat,section,re.S);assert m
 cap=m[1].replace('rho/sqrt(5)',r'$\rho/\sqrt{5}$').replace('(microarcseconds per year)^(-2)',r'$({\mu\rm as}\,{\rm yr}^{-1})^{-2}$');section=section[:m.start()]+'\n\\begin{figure}\n\\centering\n\\includegraphics[width=0.88\\linewidth]{'+file+'}\n\\caption{'+cap+'}\n\\end{figure}\n'+section[m.end():]
section=section.replace('[reference: Marcori2018, their Eq. (5.13)]',r'\cite{Marcori2018} [their Eq. (5.13)]')
# Turn draft-author plain symbol shorthands into readable math in prose only.
for plain,tex in [('A_PM',r'\(A_{\rm PM}\)'),('D_so',r'\(D_{so}\)'),('Delta t',r'\(\Delta t\)'),('L_sigma',r'\(L_\sigma\)'),('kappa=1',r'\(\kappa=1\)'),('rho=0',r'\(\rho=0\)'),('T_ref',r'\(T_{\rm ref}\)')]:
 parts=re.split(r'(\\\(.*?\\\)|\\\[.*?\\\])',section,flags=re.S)
 section=''.join(x if i%2 else x.replace(plain,tex) for i,x in enumerate(parts))
section=re.sub(r'\\\(\((?:2\.43693|0\.503015).*?\)\\\)',lambda m:m[0].replace(',',r',\allowbreak '),section)
section=section.replace('### ','### ')
appendix='The supplementary source map records the retained rank argument, response conventions and numerical inputs. The astrometric supplement retains the full five-component coefficients, covariance, signal–nuisance cross covariance, information eigenbasis, ten-coordinate history information and exact response-null arrays. The two nuisance profiles consume the same 102-dimensional normal matrix and score; no old prior is imported. All displayed astrometric values and figures are generated from these retained quantities.'
def transform(s):
 s=re.sub(r'^# .*',lambda m:'# '+title,s,count=1)
 s=re.sub(r'(## Abstract\n\n).*?(?=\n## 1\.)',lambda m:m[1]+abstract+'\n',s,flags=re.S)
 s=re.sub(r'## 7\. Physical interpretation and the next measurement\n.*?(?=## Numerical appendix)',lambda m:'## 7. A proper-motion endpoint and history response\n\n'+section+'\n\n## 8. Physical interpretation and the next measurement\n\n'+disc+'\n\n',s,flags=re.S)
 s=re.sub(r'The source rank theorem is retained from .*?companion claim map\.',lambda m:appendix,s,flags=re.S)
 s=s.replace('`NOT_CERTIFIED_BY_THIS_BOUND`','outside the certified domain')
 return s
for rel in ['science/MANUSCRIPT.md','report/manuscript_generated.md']:(dest/rel).write_text(transform((old/rel).read_text()))
for key,file in [('pm_power_figure','pm_history_power.pdf'),('pm_information_figure','pm_history_information.pdf')]:shutil.copyfile(c['source_bindings'][key]['path'],dest/'report'/file)
# Existing converter, modified only for new title and figure/section inventory.
build=(old/'report/build_tex.py').read_text().replace('body.count("\\\\begin{figure}") == 3','body.count("\\\\begin{figure}") == 5').replace('[1-7]','[1-8]').replace('Separating observer motion, bulk flow and a two-mode history by finite response design',title).replace('3 figures, equations 1–27','5 figures, equations 1–35')
build=build.replace('ending = r"""','ending = r"""\n\\begin{thebibliography}{1}\n\\bibitem{Marcori2018} O. H. Marcori, C. Pitrou, J.-P. Uzan, and T. S. Pereira, ``Direction and redshift drifts for general observers and their applications in cosmology,\'\' Phys. Rev. D \\textbf{98}, 023517 (2018), arXiv:1805.12121.\n\\end{thebibliography}')
(dest/'report/build_tex.py').write_text(build)
subprocess.run([str(pathlib.Path.cwd()/'.venv/bin/python'),str(dest/'report/build_tex.py')],check=True)
# Explicit old equation and numerical appendix preservation checks.
def equations(s):return re.findall(r'\\\[.*?\\\]',s,re.S)
for i,(x,y) in enumerate(zip(equations((old/'report/body.tex').read_text())[:27],equations((dest/'report/body.tex').read_text())[:27])):assert x==y,('old equation',i+1)
assert (old/'report/manuscript_generated.md').read_text().split('## Generated numerical appendix tables')[1]==(dest/'report/manuscript_generated.md').read_text().split('## Generated numerical appendix tables')[1]
for file in ['figure1_spectra.pdf','figure2_leverage_precision.pdf','figure3_error_bound.pdf','RESULT.json','matrices.json','spectra.json']:assert sha(old/'report'/file)==sha(dest/'report'/file)
(HERE/'NUMBER_FIGURE_MAP.json').write_text(json.dumps({'source':c['source_bindings']['pm_result'],'profiles':number_map,'figures':[c['source_bindings']['pm_power_figure'],c['source_bindings']['pm_information_figure']]},indent=2)+'\n')
(HERE/'SOURCE_CONTRACT.json').write_text(json.dumps(c,indent=2)+'\n')
print('Assembly/source identity/old equation/old appendix/source figure checks PASS')
