#!/usr/bin/env python3
"""Render this report's restricted Markdown to XeLaTeX; no research imports.

Input grammar: headings, paragraphs, pipe tables, list items, TeX math,
inline code/bold, links and explicit HTML anchors. Not a general MD engine.
"""
from pathlib import Path
import argparse,csv,re,subprocess
BASE=Path(__file__).resolve().parent

def esc(s):
    d={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(d.get(c,c) for c in s)

def inline(s):
    patt=r'\\\(.*?\\\)|`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]*\)|https?://[^\s]+|\[S\d{2}[^\]]*\]'
    out=[];pos=0
    for m in re.finditer(patt,s):
        out.append(esc(s[pos:m.start()]));v=m.group()
        if v.startswith(r'\('):out.append(v)
        elif v.startswith('`'):out.append(r'\texttt{'+esc(v[1:-1])+ '}')
        elif v.startswith('**'):out.append(r'\textbf{'+esc(v[2:-2])+'}')
        elif v.startswith('http'):out.append(r'\url{'+v+'}')
        elif v.startswith('[S') and '](' not in v:
            sid=re.search(r'S\d{2}',v).group();out.append(r'\hyperlink{src:'+sid+'}{'+esc(v)+'}')
        else:
            label,url=re.match(r'\[(.*?)\]\((.*?)\)',v).groups();out.append(r'\href{'+url+'}{'+esc(label)+'}')
        pos=m.end()
    out.append(esc(s[pos:]));return ''.join(out)

def render(md):
    lines=md.splitlines();out=[];i=0;paragraph=[]
    def flush():
        if paragraph:out.append(inline(' '.join(paragraph))+'\n');paragraph.clear()
    while i<len(lines):
        s=lines[i].strip()
        if s=='## 초록':break
        i+=1
    while i<len(lines):
        s=lines[i].strip()
        if not s:flush();i+=1;continue
        if s.startswith('<a id='):
            flush();out.append(r'\hypertarget{'+re.search(r'id="([^"]+)"',s).group(1)+'}{}');i+=1;continue
        if s==r'\[':
            flush();eq=[];i+=1
            while i<len(lines) and lines[i].strip()!=r'\]':eq.append(lines[i]);i+=1
            if i==len(lines):raise ValueError('Unclosed display math')
            out.append('\\[\n'+'\n'.join(eq)+'\n\\]');i+=1;continue
        if s.startswith('##'):
            flush();level=len(s)-len(s.lstrip('#'));t=s[level:].strip();cmd='section' if level==2 else 'subsection';out.append(chr(92)+cmd+'*{'+inline(t)+'}')
            if level==2:out.append(r'\addcontentsline{toc}{section}{'+esc(t)+'}')
            i+=1;continue
        if s.startswith('|'):
            flush();rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                line=lines[i].strip();cells=[c.strip() for c in line[1:-1].split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append(cells)
                i+=1
            n=len(rows[0]);weights={3:[.23,.29,.48],4:[.20,.27,.27,.26]}.get(n,[1/n]*n)
            out.append(r'{\small\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.3}')
            spec=''.join(r'>{\raggedright\arraybackslash}p{'+f'{w:.4f}'+r'\dimexpr\linewidth-'+str(n*8)+r'pt\relax}' for w in weights)
            out.append(r'\begin{longtable}{'+spec+'}'+r'\toprule')
            for j,row in enumerate(rows):
                if len(row)!=n:raise ValueError('Malformed table')
                vals=[inline(c) for c in row]
                out.append(' & '.join(vals)+r' \\')
                if j==0:out.append(r'\midrule\endhead')
            out.append(r'\bottomrule\end{longtable}}');continue
        if s.startswith('- '):
            flush();out.append(r'\noindent\textbullet\ '+inline(s[2:])+r'\par');i+=1;continue
        paragraph.append(s);i+=1
    flush();return '\n\n'.join(out)

PREAMBLE=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=23mm,headheight=15pt]{geometry}
\usepackage{fontspec,xeCJK}
\xeCJKsetup{CJKspace=true}
\setmainfont{TeX Gyre Pagella}
\setCJKmainfont{Noto Serif CJK KR}
\setCJKsansfont{Noto Sans CJK KR}
\setCJKmonofont{Noto Sans Mono CJK KR}
\setmonofont{DejaVu Sans Mono}[Scale=0.8]
\usepackage{amsmath,amssymb,mathtools,booktabs,longtable,array}
\usepackage{microtype,setspace,xcolor,titlesec,fancyhdr,xurl}
\definecolor{navy}{HTML}{17384F}
\usepackage[colorlinks=true,linkcolor=navy,urlcolor=navy,bookmarksopen=true]{hyperref}
\hypersetup{pdftitle={HTT 수학·물리·통계 종합 이론 보고서},pdfauthor={HTT manuscript}}
\setstretch{1.21}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.65em}
\setlength{\emergencystretch}{4em}
\titleformat{\section}{\Large\sffamily\bfseries\color{navy}}{}{0em}{}
\titleformat{\subsection}{\large\sffamily\bfseries}{}{0em}{}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small HTT · 수학 / 물리 / 통계}
\fancyhead[R]{\small 2026-09-13}
\fancyfoot[C]{\thepage}
\begin{document}
\hypersetup{pageanchor=false}
\begin{titlepage}
\color{navy}\vspace*{25mm}
{\sffamily\large HTT RESEARCH COMPENDIUM}\par\vspace{10mm}
{\sffamily\Huge\bfseries 수학·물리·통계\\[4mm]종합 이론 보고서}\par\vspace{12mm}
{\Large 전체 연구 갈래의 최신 유지 결과와\\[3mm]텐서 기반 통합 분석}\par\vspace{18mm}
{\large Low-ell morphology · Tensorized MES\\[3mm]Kinematics · Depth discrimination · Statistical inference}\par
\vfill
\color{black}2026년 9월 13일 · 한국어 편집판 1\par
기존 문서·구현·증명 근거의 종합. 새로운 연구 계산이나 증명 판정은 수행하지 않음.\par
분기별 고정 source 및 관측 적용 범위는 본문과 출처 지도에 명시.\par
\end{titlepage}
\pagenumbering{roman}\hypersetup{pageanchor=true}
\tableofcontents\clearpage\pagenumbering{arabic}
'''
def main():
    p=argparse.ArgumentParser();p.add_argument('--tex-only',action='store_true');a=p.parse_args()
    md=(BASE/'REPORT.md').read_text();body=render(md)
    sources=list(csv.DictReader((BASE/'sources.csv').open()))
    tail=r'\clearpage\section*{내부 출처 지도}\addcontentsline{toc}{section}{내부 출처 지도}'+'\n'
    for r in sources:
        tail+=r'\hypertarget{src:'+r['source_id']+'}{}'+r'\textbf{'+r['source_id']+r'}\quad '+r'\nolinkurl{'+r['path']+r'}\par'+'\n'
        tail+=r'{\small 고정 커밋: \texttt{'+r['commit'][:12]+r'}; 본문 '+esc(r['report_sections'])+r'절. \href{'+r['url']+r'}{원격 원문 열기}}\par'+'\n'
    tex=PREAMBLE+body+'\n'+tail+'\n'+r'\end{document}'+'\n';(BASE/'report.tex').write_text(tex)
    if not a.tex_only:
        subprocess.run(['latexmk','-xelatex','-interaction=nonstopmode','-halt-on-error','-outdir=.build','report.tex'],cwd=BASE,check=True)
        (BASE/'report.pdf').write_bytes((BASE/'.build/report.pdf').read_bytes())
if __name__=='__main__':main()
