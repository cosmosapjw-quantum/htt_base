from runner import *
import shutil
(OUT/'structure.lua').write_text(r'''
local appendix_started = false
local function strip(inlines, prefix)
  local text = pandoc.utils.stringify(inlines)
  return pandoc.Inlines(pandoc.read(text:gsub(prefix, '', 1), 'markdown').blocks[1].content)
end
function Header(h)
 local s=pandoc.utils.stringify(h.content)
 if s:match('^Part [IVX]+%. ') then
  local title=s:gsub('^Part [IVX]+%. ', '')
  return pandoc.RawBlock('latex', '\\part{'..title..'}')
 elseif s:match('^Appendix [A-E]%. ') then
  h.level=1; h.content=strip(h.content,'^Appendix [A-E]%. ')
  if not appendix_started then appendix_started=true;return {pandoc.RawBlock('latex','\\appendix'),h} end
 elseif s=='Abstract' or s=='How to read this report' or s=='References' then
  h.level=1;h.classes:insert('unnumbered')
 elseif s:match('^[A-E]%.%d+ ') then
  h.level=2;h.content=strip(h.content,'^[A-E]%.%d+ ')
 elseif s:match('^%d+%.%d+ ') then
  h.level=2;h.content=strip(h.content,'^%d+%.%d+ ')
 elseif s:match('^%d+%. ') then
  h.level=1;h.content=strip(h.content,'^%d+%. ')
 end
 return h
end
function CodeBlock(b)
 local changed=false
 local t=b.text:gsub('%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d+',function(d)
  if #d<=68 then return d end
  changed=true
  local chunks={}; for start=1,#d,68 do chunks[#chunks+1]=d:sub(start,start+67) end
  return table.concat(chunks,'\n  ')
 end)
 if changed then
  return {pandoc.Para(pandoc.Inlines{pandoc.Str('Long integers continue on indented lines; concatenate their decimal lines before applying division.')}),pandoc.RawBlock('latex','\\begin{verbatim}\n'..t..'\n\\end{verbatim}')}
 end
 return b
end
''')
(OUT/'header.tex').write_text(r'''
\usepackage{xurl}
\usepackage{titlesec}
\usepackage{microtype}
\setmonofont{Latin Modern Mono}[Scale=0.85]
\titleformat{\section}{\normalfont\Large\bfseries\raggedright}{\thesection}{1em}{}
\titleformat{\subsection}{\normalfont\large\bfseries\raggedright}{\thesubsection}{1em}{}
\setlength{\emergencystretch}{2em}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,citecolor=blue}
''')
(OUT/'metadata.yaml').write_text('''title: From a CMB Sky Map to Physical Constraints
subtitle: An introductory account of tensor morphology, kinematical bounds and response-limited inference
author: Jiwon Park
date: 7 September 2026
lang: en-GB
documentclass: article
classoption: [11pt, a4paper]
geometry: [margin=25mm]
''')
