"""Summarize the completed R64 carriers without refitting or selecting models."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def run(root):
    root=Path(root).resolve()
    sys.path[:0]=[str(root/'htt'),str(root/'htt/src')]
    from htt.htt.infer import r64_directional_hubble as dh
    base=root/'docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117'
    path=base/'RESULTS/OBSERVED/DIRECTIONAL_HUBBLE_RESULT.json'
    r=json.loads(path.read_text())
    cp=base/'RESULTS/OBSERVED/DIRECTIONAL_HUBBLE_CARRIERS.npz'
    a=np.load(cp,allow_pickle=False)
    rows=[]; witnesses={}; exemplars={}
    for key,m in r['models'].items():
        name, degree=key.rsplit('__J',1);degree=int(degree)
        maps=m['directional_maps']
        valid=[v for v in maps if v['z_index']!=1]
        held=m['internal_predictive']
        hp=[t['nominal_p'] for t in held if t['status']=='IDENTIFIED'] if isinstance(held,list) else []
        hcounts=dict(Counter(v['radial_ratio_region']['status'] for v in valid))
        qcounts=dict(Counter(v['q_region']['status'] for v in maps))
        theta=a[key+'__estimate']
        ident=m['depth_eta_image']['identified']
        supported=m['depth_eta_image']['intervals']
        excludes0=[i for i,v in enumerate(supported) if v['identified'] and (v['lower']>0 or v['upper']<0)]
        angular_excludes=[i for i in excludes0 if i%9!=0]
        rows.append(dict(model=key,operator=name,degree=degree,rank=m['rank'],parameters=m['n_parameters'],
            residual_df=m['dof'],adequacy_p=m['adequacy_p'],radial_angular_p=m['angular_radial_null']['nominal_p'],
            radial_angular_df=m['angular_radial_null']['df'],Q95=m['angular_radial_null']['noise_reference_Q95'],
            H_ratio_status_nonreference=hcounts,q_status=qcounts,depth_coordinates_identified=sum(ident),
            depth_coordinates_total=len(ident),depth_simultaneous_intervals_excluding0=excludes0,
            angular_depth_intervals_excluding0=angular_excludes,
            holdout_p_range=[min(hp),max(hp)] if hp else None,
            l3_depth_bias_max=m['calibration']['omitted_l3_identified_depth_max_bias'] if sum(ident) else None,
            represented_calibration_error=m['calibration']['represented_identified_depth_max_error'],
            published_q_depth_shift_max=float(np.max(np.abs(m['published_chart']['depth_eta_shift']))),
            coherent_V_representative_km_s=theta[:3].tolist(),
            coherent_V_representative_norm_km_s=float(np.linalg.norm(theta[:3]))))
        if name=='log_mono' and degree in (1,2):
            exemplars[key]=[{**v,'direction_label':['+x','+y','+z','-x','-y','-z'][v['direction_index']]}
                            for v in maps if v['z_index']==3 and v['direction_index']<6]
        # A concrete nonlinear fibre witness is separate from the sufficient
        # ingredient-identification certificate. This is not a new fit.
        null=a[key+'__null_basis']
        if null.shape[1]:
            best=None
            for j in range(null.shape[1]):
                changed=theta+null[:,j]
                for ni,nn in enumerate(a['directions_ICRS']):
                    vals=[dh.point_image(th,z,nn,degree,r['Omega_m_reference'],r['H0_reference_km_s_Mpc'])
                          for th in (theta,changed) for z in (.08,.04)]
                    if any(v['status']!='OK' for v in vals):continue
                    rr0=vals[0]['H_D']/vals[1]['H_D'];rr1=vals[2]['H_D']/vals[3]['H_D']
                    dd=abs(rr1-rr0)
                    if best is None or dd>best['ratio_change_abs']:
                        best=dict(direction_index=ni,null_column=j,ratio_before=rr0,ratio_after=rr1,
                            ratio_change_abs=dd,q08_before=vals[0]['q_D'],q08_after=vals[2]['q_D'],
                            denominator_values=[v['denominator'] for v in vals],
                            whitened_mean_change_norm=float(np.linalg.norm(a[key+'__likelihood_factor']@null[:,j])),
                            parameter_displacement=null[:,j].tolist())
            witnesses[key]=dict(witness=best,scope='same finite compressed mean; positive distance derivative at the two evaluated redshifts/direction only; no full-lightcone geometry existence claimed')
    bydegree={}
    for j in (1,2,3):
        group=[v for v in rows if v['degree']==j]
        ps=[v['adequacy_p'] for v in group if v['adequacy_p'] is not None]
        ap=[v['radial_angular_p'] for v in group]
        bydegree[str(j)]=dict(adequacy_p_range=[min(ps),max(ps)] if ps else None,
            radial_angular_p_range=[min(ap),max(ap)],ranks=sorted(set(v['rank'] for v in group)),
            angular_signed_depth_sign_detections=sum(len(v['angular_depth_intervals_excluding0']) for v in group))
    out=dict(schema='htt.r64.interpretation/1',source_result_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_carrier_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),models=rows,degree_summary=bydegree,
        exemplars=exemplars,nonlinear_fibre_witnesses=witnesses,
        sources=dict(n=r['source_rows'],z_range=r['redshift_range'],source_sha256=r['source_carrier']['sha256']),
        observed_models=len(rows),operators=7,tests_passed=60,
        smooth_chart_max_eta_offset=r['smooth_reference_transport']['max_abs_raw_eta_offset'],
        interpretation='No added radial angular mean is required in these fixed-C low-order models after free coherent V and constant angular field. This does not exclude static anisotropy or establish physical isotropy.',
        resolution='J3 nulls are properties of this 36-row compression and mean family, not an intrinsic limit of the original CF4 catalogue.',
        interval_scope='Conservative supports of a common rank-r confidence region, not sharp profile-likelihood bounds; domain-certification failure does not by itself prove the exact nonlinear image unbounded.',
        publication_status='NOT_READY_TO_SUBMIT')
    (base/'RESULTS/INTERPRETATION_SUMMARY.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps(dict(degree_summary=bydegree,nonlinear_fibre_witnesses={k:None if v['witness'] is None else {q:v['witness'][q] for q in ('ratio_change_abs','whitened_mean_change_norm')} for k,v in witnesses.items()}),indent=2))

    # Standalone shareable research figure, with all operators and a declared
    # illustrative operator; no best-looking data-driven selection.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels=['raw log','method offsets','hemisphere split','survey offsets','radial nuisance','Galactic nuisance','error nuisance']
    names=list(dict.fromkeys(v['operator'] for v in rows))
    fig, axes=plt.subplots(1,3,figsize=(15,5.1),gridspec_kw={'width_ratios':[1.25,1,1.05]})
    for j,color,marker in ((1,'#2166ac','o'),(2,'#d6604d','s')):
        vals=[next(v for v in rows if v['operator']==name and v['degree']==j)['radial_angular_p'] for name in names]
        axes[0].plot(vals,np.arange(7)+(.1 if j==1 else -.1),marker=marker,color=color,ls='',label=f'J={j}')
    axes[0].set_yticks(np.arange(7),labels);axes[0].invert_yaxis();axes[0].set_xlim(0,1)
    axes[0].axvline(.05,color='gray',ls=':');axes[0].set_xlabel('Conditional radial-angular null p')
    axes[0].set_title('No added radial angular signal');axes[0].legend(frameon=False)
    for j,color,off in ((1,'#2166ac',-.12),(2,'#d6604d',.12)):
        ex=exemplars['log_mono__J'+str(j)]
        for i,v in enumerate(ex):
            q=v['radial_ratio_region']
            if q['status']=='OK':
                axes[1].errorbar(i+off,q['estimate'],yerr=[[q['estimate']-q['lower']],[q['upper']-q['estimate']]],fmt='o' if j==1 else 's',color=color,capsize=3)
            else:
                axes[1].text(i+off,50,'D?',ha='center',va='center',color=color,fontsize=9)
    axes[1].set_yscale('log');axes[1].set_xticks(range(6),['+x','+y','+z','-x','-y','-z'])
    axes[1].axhline(1,color='gray',ls=':');axes[1].set_ylabel('H_D(0.08,n) / H_D(0.04,n)')
    axes[1].set_ylim(.035,80);axes[1].set_title('Method-offset example: 95% enclosure')
    matrix=np.array([[next(v for v in rows if v['operator']==name and v['degree']==j)['rank'] for j in (1,2,3)] for name in names])
    im=axes[2].imshow(matrix,aspect='auto',vmin=20,vmax=39,cmap='Blues')
    for i in range(7):
        for jj,p in enumerate((21,30,39)):
            axes[2].text(jj,i,f'{matrix[i,jj]}/{p}',ha='center',va='center',color='black' if matrix[i,jj]<31 else 'white')
    axes[2].set_xticks(range(3),['J=1','J=2','J=3']);axes[2].set_yticks(range(7),labels)
    axes[2].set_title('Identified rank / coefficients')
    fig.suptitle('CF4 directional distance-rate evolution | fixed working covariance, free coherent velocity',fontsize=13)
    fig.text(.5,.015,'Intervals are conservative joint-region images. D? = denominator positivity not certified. J=3 nulls belong to the 36-row compression.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.045,1,.94))
    fig.savefig(base/'RESULTS/DIRECTIONAL_HUBBLE_SUMMARY.png',dpi=180)
    fig.savefig(base/'RESULTS/DIRECTIONAL_HUBBLE_SUMMARY.pdf')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.')
    run(p.parse_args().root)
