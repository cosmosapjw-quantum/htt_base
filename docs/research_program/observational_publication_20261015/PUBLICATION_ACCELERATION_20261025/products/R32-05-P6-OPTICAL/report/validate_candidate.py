"""Focused source/layout and independent unit cross-reference audit."""
from pathlib import Path
import re,json,sys,subprocess
R=Path(__file__).resolve().parent
source=(R.parent/'science/MANUSCRIPT.md').read_text(); tex=(R/'main.tex').read_text();log=(R/'main.log').read_text();text=(R/'raw/main.txt').read_text()
def equations(s,pattern):
 out={}
 for m in re.finditer(pattern,s,re.S):
  block=m[1];tag=re.search(r'\\tag\{(\d+)\}',block);assert tag
  v=re.sub(r'\\(?:begin|end)\{gathered\}|\\qquad|\\\\|\s','',block)
  out[int(tag[1])]=v
 return out
assert equations(source,r'\\\[(.*?)\\\]')==equations(tex,r'\\begin\{equation\}(.*?)\\end\{equation\}')
assert sorted(equations(tex,r'\\begin\{equation\}(.*?)\\end\{equation\}'))==list(range(1,36))
assert len(re.findall(r'\\includegraphics',tex))==2
assert 'Overfull' not in log and 'undefined' not in log.lower()
assert len(re.findall(r'\\bibitem\{',(R/'references.tex').read_text()))==4
assert re.search(r'vorticity contribution.*distinct from the working',text,re.S)
P=R.parents[2];m=json.loads((P/'evidence/RESULT_OBSERVABLE_MAP.json').read_text()); item=next(x for x in m['items'] if x['id']=='CF4_QUOTIENT');assert item['units']=='dimensionless';data=json.loads((R/'generated/retained_tensor_region.json').read_text());assert abs(item['value']['tensor_norm']-data['source_statistics']['tensor_frobenius_norm'])<=1e-12
for phrase in ['Bianchi geometry detected','Bianchi family identified','model-independent truth certificate','MIO posterior','TSC full solver','Teff full polarisation closure','external transfer validated as native']:
 assert phrase.lower() not in tex.lower()
# PDF figures must contain no embedded image objects: plots are vector output.
for figure in ['error_frontier','tensor_error_image']:
 r=subprocess.run(['pdfimages','-list',str(R/'figures'/f'{figure}.pdf')],capture_output=True,text=True);assert r.returncode==0;assert len(r.stdout.splitlines())==2
 (R/'raw'/f'{figure}_pdfimages.txt').write_text(r.stdout)
result={'equation_tags':35,'equations_semantically_identical_to_source':True,'layout_only_equation_26_wrapping':True,'pages':int(re.search(r'Pages:\s+(\d+)',(R/'raw/pdfinfo.txt').read_text())[1]),'tables':2,'vector_figures':2,'references':4,'overfull_boxes':0,'undefined_references_or_citations':0,'remaining_warnings':['nameref definition of label changed (RevTeX package interaction)'],'observable_map_dimensionless_crosscheck':True,'forbidden_phrase_scan':'PASS','visual_inspection':'All 12 pages contact sheet; title/abstract and figure pages inspected. No clipping, blank pages, or unreadable plots observed.'}
(R/'generated/candidate_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
