#!/usr/bin/env python3
"""Analytic mirror geometry and saved R24 chirality certificate figures.

Run from any directory: python reproduce_geometry.py
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).resolve().parent
SRC = BASE / "sources"
FIG = BASE / "figures"
OUT = BASE / "output"
FIG.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.titlesize": 11, "axes.labelsize": 9.5,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})
NAVY, BLUE, TEAL, GRAY = "#16324F", "#247BA0", "#2A9D8F", "#64748B"


def save(fig, stem):
    fig.savefig(FIG / (stem + ".pdf"), bbox_inches="tight")
    fig.savefig(FIG / (stem + ".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def adjoint(q, w):
    sym = (np.einsum("i,jk->ijk", w, q) +
           np.einsum("j,ik->ijk", w, q) +
           np.einsum("k,ij->ijk", w, q)) / 3
    qw = q @ w
    eye = np.eye(3)
    trace = (np.einsum("ij,k->ijk", eye, qw) +
             np.einsum("ik,j->ijk", eye, qw) +
             np.einsum("jk,i->ijk", eye, qw))
    return sym - 2 * trace / 15


def score(q, o):
    v = np.einsum("ijk,jk->i", o, q)
    chi = float(np.linalg.det(np.column_stack([v, q @ v, q @ q @ v])))
    return 135 * chi / (4*math.sqrt(2)*np.linalg.norm(q)**6*np.linalg.norm(o)**3)


def witness():
    q = np.diag([-1 / math.sqrt(2), 0, 1 / math.sqrt(2)])
    w = np.array([math.sqrt(10)/4, 1, math.sqrt(10)/4])
    o = adjoint(q, w)
    R = np.diag([-1., 1., 1.])
    qm = R @ q @ R.T
    om = np.einsum("ia,jb,kc,abc->ijk", R, R, R, o)
    assert abs(np.linalg.norm(q)-1)<1e-14 and abs(np.linalg.norm(o)-1)<1e-14
    assert abs(np.trace(q))<1e-14 and np.max(np.abs(np.einsum("iik->k", o)))<1e-14
    assert abs(np.linalg.norm(qm)-1)<1e-14 and abs(np.linalg.norm(om)-1)<1e-14
    assert abs(score(q,o)-1)<1e-14 and abs(score(qm,om)+1)<1e-14
    rng=np.random.default_rng(70924)
    dirs=rng.normal(size=(256,3));dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    original = np.einsum("ni,ij,nj->n", dirs @ R, q, dirs @ R)
    original += np.einsum("ni,nj,nk,ijk->n", dirs @ R, dirs @ R, dirs @ R, o)
    mirrored = np.einsum("ni,ij,nj->n", dirs, qm, dirs)
    mirrored += np.einsum("ni,nj,nk,ijk->n", dirs, dirs, dirs, om)
    err=float(np.max(np.abs(original-mirrored)))
    assert err<2e-15
    return q,o,qm,om,err


def angular_fields(q,o,qm,om):
    lon=np.linspace(-math.pi,math.pi,361)
    lat=np.linspace(-math.pi/2,math.pi/2,181)
    ll,bb=np.meshgrid(lon,lat)
    n=np.stack([np.cos(bb)*np.cos(ll),np.cos(bb)*np.sin(ll),np.sin(bb)],axis=-1)
    def eval_field(tensor2,tensor3):
        f2=np.einsum("...i,ij,...j->...",n,tensor2,n)
        f3=np.einsum("...i,...j,...k,ijk->...",n,n,n,tensor3)
        return f2,f3
    f2,f3=eval_field(q,o); f2m,f3m=eval_field(qm,om)
    return lon,lat,[f2,f3,f2+f3,f2m+f3m],{
        "f2_range":[float(f2.min()),float(f2.max())],
        "f3_range":[float(f3.min()),float(f3.max())],
        "combined_range":[float((f2+f3).min()),float((f2+f3).max())],
        "mirror_range":[float((f2m+f3m).min()),float((f2m+f3m).max())],
    }


def fig08(q,o,qm,om):
    lon,lat,fields,ranges=angular_fields(q,o,qm,om)
    extent=max(float(np.max(np.abs(f))) for f in fields)
    titles=[r"Quadrupole $Q_{ij}n^in^j$",
            r"Octupole $O_{ijk}n^in^jn^k$",
            r"Joint field: $C=+1$",
            r"Reflected joint field: $C=-1$"]
    fig,axes=plt.subplots(2,2,figsize=(10.1,6.45),subplot_kw={"projection":"mollweide"})
    for ax,field,title in zip(axes.flat,fields,titles):
        artist=ax.pcolormesh(lon,lat,field,cmap="RdBu_r",vmin=-extent,vmax=extent,
                             shading="auto",rasterized=True)
        ax.grid(color="white",alpha=.45,lw=.6)
        ax.set_title(title,pad=11)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    cax=fig.add_axes([.19,.105,.62,.025])
    fig.colorbar(artist,cax=cax,orientation="horizontal",
                 label=r"Angular field $f(n)=Q{:}nn+O{:}nnn$ (unit tensor norms)")
    fig.suptitle("Sharp tensor witness and its mirror",x=.055,y=.99,ha="left",fontsize=13)
    fig.text(.055,.015,
             "Analytic construction, not a CMB map. Both tensors have unit full Frobenius norm; reflection preserves their norms and reverses C.",
             color=GRAY,fontsize=8)
    fig.subplots_adjust(left=.04,right=.98,top=.92,bottom=.21,hspace=.18,wspace=.04)
    save(fig,"fig08_tensor_mirror")
    return ranges


def certificate_counts(result):
    expected=["0/1","1/1000000","1/100000","1/10000","1/1000","1/20"]
    counts=[]
    for rho in expected:
        statuses=[next(p["status"] for p in b["perturbation_scenarios"] if p["rho"]==rho)
                  for b in result["bundles"]]
        c=Counter(statuses)
        assert set(c)<= {"CERTIFIED_SIGN_PRESERVED","INCONCLUSIVE"}
        counts.append({"rho":rho,"certified":c["CERTIFIED_SIGN_PRESERVED"],
                       "inconclusive":c["INCONCLUSIVE"]})
    assert [r["certified"] for r in counts]==[60,60,39,0,0,0]
    comparison=[]
    display={"same_processing_split_vs_full":"Split vs full",
             "primary_vs_pilot_zero_window":"Primary vs pilot",
             "pilot_window_vs_zero":"Window vs zero"}
    for key in display:
        rows=[c for c in result["comparisons"] if c["kind"]==key]
        changes=sum(a["chi_signs"][0]!=a["chi_signs"][1] for a in rows)
        comparison.append({"kind":key,"label":display[key],"changed":changes,
                           "unchanged":len(rows)-changes,"total":len(rows)})
    assert [(c["changed"],c["total"]) for c in comparison]==[(18,48),(0,15),(3,30)]
    return counts,comparison


def fig09(counts,comparisons):
    fig,(ax,bx)=plt.subplots(1,2,figsize=(9.9,4.35),width_ratios=[1.25,.9])
    xx=np.arange(6)
    certified=np.array([r["certified"] for r in counts])
    inconclusive=np.array([r["inconclusive"] for r in counts])
    ax.bar(xx,certified,color=TEAL,width=.65,label="Sign certified")
    ax.bar(xx,inconclusive,bottom=certified,color="#CBD5DC",width=.65,label="Inconclusive")
    for i,val in enumerate(certified):
        if val:ax.text(i,val/2,str(val),ha="center",va="center",
                       color="white",fontweight="bold",fontsize=9)
    ax.set(xticks=xx,xticklabels=["0","10⁻⁶","10⁻⁵","10⁻⁴","10⁻³","0.05"],
           xlabel="Declared harmonic perturbation radius ρ",ylabel="Configurations / 60",
           ylim=(0,67))
    ax.set_title("Exact sign certificates",loc="left")
    yy=np.arange(3)
    changed=np.array([c["changed"] for c in comparisons])
    unchanged=np.array([c["unchanged"] for c in comparisons])
    bx.barh(yy,changed,color="#B23A48",height=.58,label="Sign differs")
    bx.barh(yy,unchanged,left=changed,color="#CBD5DC",height=.58,label="Same sign")
    for i,c in enumerate(comparisons):
        bx.text(c["total"]+.7,i,f"{c['changed']}/{c['total']} changed",
                ha="left",va="center",fontsize=8,color=NAVY)
    bx.set(yticks=yy,yticklabels=[c["label"] for c in comparisons],
           xlim=(0,66),xlabel="Same-sky comparison pairs")
    bx.invert_yaxis()
    bx.set_title("Processing sign comparisons",loc="left")
    fig.suptitle("Certificates and processing sensitivity on one observed sky",
                 x=.025,y=.995,ha="left",fontsize=12.5)
    fig.text(.025,.01,"Teal: certified; gray: inconclusive/same sign; red: different sign. All pairs share one Planck PR3 E-mode sky.",
             color=GRAY,fontsize=8)
    fig.tight_layout(rect=(0,.065,1,.92))
    save(fig,"fig09_chirality_certificates")


def main():
    raw=(SRC/"chirality_RESULT.json").read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    summary=json.loads((SRC/"execution_summary.json").read_text())
    expected=next(t["source_sha256"] for t in summary["tasks"]
                  if t["task_id"]=="R24-CMB-CHIRALITY")
    assert digest==expected
    q,o,qm,om,mirror_error=witness()
    fields=fig08(q,o,qm,om)
    result=json.loads(raw)
    counts,comparisons=certificate_counts(result)
    fig09(counts,comparisons)
    checks={
        "source_commit":"10f3ea585c6608e794900efe7e4f8f42c0747a3b",
        "chirality_RESULT_sha256":digest,
        "witness":{"Q_frobenius_norm":float(np.linalg.norm(q)),
                   "O_frobenius_norm":float(np.linalg.norm(o)),
                   "Q_mirror_frobenius_norm":float(np.linalg.norm(qm)),
                   "O_mirror_frobenius_norm":float(np.linalg.norm(om)),
                   "C":float(score(q,o)),"C_mirror":float(score(qm,om)),
                   "field_reflection_max_abs_error":mirror_error,
                   "map_field_ranges":fields},
        "certificate_counts":counts,"same_sky_comparisons":comparisons,
        "scope":"analytic unit-tensor witness and exact saved finite processing certificates",
    }
    (OUT/"geometry_checks.json").write_text(json.dumps(checks,indent=2,allow_nan=False)+"\n")
    print("analytic witness C={:.16f}, mirror C={:.16f}, field reflection error={:.2e}".format(
        checks["witness"]["C"],checks["witness"]["C_mirror"],mirror_error))
    print("certified sign counts", [r["certified"] for r in counts])
    print("comparison changes",[(r["changed"],r["total"]) for r in comparisons])


if __name__=="__main__":
    main()
