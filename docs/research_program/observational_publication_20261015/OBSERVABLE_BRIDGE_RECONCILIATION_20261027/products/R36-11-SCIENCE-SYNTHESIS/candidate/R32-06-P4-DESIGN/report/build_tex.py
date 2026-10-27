#!/usr/bin/env python3
"""Convert the full released Markdown note plus generated tables to RevTeX."""
from pathlib import Path
import re
import subprocess

here = Path(__file__).resolve().parent
source = here / "manuscript_generated.md"
science = here.parent / "science" / "MANUSCRIPT.md"
assert here.name == "report" and source.is_file() and science.is_file()
subprocess.run(["pandoc", str(source), "-f", "markdown+tex_math_single_backslash+raw_tex",
                "-t", "latex", "--wrap=none", "-o", str(here / "body.tex")], check=True)
body = (here / "body.tex").read_text()
anchor = "\\hypertarget{a-common-frame-and-a-finite-response}"
assert body.count(anchor) == 1
body = anchor + body.split(anchor,1)[1]
body = body.replace("\\subsubsection{", "\\P4TEMPHEADING{")
body = body.replace("\\subsection{", "\\section{")
body = body.replace("\\P4TEMPHEADING{", "\\subsection{")
body = re.sub(r"\\section\{[1-8]\. ", r"\\section{", body)
body = body.replace("\\section{Numerical appendix: reproducible comparison}",
                    "\\appendix\n\\section{Numerical appendix: reproducible comparison}")
body = body.replace("\\begin{split}", "\\begin{aligned}").replace("\\end{split}", "\\end{aligned}")
first_scale = body.index("\\[\nc=299792.458")
first_scale_end = body.index("\\]", first_scale) + 2
body = body[:first_scale] + r"""\[
\begin{aligned}
c &= 299792.458\ {\rm km\,s^{-1}}, & R_* &= 100\ {\rm Mpc},\\
v_* &= 300\ {\rm km\,s^{-1}}, & \beta_* &= v_*/c,\\
h_* &= v_*/R_* = 3\ {\rm km\,s^{-1}\,Mpc^{-1}}.
\end{aligned}\tag{1}
\]""" + body[first_scale_end:]
abstract = science.read_text().split("## Abstract\n\n",1)[1].split("\n## 1.",1)[0].strip()
assert "\\tag{27}" in body and body.count("\\begin{figure}") == 5
preamble = r"""\documentclass[aps,prd,preprint,onecolumn,notitlepage]{revtex4-2}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,graphicx,booktabs,longtable,array,calc,hyperref}
\newcommand{\tightlist}{}
\begin{document}
\title{Separating endpoint and history information in radial and astrometric response design}
\author{HTT conditional response-design research}
\noaffiliation
\date{25 October 2026}
\begin{abstract}
"""
ending = r"""
\begin{thebibliography}{1}
\bibitem{Marcori2018} O. H. Marcori, C. Pitrou, J.-P. Uzan, and T. S. Pereira, ``Direction and redshift drifts for general observers and their applications in cosmology,'' Phys. Rev. D \textbf{98}, 023517 (2018), arXiv:1805.12121.
\end{thebibliography}
\end{document}
"""
(here / "body.tex").write_text(body)
(here / "main.tex").write_text(preamble + abstract + "\n\\end{abstract}\n\\maketitle\n" + body + ending)
print(f"RevTeX source generated: {len(body.splitlines())} body lines, 5 figures, equations 1–35")
