#!/usr/bin/env python3
"""Render evidence-layer overview and the actual 60/129 R78 science DAG.

Requires graphviz dot on the authorized research workstation. Output SVGs are
static view artifacts, not physical/cosmological verification.
"""
import json
from pathlib import Path
import subprocess

OUT=Path("docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119")
D=json.loads((OUT/"INTEGRATED_DAG.json").read_text())
assert len(D["nodes"])==60 and len(D["edges"])==129
for n in D["nodes"]:
    assert n["id"] in D["topological_order"]
MMD="""flowchart TB
  subgraph E["재사용 근거 · R60–R77"]
    R60["R60–R66<br/>실제 source·조건부 통계"]
    R67["R67–R77<br/>5뷰 물리 정리·반례"]
    R60 --> R67
  end

  subgraph Q["11개 자료·물리 전달 확인"]
    CF4["SQ-CF4<br/>CF4 calibration"]
    GAIA["SQ-GAIA<br/>Gaia VSH systematics"]
    RADIO["SQ-RADIO<br/>source k / κ"]
    FRAME["SQ-FRAME<br/>observer·source frame"]
    OPT["SQ-OPTICAL<br/>Sachs/Jacobi"]
    FLUX["Photon flux"]
    NORMAL["Bianchi normal flux"]
    CMB["CMB matched null"]
    NATIVE["외부 native transfer"]
    JOINT["SQ-CROSS-COV<br/>공동 C·heldout"]
    FRAME --> OPT
    CF4 --> JOINT
    GAIA --> JOINT
    RADIO --> JOINT
    OPT --> JOINT
  end

  subgraph P["원래 42개 과학 DAG 목표 · acceptance 불변"]
    P1["P1<br/>signed inference"]
    P2["P2<br/>CMB morphology"]
    P3["P3<br/>H(z,n) · CF4"]
    P4["P4<br/>boost / tilt"]
    P5["P5<br/>Bianchi"]
    P6["P6<br/>GR kinematics"]
  end

  subgraph PHY["PHY-01–07 · 조건부 물리 결합"]
    PHY1["01 · CF4 × normal GR"]
    PHY2["02 · Photon × Codazzi"]
    PHY3["03 · Radio × photon"]
    PHY4["04 · Gaia × Lie B2"]
    PHY5["05 · Bianchi × tilt"]
    PHY6["06 · Shear × kinetic"]
    PHY7["07 · CF4 × radio"]
  end

  R67 --> CF4
  R67 --> GAIA
  R67 --> RADIO
  CF4 --> P3
  GAIA --> P6
  RADIO --> P4
  CMB --> P2
  NATIVE --> P5
  FRAME --> P4
  OPT --> P3
  JOINT --> P6

  CF4 --> PHY1
  OPT --> PHY1
  CMB --> PHY2
  NORMAL --> PHY2
  FLUX --> PHY2
  RADIO --> PHY3
  FLUX --> PHY3
  GAIA --> PHY4
  OPT --> PHY4
  FRAME --> PHY4
  NORMAL --> PHY5
  OPT --> PHY5
  CMB --> PHY6
  FLUX --> PHY6
  CF4 --> PHY7
  RADIO --> PHY7

  classDef completed fill:#d8ede3,stroke:#4f9579,color:#173b32
  classDef available fill:#fff1c8,stroke:#d5a13f,color:#553b12
  classDef blocked fill:#f7dddd,stroke:#b96767,color:#522121
  classDef route fill:#dceafa,stroke:#7396bf,color:#163f68
  class R60,R67 completed
  class CF4,GAIA,RADIO,FRAME available
  class FLUX,NORMAL,CMB,NATIVE blocked
  class OPT,JOINT available
  class PHY1,PHY2,PHY3,PHY4,PHY5,PHY6,PHY7 route
"""
(OUT/"PLAN_OVERVIEW.mmd").write_text(MMD)

def q(x):
    return json.dumps(str(x),ensure_ascii=False)
paper_order=["COMMON","P1","P2","P3","P4","P5","P6","SOURCE","CROSS"]
colors={"completed_scoped":"#dcefe3","blocked_input":"#fbe1e1",
        "pending":"#ebeff3","ready_scoped":"#fff0c5",
        "blocked_physical_anchor":"#fbe1e1","blocked_source":"#fbe1e1",
        "blocked_external":"#f4d3d3","pending_dependency":"#fff1d7",
        "pending_conditional":"#fff1d7",
        "theory_verified_physical_data_pending":"#dce9fb"}
nodes_by={}
for n in D["nodes"]:
    group=n["paper"] if n.get("node_class") not in ("source_qualification","physical_cross_route") else ("SOURCE" if n["node_class"]=="source_qualification" else "CROSS")
    nodes_by.setdefault(group,[]).append(n)
descrip={"COMMON":"공통 정본 (7)", "P1":"P1 signed inference", "P2":"P2 CMB", "P3":"P3 directional H(z,n)",
        "P4":"P4 boost / tilt","P5":"P5 Bianchi","P6":"P6 kinematics",
        "SOURCE":"11 source/physics qualifications","CROSS":"7 physical PHY combinations"}
s=['digraph R78 {','  graph [rankdir=LR, pad=0.4, nodesep=0.30, ranksep=0.62, splines=polyline, concentrate=true, fontname="DejaVu Sans", fontsize=16, label="R78 unified 60-node / 129-edge science dependency DAG", labelloc=t];',
   '  node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=10, margin="0.11,0.08", color="#8698a8"];',
   '  edge [color="#a4aeb9", arrowsize=0.53, penwidth=0.8];']
for k in paper_order:
    if not nodes_by.get(k):continue
    s.append(f'  subgraph cluster_{k} {{')
    s.append(f'    label={q(descrip[k])}; style=rounded; color="#b5c8da"; bgcolor="#fafcff"; fontsize=13;')
    for n in nodes_by[k]:
        name=n["id"]
        title=n.get("objective",name).replace("\n"," ")
        color=colors.get(n.get("state"),"#e7e7e7")
        label=name if k not in ("SOURCE","CROSS") else name+"\\n"+title[:26]
        tooltip=f'{n["id"]} / {n.get("state")} / {title}'
        s.append(f'    {q(name)} [label={q(label)}, fillcolor={q(color)}, tooltip={q(tooltip)}];')
    s.append('  }')
for e in D["edges"]:
    style='dashed' if e["kind"]=="new_qualification_overlay" else 'solid'
    color='#b87669' if e["kind"]=="new_qualification_overlay" else '#5482ae' if e["kind"]=="new_source_or_physical_route" else '#a3aeb8'
    s.append(f'  {q(e["from"])} -> {q(e["to"])} [style={style},color={q(color)}];')
s.append('}')
(OUT/"PLAN_FULL.dot").write_text("\n".join(s)+"\n")
OV='''digraph R78Overview {
 graph [rankdir=LR, bgcolor="white", fontname="DejaVu Sans", fontsize=16, pad=.45,
 label="R78: one science SSOT, 42 immutable goals + 11 source qualifiers + 7 PHY links", labelloc=t, nodesep=.42, ranksep=.95];
 node [shape=box, style="filled,rounded", fontname="DejaVu Sans", fontsize=13, penwidth=1.3, margin=".17,.10"];
 edge [arrowsize=.75, penwidth=1.4];
 E [label="R60–R66\\nobserved-source results",fillcolor="#dcefe3",color="#4c9276"];
 T [label="R67–R77\\nconditional physics and 5 views",fillcolor="#dcefe3",color="#4c9276"];
 CF [label="SQ-CF4\\nNEXT: same-group calibration",fillcolor="#fff0c5",color="#d8a744"];
 GA [label="SQ-GAIA\\nredshift/scanning/AGN",fillcolor="#fff0c5",color="#d8a744"];
 RA [label="SQ-RADIO\\nk, kappa and LSS",fillcolor="#fff0c5",color="#d8a744"];
 FR [label="SQ-FRAME → SQ-OPTICAL\\nobserver/Sachs transfers",fillcolor="#fff0c5",color="#d8a744"];
 EX [label="CMB / photon flux / normal flux\\nexternal native transfer blocked",fillcolor="#f9dcdc",color="#bd7171"];
 P [label="P1–P6\\n42 original science goals\\n18 scoped · 23 pending · 1 blocked",fillcolor="#e8edf2",color="#7e8e9a"];
 PHY [label="PHY-01–07\\n7 conditional physical links",fillcolor="#dce9fb",color="#638eb8"];
 J [label="SQ-CROSS-COV\\nheldout, real joint source law",fillcolor="#fff0c5",color="#d8a744"];
 E -> T; E -> CF; E -> GA; E -> RA;
 T -> PHY; CF -> P; GA -> P; RA -> P; FR -> P; EX -> P;
 CF -> PHY; GA -> PHY; RA -> PHY; FR -> PHY; EX -> PHY;
 CF -> J; GA -> J; RA -> J; FR -> J;
 J -> P; J -> PHY;
 }'''
(OUT/"PLAN_OVERVIEW.dot").write_text(OV)
for basename in ("PLAN_FULL","PLAN_OVERVIEW"):
    out=subprocess.run(["dot","-Tsvg",str(OUT/(basename+".dot")),"-o",str(OUT/(basename+".svg"))],
                       capture_output=True,text=True)
    if out.returncode:raise RuntimeError((basename,out.stderr))
    p=OUT/(basename+".svg")
    assert p.is_file() and p.stat().st_size>500
    print("R78_GRAPHVIZ_SVG_READY",basename,p.stat().st_size)
print("R78_MERMAID_OVERVIEW_FILE_READY", (OUT/"PLAN_OVERVIEW.mmd").stat().st_size)
