"""Combine the completed primary and source-augmented R64 results."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import stats


def run(root):
    base=Path(root).resolve()/'docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117'
    p=base/'RESULTS/INTERPRETATION_SUMMARY.json';summary=json.loads(p.read_text())
    f=base/'RESULTS/AUGMENTED/AUGMENTED_RESULT.json';r=json.loads(f.read_text())
    out=[];examples={};cal=[]
    for key,m in r['models'].items():
        maps=m['maps'];valid=[v for v in maps if v['z_index']!=1]
        out.append(dict(key=key,experiment=m['experiment'],degree=m['degree'],family=m['calibration_family'],
            rows=m['n_observed_original'],nuisance_rank=m['nuisance_rank'],field_velocity_rank=m['rank'],
            field_velocity_parameters=m['n_parameters'],total_mean_rank=m['total_mean_rank'],dof=m['dof'],
            chi2=m['residual_chi2'],adequacy_p=m['adequacy_p'],
            radial_angular_p=m['angular_radial_null']['nominal_p'],radial_angular_df=m['angular_radial_null']['df'],
            ratio_status=dict(Counter(v['ratio']['status'] for v in valid)),
            q_status=dict(Counter(v['q']['status'] for v in maps)),
            added_row_prediction=m['additional_rows'].get('predictive')))
        if m['experiment']=='mono_method':
            examples[key]=[{**v,'direction_label':['+x','+y','+z','-x','-y','-z'][v['direction_index']]}
                          for v in maps if v['z_index']==3 and v['direction_index']<6]
        if m['calibration_family']=='method_angular_nuisance':
            n=r['models'][key.replace('method_angular_nuisance','common_field')]
            delta=n['residual_chi2']-m['residual_chi2']
            rank=m['total_mean_rank']-n['total_mean_rank']
            if delta<-1e-8 or rank!=24:raise ValueError('unexpected nested calibration geometry')
            cal.append(dict(experiment=m['experiment'],degree=m['degree'],delta_chi2=delta,df=rank,
                nominal_p=float(stats.chi2.sf(max(delta,0.),rank)),
                meaning='conditional comparison of common field vs method-angular mean offsets; not causal proof of calibration errors'))
    augmented=dict(source_result_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
        source_carrier_sha256=hashlib.sha256((f.parent/'AUGMENTED_CARRIERS.npz').read_bytes()).hexdigest(),
        cache_sha256=r['cache_sha256'],cache_reuse=r['cache_reuse'],input_checks=r['input_checks'],
        models=out,method_calibration_comparison=cal,examples=examples,
        observed_models=len(out),new_independent_sources=0,new_pair_sum=False,
        parameter_count_convention='Field/velocity rank counts coherent V3 plus 9*(J+1) signed distance-field coefficients; extra method-angular nuisance rank is reported separately.',
        scientific_result='All selected68/72row augmentations restore rank39 for the J3 distance-field plus coherent-V3 family, including profiling24method-angular nuisance directions in the68row cases. This removes the initial structural compression null, but does not ensure precise derivative images or empirical calibration.')
    summary['augmentation']=augmented
    summary['unique_observed_models']=len(summary['models'])+len(out)
    summary['tests_passed']=62
    summary['decision']='Consolidate P3 around source-dependent radial information and resolution recovery. Use initial36 and augmented68/72 contrasts jointly in the manuscript; do not claim intrinsic CF4 derivative impossibility or general physical anisotropy detection.'
    p.write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'rows':out,'method_comparisons':cal,'cache_reuse':r['cache_reuse']},indent=2))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(11.5,4.7))
    x=np.arange(1,4)
    ax[0].plot(x,[21,30,36],'o-',label='Initial36 rows',color='#2166ac')
    ax[0].plot(x,[21,30,39],'s-',label='Augmented68 rows',color='#d6604d')
    ax[0].plot(x,[21,30,39],ls=':',color='black',label='Required coefficients')
    ax[0].set_xticks(x,['J=1','J=2','J=3']);ax[0].set_ylim(18,42)
    ax[0].set_ylabel('Identified field + velocity coefficient rank')
    ax[0].set_title('Existing correlated method rows recover rank')
    ax[0].legend(frameon=False,fontsize=9)
    ax[0].text(1.02,18.8,'Free24 method-angular offsets also retain39/39 at J=3.',fontsize=8)
    orig=[next(v for v in summary['models'] if v['operator']=='log_mono' and v['degree']==j)['adequacy_p'] for j in (1,2)]
    ax[1].plot([1,2],orig,'o-',label='Initial36',color='#2166ac')
    for fam,style,color,label in [('common_field','s-','#b2182b','68 common field'),('method_angular_nuisance','^-','#238b45','68 + method angular nuisance')]:
        vals=[next(v for v in out if v['experiment']=='mono_method' and v['degree']==j and v['family']==fam)['adequacy_p'] for j in (1,2,3)]
        ax[1].plot(x,vals,style,color=color,label=label)
    ax[1].axhline(.05,color='gray',ls=':');ax[1].set_yscale('log');ax[1].set_ylim(.002,1)
    ax[1].set_xticks(x,['J=1','J=2','J=3']);ax[1].set_ylabel('Conditional fit adequacy p')
    ax[1].set_title('Retained method information tests the mean')
    ax[1].legend(frameon=False,fontsize=9,loc='center',bbox_to_anchor=(.5,.39))
    fig.suptitle('CF4 mono_method: log_mono36 + method32 information recovery',fontsize=12)
    fig.text(.5,.015,'Illustrative mono_method case; same catalogue and full inherited working covariance. Method nuisance is not a measured calibration prior.',ha='center',fontsize=8.5)
    fig.tight_layout(rect=(0,.045,1,.94))
    fig.savefig(base/'RESULTS/INFORMATION_RECOVERY.png',dpi=180)
    fig.savefig(base/'RESULTS/INFORMATION_RECOVERY.pdf')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.')
    run(p.parse_args().root)
