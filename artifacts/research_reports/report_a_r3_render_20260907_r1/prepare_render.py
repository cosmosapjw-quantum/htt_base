from runner import *
import difflib
original=(REPO/'docs/research_reports/report_a/structure.lua').read_text()
adapter=original.replace('''        else
          if block.level >= 2 then''','''        elseif label == "References" then
          block.level = 1
          block.identifier = "references"
          table.insert(block.classes, "unnumbered")
        elseif appendix_started then
          -- This edition already uses natural Markdown appendix levels.
          -- B.1/D.1 prefixes are supplied by LaTeX subsection numbering.
          if #block.content > 0 and block.content[1].t == "Str"
              and block.content[1].text:match("^[A-Z]%.%d+[%.%d]*%.?$") then
            table.remove(block.content, 1)
            if #block.content > 0 and block.content[1].t == "Space" then
              table.remove(block.content, 1)
            end
          end
        else
          if block.level >= 2 then''')
assert adapter != original
adapter+='''
-- Formatting only: permit long source paths/hashes/IDs to break, without
-- changing their literal content. xurl supplies safe break opportunities.
function Code(code)
  if #code.text > 24 then
    assert(not code.text:find("[{}\\\\]"), "unsupported literal in code wrapper")
    return pandoc.RawInline("latex", "{\\\\ttfamily\\\\nolinkurl{" .. code.text .. "}}")
  end
end
'''
(OUT/'structure-r3.lua').write_text(adapter)
header=(REPO/'docs/research_reports/report_a/header.tex').read_text()
newheader=header.replace('\\usepackage[T1]{fontenc}','% XeLaTeX uses Unicode fonts; no unconditional legacy T1 override.')
newheader+='''
% Edition-only layout; scientific Markdown remains untouched.
\\usepackage{xurl}
\\usepackage{titlesec}
\\titleformat{\\section}{\\normalfont\\Large\\bfseries\\raggedright}{\\thesection}{1em}{}
\\titleformat{\\subsection}{\\normalfont\\large\\bfseries\\raggedright}{\\thesubsection}{1em}{}
\\setmonofont{Latin Modern Mono}[Scale=0.85]
'''
(OUT/'header-r3.tex').write_text(newheader)
(OUT/'metadata.yaml').write_text('''title: Tensorised Low-Multipole CMB Morphology, Kinematical Isotropy Bounds and Response-Limited Identification
subtitle: "Evidence-integrated theory-and-methods edition, revision 3 — review candidate; not a canonical release"
author: Jiwon Park
date: 2026-09-07
lang: en-GB
documentclass: article
classoption: [11pt, a4paper]
geometry: [margin=25mm]
''')
for name,old,new in [('structure',original,adapter),('header',header,newheader)]:
 (E/(name+'-adapter.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name+'-source',tofile=name+'-r3')))
run('pandoc-render',[PANDOC,MAN,'--from='+FMT,'--to=latex','--standalone','--number-sections','--top-level-division=section','--lua-filter='+str(OUT/'structure-r3.lua'),'--citeproc','--bibliography='+str(BIB),'--metadata-file='+str(OUT/'metadata.yaml'),'--include-in-header='+str(OUT/'header-r3.tex'),'--wrap=preserve','--log='+str(E/'pandoc.json'),'--output='+str(OUT/'HTT_REPORT_A_R3.tex')])
p=OUT/'HTT_REPORT_A_R3.tex'; original_tex=p.read_text(); (E/'pandoc-original.tex').write_text(original_tex)
tex=original_tex.replace(r'\usepackage{amsmath,amssymb}',r'\usepackage{amsmath,amssymb,mathtools}',1)
assert tex!=original_tex
p.write_text(tex)
(E/'tex-package-order.patch').write_text(''.join(difflib.unified_diff(original_tex.splitlines(True),tex.splitlines(True),fromfile='pandoc-original.tex',tofile='HTT_REPORT_A_R3.tex')))
run('latexmk-initial',['latexmk','-xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','-outdir='+str(OUT),str(p)],timeout=240,cwd=OUT,expected=None)
for suffix in ('log','pdf','tex'):
 f=OUT/('HTT_REPORT_A_R3.'+suffix)
 if f.exists():(E/('initial.'+suffix)).write_bytes(f.read_bytes())
