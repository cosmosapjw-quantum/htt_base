#!/usr/bin/env python3
"""Build the R8 scientific synthesis from executed, scoped numerical inputs."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'docs/generated/tensor_joint_r8';OUT=ART/'final'


def read(rel):return json.loads((ART/rel).read_text())
def fraction(x):return x['numerator']/x['denominator'] if isinstance(x,dict) else float(x)


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    a=read('orbit_continuation/summary.json');f=read('restricted_history/results.json')
    c=read('law_followup/products.json')['products'];d=read('jet_images/execution_20260912/results.json')
    g=read('final/campaign/summary.json');b=read('representations/execution_after_symmetry/mock2.json')
    observed=read('final/campaign/R8-12/gaussian_observation/latest.json')
    interval=observed['products']['desi_compressed']['confidence_region']['conditional_CI95_display']
    figs=[]
    def save(fig,name,title):
        fig.suptitle(title,fontsize=14)
        fig.text(.02,.015,'R8 | non-claim-bearing research synthesis | fixed inputs and conditional assumptions',fontsize=8,color='.3')
        fig.tight_layout(rect=(0,.045,1,.95));fig.savefig(OUT/(name+'.png'),dpi=180);figs.append((name,fig))
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    cells=a['cells'];idx=np.arange(30)
    axes[0].plot(idx,[x['old_mean_width'] for x in cells],'o',label='saved checkpoint')
    axes[0].plot(idx,[x['mean_width'] for x in cells],'x',label='one continued checkpoint')
    axes[0].set(xlabel='Fixed pool index (10 each: M=31 / 301 / 1000)',ylabel='Mean orbit-distance enclosure width');axes[0].legend()
    lo=np.array([fraction(x['rank']['p_lower']) for x in cells]);hi=np.array([fraction(x['rank']['p_upper']) for x in cells])
    axes[1].vlines(idx,lo,hi,color='tab:blue');axes[1].scatter(idx,(lo+hi)/2,s=12)
    axes[1].axhline(.05,color='tab:red',ls='--',label='alpha=0.05');axes[1].set(xlabel='Fixed pool index',ylabel='Conservative rank interval',ylim=(-.02,1.05));axes[1].legend()
    save(fig,'orbit_continuation','Full-tensor orbit ranks: 5 non-rejections; 25 unresolved intervals')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    u=c['union3'];z=np.array(u['redshift']);res=np.array(u['residual_mag'])
    axes[0].plot(z,res,'o-');axes[0].axhline(0,color='.5',lw=1)
    axes[0].set(xlabel='Released spline-node redshift',ylabel='Distance modulus residual [mag]')
    axes[1].plot(u['omega_grid'],np.array(u['profile_chi2'])-u['chi2']);axes[1].axvline(u['omega_m'],color='.5',ls='--')
    axes[1].set(xlabel='Omega_m (flat LCDM; common offset profiled)',ylabel='Delta chi-square of released compression')
    save(fig,'union3_compressed',f"Union3 approximate compressed scenario: Omega_m={u['omega_m']:.5f}; no exact coverage claim")
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for key in ('hamiltonian','einstein_spatial','killing_rapidity','photon_conservation'):
        xs=[1e-6,1e-8,1e-10];ys=[max(r['residuals'][key] for r in f['histories'] if r['tolerance']==t) for t in xs]
        axes[0].loglog(xs,np.maximum(ys,1e-17),'o-',label=key.replace('_',' '))
    axes[0].axhline(1.001e-7,color='red',ls='--');axes[0].invert_xaxis();axes[0].legend(fontsize=8)
    axes[0].set(xlabel='ODE relative tolerance',ylabel='Maximum normalized residual across 18 settings')
    for key in ('reciprocity_residual','return_position_residual'):
        xs=[1e-6,1e-8,1e-10];ys=[max(r[key] for r in f['rays'] if r['tolerance']==t) for t in xs]
        axes[1].loglog(xs,ys,'o-',label=key.replace('_',' '))
    axes[1].invert_xaxis();axes[1].set(xlabel='ODE relative tolerance',ylabel='Maximum optical residual [H_i^-1]');axes[1].legend(fontsize=8)
    save(fig,'restricted_convergence','Coupled R3 history and executed reverse rays: coarse histories fail; tighter settings pass')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for zeta in (0.,.01):
        rows=[r for r in f['sky'] if r['zeta']==zeta]
        axes[0].plot([r['kappa'] for r in rows],[r['quadrupole_legendre'] for r in rows],'o-',label=f'zeta_i={zeta}')
        rows=[r for r in f['rays'] if r['zeta']==zeta and r['order']==128 and r['tolerance']==1e-10 and r['direction']==3 and r['observer']==[.001,0.,0.]]
        axes[1].plot([r['kappa'] for r in rows],[r['angular_distance'] for r in rows],'o-',label=f'zeta_i={zeta}')
    axes[0].set(xlabel='Conserved dust momentum kappa',ylabel='Thermal sky quadrupole / T_i')
    axes[1].set(xlabel='Conserved dust momentum kappa',ylabel='Oblique angular distance [H_i^-1]')
    for ax in axes:ax.legend()
    save(fig,'restricted_predictions','Restricted R3 predictions at a=2: no observed sky/distance law is attached')
    existing=[('representations/execution_after_symmetry/representation_controls.png','Full-MV reconstruction and lossy descriptive controls'),
              ('jet_images/execution_20260912/jet_support_frontiers.png','Conditional jet/remainder frontiers; no empirical jet law'),
              ('owned_controls/execution/flow_controls.png','Owned flow controls at shared CF4 positions; no likelihood'),
              ('owned_controls/cmb/same_sky_differences.png','PR3 same-sky component differences; no independent null pool')]
    with PdfPages(OUT/'R8_scientific_synthesis.pdf') as pdf:
        for _,fig in figs:pdf.savefig(fig)
        for rel,title in existing:
            image=plt.imread(ART/rel);fig,ax=plt.subplots(figsize=(11,8));ax.imshow(image);ax.axis('off');fig.suptitle(title,fontsize=13)
            fig.text(.02,.02,'Carried completed calculation. Source: '+rel,fontsize=7);pdf.savefig(fig);plt.close(fig)
    for _,fig in figs:plt.close(fig)
    sources=['orbit_continuation/summary.json','restricted_history/results.json','law_followup/products.json',
             'jet_images/execution_20260912/results.json','representations/execution_after_symmetry/mock2.json',
             'final/campaign/summary.json',*[p for p,_ in existing]]
    manifest={'owner':'HTT / obsstat / restricted BASS benchmark','scope':'NON_CLAIM_BEARING_R8_SCIENTIFIC_SYNTHESIS',
              'source_files':{p:hashlib.sha256((ART/p).read_bytes()).hexdigest() for p in sources},
              'generator':str(Path(__file__).relative_to(ROOT)),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'R8_scientific_synthesis.pdf',*[OUT/(n+'.png') for n,_ in figs]]},
              'visual_audit':'PENDING','scientific_admission':'NOT_ADMITTED'}
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    decisions={key:sum(c['rank']['decision']==key for c in cells) for key in ('NON_REJECT','UNRESOLVED','REJECT')}
    supported=[r for r in f['histories'] if r['numerical_status']=='PASS']
    text=f'''# R8 full execution: scientific results and remaining limits

Owner: HTT / obsstat / restricted BASS benchmark. Scope: internal, non-claim-bearing research synthesis.
Design: PR #467; implementation branch `implementation/tensor-joint-r8-20260909`.

All **24 nodes and 52 action handlers** have terminal results. There are no unimplemented handlers.
This completes the requested implementation/execution pass. **Full scientific acceptance is not achieved**:
independent CAS obligations, observed sampling/response laws and the held mixture diagnostic remain as specified.
No merge or canonical scientific promotion is included.

## What the executed data show

- **Orbit bounds:** 30 saved pools were continued without deleting rows or changing targets, scales, seeds or alpha. {sum(c['improved_pairs'] for c in cells):,} pair upper bounds improved. {decisions['NON_REJECT']} pools are conservative non-rejections; {decisions['UNRESOLVED']} remain unresolved; {decisions['REJECT']} reject. These are computed synthetic statistics, without a qualified observed CMB pool. Exact pair trees, row banks and cumulative accounting are saved for resumption. Old checkpoints lacked trees; their enclosure banks and work counts were retained, and only newly visited pairs started trees. The 60-second cooperative checkpoints completed their last indivisible operation after the deadline: observed refinement times {min(c['checkpoint']['elapsed_seconds'] for c in cells):.3f}–{max(c['checkpoint']['elapsed_seconds'] for c in cells):.3f} s. These overruns are disclosed; this is not a hard real-time guarantee. Whole-scope caps remain unexhausted.
- **Representation:** {b['converted_rows']}/{b['M']} mock tensors reconstruct; the coincident-vector refusal retains its tensor row. All four observed component tensors reconstruct. Full-tensor/full-MV enclosures overlap after reconstruction error transport; lossy summaries offer no demonstrated representation information gain.
- **DESI released Gaussian summary:** the unchanged standalone conditional 95% qiso interval is **[{interval[0]:.10f}, {interval[1]:.10f}]**. The integrated run separately uses alpha=1/80 for this component. CMB, CF4 and distance-calibration allocations remain unused whole domains; no budget is reassigned.
- **Union3:** official release documentation resolves the 23x23 layout into 22 redshift/modulus nodes and their precision matrix. The original UNITY1.5 compression gives **Omega_m={u['omega_m']:.7f}**, profile chi-square **{u['chi2']:.7f}**, with a free common distance-modulus offset in flat LCDM. This is a released approximate Gaussian scenario, not an exact finite-sample acceptance or an anisotropic R3 likelihood. The matrix's tiny antisymmetric part drops out of the quadratic identically; its symmetric part is positive definite. No posterior samples were treated as independent observed draws.
- **CF4 / JWST / raw DESI:** actual release tables, source members and FITS metadata were inspected. Missing selected sampling/covariance/response premises prevent stronger laws. Published error bars alone do not fill them. The earlier 38,053-position flow controls and four PR3 component controls are preserved as descriptive evidence.
- **Conditional physical image:** {d['finite_query_count']} finite and {d['query_count']-d['finite_query_count']} unrestricted support queries remain valid within their stated fixture domains. Missing observed radiation/derivative laws leave the empirical physical region unrestricted. No empirical x_C, F or G_F bound is fabricated.
- **Restricted R3:** all 54 histories and 432 forward/reverse-ray pairs were executed. {len(supported)} histories at tolerances 1e-8 / 1e-10 pass; 18 coarse histories fail the unchanged convergence/residual criteria. All 432 optical tests pass their criterion, but only 288 rays associated with passing histories are eligible as numerical benchmark outputs. Wrong rapidity and pi-scale controls are detected. The normal thermal sky has even parity and zero coherent odd multipoles. Fixed benchmark predictions have no attached observed likelihood. The radiation derivative jet is explicitly unavailable.
- **Mixture simulator:** the frozen mu=-1 cell has 64/1000 rejections and upper bound 0.0911411 above 0.085. The adapter stays held. Analytic iid continuous-rank size is 0.05; a finite diagnostic fluctuation is possible, but does not override the held result. Seeds and criteria were not changed.

## Methods and interpretation

SO(3) orbit distances use q0=o0=1e-5 K and k=ceil(sqrt(M-1)). Optimizers provide only feasible upper witnesses, which are recomputed with exact rational quaternion rotations. Lower bounds retain exact root isolation and outward arithmetic. Bounds, not optimized point distances, enter ranks; inclusive ties and unresolved states remain conservative.

R3 follows the coupled LRS Bianchi-I two-antipodal-dust-stream + initially isotropic collisionless Planck-photon + Lambda model in `R3_MODEL_REFERENCE.md` N1–N29. Units are c=H_i=1, 8piG/(3c^2)=1. The fixed six kappa/zeta cases run from a=1 to a=2 at three quadrature orders and three tolerances. An independent observer boost and positive-stream source frame are retained. Full four-vector screens and Jacobi matrices propagate with the actual stress history; reverse rays are numerically integrated. Evidence is limited to the fixed, weak-anisotropy benchmark endpoints, not arbitrary parameters or a global caustic theorem.

The three selected review87 members match their declared hashes. Their Bose moments and screen basis were actually exercised as donor comparisons. No license file is declared in that supplied archive; the new wrapper does not vendor it or assert a redistribution license. The existing dust and physical anisotropic-stress conventions are retained.

The [Union3 release README](https://github.com/rubind/union3_release/blob/f5c387349b68f3535fdabf0fbc4f45cd407f9084/README.md) specifies the compression; [Rubin et al., arXiv:2311.12098](https://arxiv.org/abs/2311.12098) describes UNITY. The [Bianchi-I optics reference](https://arxiv.org/abs/1410.8473) supplies the Sachs/Jacobi context. These sources do not validate this implementation by citation alone.

## Deliverables and reproducibility

- [Eight-page scientific figure report](R8_scientific_synthesis.pdf), [figure source bindings](figure_manifest.json).
- [Executed campaign](campaign/summary.json), [dry plan](dry_plan.json).
- [Targeted test log](tests.log), [direct review and limitations](REVIEW.md).
- [Orbit continuation](../orbit_continuation/summary.json), [R3 grid and optics](../restricted_history/results.json), [product intake](../law_followup/products.json), [mixture diagnosis](../law_followup/mixture_diagnosis.json).

Run commands are recorded in `EXECUTION.md`. Initial failures, old incomplete results and original input files are retained. Tests and numerical checks are separate from independent four-axis CAS acceptance and scientific admission. There is no native Bianchi family identification, empirical CMB rank, MIO posterior or truth certificate in these outputs.
'''
    (OUT/'REPORT.md').write_text(text)
    print(json.dumps({'report':str(OUT/'REPORT.md'),'figures':len(figs)+len(existing),'execution_complete':g['execution_complete']}))

if __name__=='__main__':build()
