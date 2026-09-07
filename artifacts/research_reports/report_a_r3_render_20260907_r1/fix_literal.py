from runner import *
import difflib
p=OUT/'structure-r3.lua'; before=p.read_text(); (E/'structure-r3-initial.lua').write_text(before)
needle='function Code(code)\n'
replacement='''function Code(code)
  -- Page 10 review found an inserted line-end hyphen inside this literal.
  if code.text == "RATIO_UNIDENTIFIED" then
    return pandoc.RawInline("latex", "\\\\mbox{\\\\texttt{RATIO\\\\_UNIDENTIFIED}}")
  end
'''
assert before.count(needle)==1
p.write_text(before.replace(needle,replacement))
(E/'literal-layout-repair.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='structure-r3-initial.lua',tofile='structure-r3.lua')))
write('layout-corrections.json',{'source_transcription_changes':0,'initial_adapter_adjustments':['Preserve natural appendix subheadings and strip manual B.1/D.1 prefixes','Unique unnumbered References heading','Retain revision/status subtitle','Omit unconditional legacy T1 encoding under Unicode XeLaTeX','Load mathtools before unicode-math using exact generated-preamble replacement','Long paths/hashes use literal xurl wrapping; ragged-right headings'],'observed_correction':{'page':10,'finding':'RATIO_UNIDENTIFIED broke as RA- / TIO_UNIDENTIFIED with a discretionary hyphen in monospaced text.','repair':'Keep this one source literal together with mbox/texttt in run-local Lua adapter.','scientific_or_bibliography_source_changed':False}})
run('pandoc-render-final',[PANDOC,MAN,'--from='+FMT,'--to=latex','--standalone','--number-sections','--top-level-division=section','--lua-filter='+str(p),'--citeproc','--bibliography='+str(BIB),'--metadata-file='+str(OUT/'metadata.yaml'),'--include-in-header='+str(OUT/'header-r3.tex'),'--wrap=preserve','--log='+str(E/'pandoc-final.json'),'--output='+str(OUT/'HTT_REPORT_A_R3.tex')])
p=OUT/'HTT_REPORT_A_R3.tex'; s=p.read_text(); assert s.count(r'\usepackage{amsmath,amssymb}')==1;p.write_text(s.replace(r'\usepackage{amsmath,amssymb}',r'\usepackage{amsmath,amssymb,mathtools}',1))
run('latexmk-final',['latexmk','-xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-outdir='+str(OUT),str(p)],timeout=240,cwd=OUT)
run('parse-generated-tex-final',[PANDOC,p,'--from=latex','--to=json','--output='+str(E/'tex-final.ast.json')])
run('pdfinfo-final',['pdfinfo',OUT/'HTT_REPORT_A_R3.pdf'])
run('pdftotext-final',['pdftotext','-layout',OUT/'HTT_REPORT_A_R3.pdf',E/'pdf-final-text.txt'])
(RUN/'pages-final').mkdir()
run('raster-final-pages',['pdftoppm','-r','120','-png',OUT/'HTT_REPORT_A_R3.pdf',RUN/'pages-final/page'],timeout=240)
from PIL import Image
results=[]
for file in sorted((RUN/'pages-final').glob('*.png')):
 with Image.open(file) as im:im.verify()
 prior=RUN/'pages'/file.name
 with Image.open(file) as im,Image.open(prior) as old: equal=im.size==old.size and im.tobytes()==old.tobytes()
 results.append({'page':int(file.stem.split('-')[-1]),'image':ident(file.read_bytes()),'pixels_equal_to_initial':equal})
write('final-page-comparison.json',{'pdf':ident((OUT/'HTT_REPORT_A_R3.pdf').read_bytes()),'pages':results,'changed_pages':[r['page'] for r in results if not r['pixels_equal_to_initial']]})
print('changed pages',[r['page'] for r in results if not r['pixels_equal_to_initial']])
