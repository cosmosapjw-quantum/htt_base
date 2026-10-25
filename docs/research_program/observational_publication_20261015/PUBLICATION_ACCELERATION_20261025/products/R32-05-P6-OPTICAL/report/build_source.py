"""Literal manuscript-to-RevTeX layout; scientific equations are copied verbatim."""
from pathlib import Path
import re
R=Path(__file__).resolve().parent
s=(R.parent/'science/MANUSCRIPT.md').read_text(); s,refs=s.split('## References for bibliography generation')
title=s.splitlines()[0][2:]; s=s[s.index('## Abstract')+len('## Abstract'):];abstract,s=s.split('## 1.',1);s='## 1.'+s
# Approved notation clarification, with no changed equation.
s=s.replace('Unmeasured terms are not assigned zero.','Here the comparator quantity \\(W^2\\) is the dimensionless vorticity contribution; it is distinct from the working whitening matrix \\(W\\) in Section 3. Unmeasured terms are not assigned zero.')
# Protect all mathematics from prose conversion.
math=[]
def hold(m):math.append(m.group());return f'@@MATH{len(math)-1}@@'
s=re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)',hold,s,flags=re.S)
abstract=re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)',hold,abstract,flags=re.S)
def prose(s):
 s=re.sub(r'^## \d+\. (.+)$',lambda m:r'\section{'+m[1]+'}',s,flags=re.M)
 s=re.sub(r'^### (.+)$',lambda m:r'\subsection{'+m[1]+'}',s,flags=re.M)
 s=re.sub(r'\*\*(.*?)\*\*',lambda m:r'\textbf{'+m[1]+'}',s,flags=re.S)
 s=s.replace('*Proof.*',r'\textit{Proof.}')
 s=re.sub(r'\[(Heinesen2021|Maartens2024|QOMethods|CF4Retained)\]',lambda m:r'\cite{'+m[1]+'}',s)
 s=s.replace('−','-').replace('–','--').replace('—','---').replace('“','``').replace('”',"''").replace('’',"'")
 for i,m in enumerate(math):
  if m.startswith(r'\['):m=m.replace(r'\[',r'\begin{equation}',1).replace(r'\]',r'\end{equation}')
  s=s.replace(f'@@MATH{i}@@',m)
 return s
s=prose(s);abstract=prose(abstract)
# Layout-only line wrapping of long equation (26); every scientific token retained.
s=s.replace(r' t:=\|\widehat S_{\rm app}\|_F=0.03265680189321492,\qquad',r' \begin{gathered}t:=\|\widehat S_{\rm app}\|_F=0.03265680189321492,\\')
s=s.replace(r' \lambda(\widehat S_{\rm app})=',r' \lambda(\widehat S_{\rm app})=\\')
s=s.replace(r'0.022399216273178365).\tag{26}',r'0.022399216273178365).\end{gathered}\tag{26}')
caption1='Conditional shear bounds from the retained apparent CF4 tensor. The horizontal coordinate is an assumed qualified dimensionless response-error radius divided by the apparent norm. The left panel gives the dimensionless shear-amplitude interval. The right panel converts it to a dimensional shear rate, divided by a symbolic reference Hubble rate, for three assumed relative Hubble intervals. A positive lower bound requires $r_Q$ below the apparent norm. The figure assumes the same-event, same-congruence response in equation (28); neither error radius nor a physical shear detection is estimated here.'
caption2='A deterministic projection of the tensor error region. The retained working matrix supplies an illustrative ellipsoidal shape, with unit assumed ellipsoid radius and three assumed isotropic response radii. Curves show the projection onto the first two Frobenius-orthonormal source coordinates, and the corresponding centered directional support. The product error-set assumption gives the support exactly. The unit radius has no assigned confidence level, and the additional response radii are sensitivity choices.'
tables=r'''
\begin{table}[tb]
\caption{Retained apparent tensor in the dimensionless J2000 source basis (24). Singular values use the retained working metric. All central values are generated from full precision retained inputs.}
\input{generated/tensor.tex}
\end{table}
\begin{table}[tb]
\caption{Conditional frontier for assumed $r_Q$ and assumed $r_H/H_*=0.1$. Rate columns mean $\|\sigma\|_F/(\sqrt6 H_*)$. The zero-radius row is an exact-response limiting scenario, without a calibrated physical error estimate.}
\input{generated/frontier.tex}
\end{table}
'''
s=s.replace(r'\textbf{Proposition 3',tables+'\n'+r'\textbf{Proposition 3',1)
fig1='\n'+r'\begin{figure}[tb]\includegraphics[width=\linewidth]{figures/error_frontier.pdf}\caption{'+caption1+r'}\end{figure}'+'\n'
s=s.replace('If the measured tensor were instead',fig1+'\nIf the measured tensor were instead',1)
fig2='\n'+r'\begin{figure}[tb]\includegraphics[width=\linewidth]{figures/tensor_error_image.pdf}\caption{'+caption2+r'}\end{figure}'+'\n'
s=s.replace(r'\section{Tensor carriers',fig2+'\n'+r'\section{Tensor carriers',1)
bib=[]
for line in refs.splitlines():
 if line.startswith('- ['):
  key,text=line[3:].split('] ',1)
  text=text.replace('–','--').replace('—','---').replace('“','``').replace('”',"''").replace('‘','`').replace('’',"'")
  text=text.replace('_',r'\_')
  text=re.sub(r'https://[^ ]+',lambda m:r'\url{'+m[0]+'}',text)
  bib.append(r'\bibitem{'+key+'} '+text)
references='\\begin{thebibliography}{9}\n'+'\n\n'.join(bib)+'\n\\end{thebibliography}\n'
(R/'references.tex').write_text(references)
header=r'''\documentclass[aps,prd,reprint,onecolumn,11pt,nofootinbib,notitlepage]{revtex4-2}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,bm,graphicx}
\usepackage[colorlinks=true,citecolor=blue,linkcolor=blue,urlcolor=blue]{hyperref}
\setlength{\emergencystretch}{4em}
\begin{document}
'''
(R/'main.tex').write_text(header+'\\title{'+title+'}\n\\author{Conditional methods review draft}\\noaffiliation\n\\begin{abstract}\n'+abstract+'\n\\end{abstract}\n\\maketitle\n'+s+'\n\\input{references.tex}\n\\end{document}\n')
assert len(re.findall(r'\\tag\{\d+\}',s))==35
print('Faithfully copied 35 tagged equations; generated two table and two figure inputs.')
