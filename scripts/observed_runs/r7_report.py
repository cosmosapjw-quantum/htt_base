"""Figures and manuscripts from actual R7 result records only."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import numpy as np
from scripts.observed_runs.run_r7_campaign import _write,_sha


def render_figures(directory,results):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    figures=[];unavailable=[]
    def save(fig,name,caption,nodes):
        fig.tight_layout();path=directory/(name+'.png');fig.savefig(path);plt.close(fig)
        figures.append({'path':str(path),'sha256':_sha(path),'caption':caption,'result_nodes':nodes,
            'source_result_files':[r.evidence[0] for i,r in results.items() if i in nodes and r.evidence],
            'visual_review':'PENDING','owner':'HTT/MIO projection consumer','scope':'see caption'})
    carrier=results.get('R7-06')
    arms=carrier.product_results.get('carriers',{}).get('arms',{}) if carrier else {}
    if arms:
        fig,axs=plt.subplots(1,2,figsize=(9,3.5))
        for name,arm in sorted(arms.items()):
            with np.load(arm['artifact'],allow_pickle=False) as z:
                fb=z['f_B'];q=z['Q'];o=z['O']
                axs[0].hist(fb[1:],bins=np.linspace(0,1,21),density=True,histtype='step',label=name)
                axs[1].scatter(np.linalg.norm(q[1:],axis=(1,2))*1e6,np.sqrt(np.sum(o[1:]**2,axis=(1,2,3)))*1e6,s=3,alpha=.35,label=name)
                axs[1].scatter(np.linalg.norm(q[0])*1e6,np.linalg.norm(o[0])*1e6,c='black',marker='*',s=90)
        axs[0].axvline(next(iter(arms.values()))['observed_f_B'],c='black',ls='--',label='observed carrier')
        axs[0].set(xlabel='response projection fraction $f_B$',ylabel='pool density',title='Descriptive finite pools')
        axs[1].set(xlabel=r'$\|Q\|$ ($\mu$K)',ylabel=r'$\|O\|$ ($\mu$K)',title='Full tensor amplitudes retained')
        axs[0].legend(fontsize=8);axs[1].legend(fontsize=8)
        save(fig,'cmb_full_tensors','PR3 measured carrier and finite FFP10 pools. Recomputed from orthonormal real harmonics. Pool densities are descriptive; no exchangeability p-value.', ['R7-06'])
    else:unavailable.append('Full tensor/packet comparison: no CMB carrier')
    shape=results.get('R7-11')
    if shape and shape.product_results.get('pools'):
        fig,axs=plt.subplots(1,2,figsize=(9,3.2))
        for ax,(name,pool) in zip(axs,sorted(shape.product_results['pools'].items())):
            d=json.loads(Path(pool['artifact']).read_text());intervals=np.asarray(d['score_intervals'])
            ax.plot(intervals[:,1],lw=.8);ax.axhline(0,c='black',lw=.8)
            ax.set(xlabel='original row index (observed = 0)',ylabel='kNN distance upper bound',title=f'{name}: {pool["resolved_rows"]}/{pool["rows"]} resolved')
        save(fig,'orbit_intervals','Complete row-symmetric SO(3) score intervals. Lower bounds are zero under the registered resource policy; exact outlier ranks remain unresolved. q0=o0=1e-5 K.', ['R7-11'])
    if shape and shape.product_results.get('pools'):
        fig,axs=plt.subplots(1,2,figsize=(9,3.3));statuses={}
        for name,pool in sorted(shape.product_results['pools'].items()):
            path=pool.get('packet_recovery_artifact')
            if not path:continue
            rows=json.loads(Path(path).read_text());good=[r for r in rows if r['status']=='RECONSTRUCTED']
            statuses[name]={state:sum(r['status']==state for r in rows) for state in {r['status'] for r in rows}}
            axs[0].hist([np.log10(r['condition']) for r in good],bins=20,histtype='step',label=name)
            axs[1].scatter([r['condition'] for r in good],[max(r['packet_replay_error'],1e-20) for r in good],s=4,alpha=.5,label=name)
        axs[0].set(xlabel='log10 Krylov condition',ylabel='row count');axs[0].legend(fontsize=8)
        axs[1].set(xscale='log',yscale='log',xlabel='Krylov condition',ylabel='16-contraction replay norm')
        save(fig,'packet_recovery','Actual full-carrier chart/reconstruction replay. Every sample ID, failed and unavailable chart is retained in the source artifact. Error plot floors exact zero at 1e-20 for display only; no physical inference.', ['R7-11'])
    thermal=results.get('R7-04');responses=thermal.product_results.get('thermal_responses',[]) if thermal else []
    from common.r7_contracts import json_value
    responses=json_value(responses)
    if responses:
        beta=np.array([r['beta'][2] for r in responses]);a20=np.array([r['retained'][0] for r in responses])
        fig,ax=plt.subplots(figsize=(6,3.3));ax.plot(beta,a20*1e6,'o-',label='finite thermal fit')
        ax.plot(beta,2.7255*beta**2*(2/3)*np.sqrt(4*np.pi/5)*1e6,'--',label='leading monopole quadrupole')
        ax.set(xlabel='beta along z',ylabel='real a20 (microK)',title='Positive 2.7255 K monopole; simultaneous ell0..5 fit');ax.legend(fontsize=8)
        save(fig,'thermal_response','Declared absolute-temperature scenario at NSIDE64. Finite pullback followed by simultaneous fit; released component processing/covariance remains unqualified.', ['R7-04'])
    if 'R7-21' in results:
        G=np.linspace(0,1,101);information=G/(1+G)
        fig,ax=plt.subplots(figsize=(6,3.2));ax.plot(G,information);ax.plot([.25],[.2],'o')
        ax.set(xlabel='independent nuisance calibration information G',ylabel='efficient theta information',title='U=V=E=1: exact scalar Schur complement')
        save(fig,'calibration_information','Declared scalar Fisher scenario. At G=1/4, efficient information is 1/5. No measured CF4/JWST shared-calibration link is asserted.', ['R7-21'])
    source=results.get('R7-12');data=source.product_results if source else {}
    if 'H0_H3_regions' in data:
        regions=data['H0_H3_regions'];fig,ax=plt.subplots(figsize=(7,3.1))
        for i,name in enumerate(('H0','H1','H2','H3')):
            r=regions[name].get('region')
            if r is None:ax.annotate('all real theta (unbounded)',(0,i),ha='center')
            else:ax.plot(r,[i,i],lw=6,solid_capstyle='butt');ax.plot(r,[i,i],'|',ms=13,c='black')
        ax.set(yticks=range(4),yticklabels=['H0 unrestricted','H1 bounded','H2 marginalized','H3 joint measured'],xlabel=r'accepted $\theta$ (scenario units)',title='95% compatible sets under four different laws',xlim=(-3,5),ylim=(-.5,3.5))
        save(fig,'high_source_regions','Fixed scalar scenario y=1, z=0.25. H0 quotient, H1 union over |h|<=1, H2 Gaussian marginal, H3 projection of full rank-two joint acceptance. Different laws and coverage targets remain explicit.', ['R7-12'])
    if 'finite_mask' in data:
        d=data['finite_mask'];fig,axs=plt.subplots(1,2,figsize=(8,3.3))
        axs[0].loglog(d['mask_fraction'],d['singular_value'],label='one-column singular value')
        axs[0].loglog(d['mask_fraction'],d['T5_norm_bound'],ls='--',label='analytic norm bound')
        axs[0].legend(fontsize=8);axs[0].set(xlabel='soft mask fraction f',ylabel='operator norm')
        axs[1].loglog(d['mask_fraction'],d['unit_displacement_minimum_cost']);axs[1].set(xlabel='soft mask fraction f',ylabel='unit image-displacement cost')
        save(fig,'mask_cost','Finite-band axial Y70 scenario, m=t(1+mu)^2/4. Numerical polynomial quadrature; no certified binary64 quadrature enclosure. Cost direction is along the one-column image, and unsupported directions cost infinity.', ['R7-12'])
    if 'MES_scenarios' in data:
        d=data['MES_scenarios'];fig,axs=plt.subplots(1,2,figsize=(8,3.3))
        axs[0].plot(d['rate_parameter_per_s'],d['normalized_shear_norm']);axs[0].set(xlabel='declared Q time-derivative rate (1/s)',ylabel=r'$\|\sigma/\Theta\|$',title='Same Q, different admitted jets')
        projection=d['same_state_GF'];outer=projection.outer_bounds if hasattr(projection,'outer_bounds') else projection['outer_bounds']
        inner=projection.inner_values if hasattr(projection,'inner_values') else projection['inner_values']
        axs[1].plot(outer,[0,0],lw=5,label='certified box outer range');axs[1].plot(inner,[0]*len(inner),'o',label='feasible same-state witness')
        axs[1].set(xlabel='signed GF scenario functional',yticks=[],title='Outer range and inner witness');axs[1].legend(fontsize=8)
        save(fig,'mes_same_state','First-order radiation-jet scenario and exact affine positive-denominator box relaxation. Supplied derivatives are assumptions; no physical MES bound is inferred from the observed CMB.', ['R7-12'])
    stress=results.get('R7-18');cells=stress.product_results.get('operational_cells',()) if stress else ()
    if cells:
        fig,axs=plt.subplots(1,2,figsize=(10,3.5));x=np.arange(len(cells));v=np.array([c['coverage'] for c in cells]);ci=np.array([c['coverage_CP99'] for c in cells])
        axs[0].errorbar(x,v,yerr=np.array([v-ci[:,0],ci[:,1]-v]),fmt='o',ms=3,capsize=2)
        axs[0].axhline(.94,c='black',ls='--');axs[0].set(ylim=(.925,1.01),ylabel='coverage; 99% CP interval',xlabel='registered cell index')
        vals=np.array([c.get('FPR',c.get('power')) for c in cells]);rci=np.array([c['rejection_CP99'] for c in cells])
        axs[1].errorbar(x,vals,yerr=[vals-rci[:,0],rci[:,1]-vals],fmt='o',capsize=3);axs[1].set(xlabel='registered cell index',ylabel='FPR (null) / power (alternative)',ylim=(-.02,1.02))
        save(fig,'gaussian_calibration','10000 independent trials per declared cell. Exact Gaussian law stress only; no transfer to PR3 data. Cells include mirror alternatives, singular support and rank zero; refusal rates are reported in the source record.', ['R7-18'])
    depth=results.get('R7-14');d=depth.product_results if depth else {}
    if 'z' in d:
        fig,axs=plt.subplots(1,2,figsize=(8,3.3));fo=np.asarray(d['observer_kernel']);fg=np.asarray(d['source_kernel']);z=np.asarray(d['z'])
        axs[0].plot(z,fo,label='observer');axs[0].plot(z,fg,label='source');axs[0].legend();axs[0].set(xlabel='redshift',ylabel='distance kernel for v/c')
        # Same local linear design, full rank spectrum and explicit constant nuisance projection.
        design=np.column_stack((fo,fg));projected=design-design.mean(axis=0)
        axs[1].plot([1,2],np.linalg.svd(design,compute_uv=False),'o-',label='before nuisance')
        axs[1].plot([1,2],np.linalg.svd(projected,compute_uv=False),'s--',label='after constant nuisance');axs[1].set(yscale='log',xticks=[1,2],xlabel='singular direction',ylabel='unweighted singular value');axs[1].legend(fontsize=8)
        save(fig,'depth_response','Flat FLRW Omega_m=.3,H0=70 low-speed scenario. Singular spectra use the declared unweighted design and a constant nuisance; these are not measured catalogue information.', ['R7-14'])
    jwst=results.get('R7-09');groups=jwst.product_results.get('jwst',()) if jwst else ()
    if groups:
        fig,axs=plt.subplots(1,len(groups),figsize=(10,3.5));axs=np.atleast_1d(axs)
        for ax,d in zip(axs,groups):
            v=np.asarray(d['delta_mag']);ax.plot(np.arange(len(v)),v,'o');ax.axhline(0,c='black',lw=.8)
            ax.axhline(d['scenario_fitted_offset_mag'],ls='--');ax.set(title=d['dataset'],xlabel='source host order',ylabel='method A - method B (mag)')
        save(fig,'jwst_host_contrasts','Source-member-verified host differences. Dashed offsets assume independent quoted Gaussian errors; shared covariance is unprovided, so these are scenario fits and no geometry amplitude is identified.', ['R7-09'])
    observed=results.get('R7-19');scopes=observed.product_results.get('scope_results',()) if observed else ()
    if scopes:
        d=scopes[0];fig,ax=plt.subplots(figsize=(6,2.8));ci=d['qiso_CI95'];q=d['data_estimate_qiso']
        ax.errorbar(q,0,xerr=[[q-ci[0]],[ci[1]-q]],fmt='o',capsize=7);ax.axvline(1,c='black',ls='--')
        ax.set(xlabel='released BAO qiso',yticks=[],title='DESI BGS compressed Gaussian model: conditional 95% interval')
        save(fig,'desi_conditional_qiso','Official syst compressed likelihood, one scalar datum and its released covariance/window. Confidence is conditional on the fixed released Gaussian summary law; true raw-catalogue coverage and anisotropic response are unverified.', ['R7-19'])
    manifest=directory/'figure_manifest.json';_write(manifest,{'figures':figures,'unavailable':unavailable})
    return {'figures':figures,'unavailable_figure_roles':unavailable,'manifest':str(manifest),'render_status':'EXECUTED','visual_audit':'PENDING'}


def _escape(value):
    s=str(value)
    math_fragments={'|h|<=1':r'$|h|\leq1$', 'm=t(1+mu)^2/4':r'$m=t(1+\mu)^2/4$',
        'Omega_m=.3,H0=70':r'$\Omega_m=0.3,\ H_0=70$'}
    for i,key in enumerate(math_fragments):s=s.replace(key,f'R7MATHTOKEN{i}')
    for a,b in [('\\',r'\textbackslash{}'),('_',r'\_'),('%',r'\%'),('^',r'\textasciicircum{}'),('&',r'\&'),('#',r'\#')]:s=s.replace(a,b)
    for i,value in enumerate(math_fragments.values()):s=s.replace(f'R7MATHTOKEN{i}',value)
    return s


def write_manuscript(directory,results):
    figures=results.get('R7-22').product_results.get('figures',[]) if results.get('R7-22') else []
    scopes=[s for r in results.values() for s in r.product_results.get('scope_results',[]) if r.node_id=='R7-19']
    paths=[]
    methods=r'''\documentclass[11pt]{article}
\usepackage[margin=24mm]{geometry}\usepackage{amsmath,amssymb,graphicx,booktabs,hyperref}
\title{Full-tensor observation laws and conditional physical regions: the R7 workstation implementation}
\author{HTT research programme}\date{Workstation execution, September 2026}
\begin{document}\maketitle
\begin{abstract}
We implement a full quadrupole--octupole carrier, a repaired constructive orbit decoder, Gaussian acceptance with exact singular support, four high-source nuisance experiments, and same-state projection machinery. We distinguish implemented algebra and declared scenario laws from empirical likelihood qualification. The implementation preserves unavailable providers and numerically unresolved distances as terminal outcomes. A separately reported DESI compressed background comparison uses the released Gaussian summary model. It does not identify anisotropic geometry.
\end{abstract}
\section{Representation and constructive contribution}
Let $Q\in\mathrm{STF}_2(\mathbb R^3)$ and $O\in\mathrm{STF}_3(\mathbb R^3)$ retain their absolute Galactic frame, with amplitudes in kelvin. For orthonormal real harmonics,
\begin{equation}Q:Q=\frac{75}{8\pi}C_2,\qquad O:O=\frac{245}{8\pi}C_3.\end{equation}
Stored complex coefficients map to the real cosine/sine layout with factors $\sqrt2$ and $-\sqrt2$. Multipole-vector representations already retain harmonic shape information \cite{land}. The project contribution is the bound implementation of the packet image check, its failure-preserving conversion, and the common law/region interfaces; no priority claim is made for standard representation theory.
For fixed unit $q$, write $L_qo=o:q$ and $M_q=I+6q^2/5$. Then
\begin{equation}L_qL_q^*=M_q/3,\quad R_q=3L_q^*M_q^{-1},\quad o=R_qv+\sqrt{1-3v^TM_q^{-1}v}\,u,\quad u\in S(\ker L_q).\end{equation}
The interior fibre has an $S^3$ freedom. Power and contraction therefore do not recover the full tensor. The repaired Q donor rejects a packet with only its ten trilinears negated; the original H target failure and repaired-target test are retained as separate execution evidence.
The all-strata quotient distance minimizes $[\|Q-RQ'R^T\|^2/q_0^2+\|O-R^{\otimes3}O'\|^2/o_0^2]^{1/2}$ over proper rotations. A cover radius $\delta$, scalar error enclosure $e$, and Lipschitz constant $L$ give lower bound $\max(0,d_{\rm grid}-L\delta-e)$ and upper bound $d_{\rm grid}+e$. Local optimization improves only a feasible upper bound. We fix $q_0=o_0=10^{-5}$ K and $k=\lceil\sqrt N\rceil$ for the full symmetric pool. Unresolved intervals do not yield an exact rank. The practical large-pool resource policy retains an identity upper bound for every pair and returns unresolved rows.
The scalar response projection $f_B$ has ideal conditional law $\mathrm{Beta}(3/2,2)$ only for independent spherical Gaussian octupoles and nonzero $Q$. Its CDF is $5x^{3/2}/2-3x^{5/2}/2$, with mean $3/7$. This law is not assigned to the masked PR3 pool.
\section{Known-law confidence and nuisance experiments}
For $Y\sim N(\mu(\theta),C)$ with known fixed positive-semidefinite covariance of rank $r$, retain the support condition and accept
\begin{equation}Y-\mu(\theta)\in\mathrm{im}(C),\qquad (Y-\mu)^TC^+(Y-\mu)\leq\chi^2_{r,0.95}.\end{equation}
At the true parameter the whitened residual has $r$ independent standard normal coordinates. Inverting this acceptance event over the physical domain has at least 95\% coverage, including rank-zero deterministic observations. Parameter fitting does not subtract Wilks degrees of freedom. Uncertain numerical rank is unresolved; a pseudoinverse does not discard an off-support residual. Gaussian conditioning retains the complete cross-covariance, and differentiation includes the derivative of its gain matrix. No posterior is substituted for confidence; a proper prior would define a separate model.
H0 quotients unrestricted deterministic high-source response. H1 unions the known-noise acceptance region over a bounded ellipsoid and an optional positive-sky intersection. H2 marginalizes a declared Gaussian source law including its normalization. H3 uses a full joint measurement law for low and measured high modes. The centre radius $\rho$ and pairwise overlap radius $2\rho$ answer different questions. A displacement outside the response image has infinite cancellation cost.
For a finite source band and mask $w=1-m$, let $f=(4\pi)^{-1}\int m$, $G=I-E$ and $E=\int myy^T$. The addition theorem gives $\|E\|\leq36f$. For $f<1/36$,
\begin{equation}\|K_w\|\leq\frac{c_Lf}{1-36f},\quad \min_{K_wh=d}\|h\|^2\geq\frac{\|d\|^2(1-36f)^2}{c_L^2f^2},\quad c_L=\|C_{\rm ret}\|4\pi\sqrt{36/(4\pi)}\sup_n\|g(n)\|.\end{equation}
The proof uses the finite-band supremum and inverse-Gram norm. It neither interchanges the infinite-band limit nor certifies pixel error. Our soft-mask numerical polynomial oracle is shown separately. Four CAS axes executed one shared contract for seven elementary/certificate implications, including the accepted rational L=10 minors. The historical continuum operator itself was not recomputed on four axes.
\section{Physical closure and same-state projections}
Use $\Theta=3H>0$, positive absolute temperature, geodesic collisionless radiation and first order about isotropy. An outward sky direction is opposite to photon propagation; all odd moments and their derivatives change sign together. Brightness moments have factors $4/3$, $8/15$, $8/35$. For normalized $q=Q/\bar T$, retain $\dot q=\dot Q/\bar T-Q\dot{\bar T}/\bar T^2$ before taking norms. The implementation evaluates tensor T3 equations only with supplied jets. An observed low-multipole sky does not supply those derivatives.
A joint accepted physical state is the input to every norm, orientation and registered signed GF functional. Exact affine positive-denominator box routines provide outer relaxations and feasible witnesses separately. Without a certified nonlinear bound provider, outer ranges remain unresolved. A ratio with unproved denominator positivity remains undefined/unresolved.
For regular nuisance Fisher block $E>0$, independent calibration information $G\succeq0$ changes efficient information by $V[E^{-1}-(E+G)^{-1}]V^T$. The scalar oracle with noise variances 1 and 4 gives information $1/5$. This does not justify an unobserved cross-probe calibration link.
\section{Execution and limitations}
Every eligible node executes or records a terminal limitation. The source tree begins at design commit 89a9a901, with selected Q/P/A/D/B files; old publication-wrapper failures are preserved separately from numerical validation. The native adapter is unavailable. Exact review87 source members and actual external reference modes are absent, so the restricted R3 physical adaptation and external physical validation were not executed. The existing bounded provider interface is not an implemented anisotropic Boltzmann solver.
The Gaussian operational cells use 10,000 independent trials each and 99\% Clopper--Pearson intervals. The confidence lower-bound gate is .94 and null FPR upper-bound gate .06. These stress experiments do not calibrate a real product by transfer. PR3 full tensors and WMAP9 controls remain descriptive. CF4 lacks its bound full group covariance. JWST host contrasts retain method and host distinctions; assumed independent-error fits are scenario results. Compressed DESI is a separate background law, and no raw-catalogue PR151 result is consumed. PR4/NPIPE is excluded.
R1/R2/A1 are mapped to the representation/fibre, finite-response and mask error, four nuisance laws, physical derivative premises, complete pool refusal, calibration and separate data report. Full multipole-vector ablation and generic non-Gaussian simulator calibration are not implemented. The empirical full-orbit anomaly comparison is also unexecuted: its product sampling law and required numerical rank precision are unavailable. Conditional MES figures use declared jets and do not establish an observed physical bound. These limitations delimit the current implementation rather than reject a physical hypothesis.
\section{Generated figures}
'''
    for f in figures:
        if Path(f['path']).stem in {'high_source_regions','mask_cost','mes_same_state','gaussian_calibration','depth_response'}:
            methods+='\\begin{figure}[ht]\\centering\\includegraphics[width=.93\\linewidth]{'+f['path']+'}\\caption{'+_escape(f['caption'])+'}\\end{figure}\n'
    methods+=r'''\clearpage\section{Code and data availability}
This is a local implementation, with source manifests, preserved execution logs and per-node attempts. Public data release identities are bound to selected local products; private workstation paths are not a public data release. Reproduction uses the campaign CLI with its pinned design DAG and an existing compatible Python environment. Optional MLflow tracing is disabled by default and cannot alter scientific outcomes. No remote publication or merge is implied.
\begin{thebibliography}{9}
\bibitem{land} K. Land and J. Magueijo, The Multipole Vectors of WMAP, and their frames and invariants, arXiv:astro-ph/0502574 (2005).
\bibitem{boost} J. Chluba and A. Ravenni, Boost operator approach to the relativistic SZ effect, MNRAS 547, stag240 (2026), doi:10.1093/mnras/stag240. General spectral boost operators are prior work; this implementation uses a restricted thermal pullback.
\end{thebibliography}\end{document}
'''
    tex=directory/'methods.tex';tex.write_text(methods);paths.append(str(tex))
    report=['# R7 integrated-data results','', 'This report is generated from actual terminal records. Confidence statements are conditional on each named law. No native-family or integrated anisotropic-geometry inference is supported.','']
    for s in scopes:
        report+=['## DESI compressed background likelihood','',f"qiso = {s['data_estimate_qiso']:.8f}; conditional 95% confidence interval {s['qiso_CI95']}.",
            f"DV/rd = {s['DV_over_rd']:.8f}; conditional interval {s['DV_over_rd_CI95']}.",s['scope_limit'],'']
    report+=['## Data partitions','']
    for i in ('R7-06','R7-07','R7-08','R7-09','R7-10','R7-19'):
        if i in results:report+=[f"- {i}: {results[i].scientific_outcome}; capabilities: {', '.join(results[i].capabilities) or 'none'}."]
    report+=['','## Remaining work','', 'A product-qualified full tensor likelihood, precise full-orbit pool ranks, full CF4 covariance, shared JWST calibration covariance, and supplied physical-provider channels remain unavailable or unresolved. Provider stubs are not counted as implemented physics.']
    md=directory/'integrated_data_results.md';md.write_text('\n'.join(report)+'\n');paths.append(str(md))
    proc=subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error',tex.name],cwd=directory,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=directory/'latexmk.log';log.write_text(proc.stdout);paths.append(str(log))
    pdf=directory/'methods.pdf'
    if proc.returncode==0 and pdf.exists():paths.append(str(pdf))
    return {'build_status':'PASS' if proc.returncode==0 and pdf.exists() else 'FAIL','artifacts':paths,
        'scope':'Methods/scenarios with separate conditional compressed-data result; pending independent audit status retained',
        'review_status':results['R7-23'].product_results.get('independent_review',{}).get('status','NOT_EXECUTED')}
