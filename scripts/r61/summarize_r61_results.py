#!/usr/bin/env python3
"""Regenerate concise tables from existing R61 results without refitting data."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import chi2


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--results',required=True)
    a=p.parse_args();root=Path(a.results).resolve()
    paths={'images':'IMAGES/KINEMATIC_IMAGES.json','depth':'DEPTH/KINEMATIC_DEPTH.json',
           'mixed':'MIXED/R61_MIXED_INVARIANT_RESULT.json','box':'BOX_COMPARISON/R61_BOX_COMPARISON_RESULT.json'}
    if (root/'DEPTH_CORRECTED/KINEMATIC_DEPTH.json').exists():
        paths['depth']='DEPTH_CORRECTED/KINEMATIC_DEPTH.json'
    sources={k:json.loads((root/v).read_text()) for k,v in paths.items()}
    i,d,m,b=(sources[k] for k in ['images','depth','mixed','box'])
    origin={};variants={}
    for name,v in d['variants'].items():
        base=i['variants'][name]['1.0'];h=np.asarray(base['estimate11']);C=np.asarray(base['covariance11'])
        w=float(h@np.linalg.solve(C,h));origin[name]={'Q11':w,'p11':float(chi2.sf(w,11))}
        cl=v['angular_log_closure'];contrast=v['depth_contrast_002_008']
        variants[name]={'slope_p5':v['slope_test']['p'],'slope_Wald5':v['slope_test']['wald'],
            'depth_contrast_rms_point':contrast['full_sky_angular_rms_point'],
            'depth_contrast_rms_interval':contrast['simultaneous16_rms_interval'],
            'common_calibration_slope_error':contrast['common_calibration_slope_max_abs'],
            'optimal_pivot':v['trace_minimizing_redshift'],'rms_z0_error_over_pivot':v['sqrt_trace_z0_over_optimal_pivot'],
            'Sigma0_joint16':v['depth_images']['0.0']['Sigma_simultaneous16'],
            'log_closure_max_shift_sd':cl['max_abs_shift_over_linear_sd'],
            'log_remainder_gaussian_norm':cl['fixed_linear_point_whitened_remainder_norm'],
            'marginal5_Sigma':base['marginal_shear5_sigma_interval'],
            'marginal5_calibration_zero_rms_mag':base['marginal_shear5_calibration_zero_threshold_mag'],
            'beta_dot_a_actual_box_width_ratio':base['images_by_rms_mag']['0.0']['beta_dot_a']['coordinate_box_comparator']['width_ratio'],
            'mixed_actual_box_ratio_zero_mag':next(x['comparison']['actual_box_width_over_joint_enclosing_width']
                for x in b['results'] if x['model']==name and x['calibration_fullsky_rms_mag']==0)}
    result={'schema':'htt.r61.summary/1','sources':{k:{'path':v,'sha256':sha(root/v)} for k,v in paths.items()},
        'generator_sha256':sha(__file__),'image_union':i['model_union'],
        'depth_contrast_union':d['model_union_depth_contrast_rms'],
        'mixed_union':m['model_union'],'mixed_max_endpoint_gap':m['max_gap'],
        'box_comparison':b['summary'],'joint_zero_response':origin,
        'maximum_p11_zero_response':max(v['p11'] for v in origin.values()),
        'speed_upper_km_s':299792.458*i['model_union']['1.0']['0.0']['relative_speed_over_c']['upper'],
        'variants':variants,'conditions':'Fixed Gaussian law; same11D confidence set for primary functions; finite7model union; calibration budgets are sensitivity inputs.'}
    (root/'NUMERICAL_SUMMARY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# R61 generated numerical tables','',
        'Generated from the four result JSON files named in NUMERICAL_SUMMARY.json. No refitting.',
        'Ranges are conditional on the declared law, response and calibration family.','',
        '## Joint11 model union, covariance lambda=1','',
        '| Quantity | 0 mmag lower | 0 mmag upper | 5 mmag lower | 5 mmag upper |',
        '|---|---:|---:|---:|---:|']
    for key in ['Sigma','acceleration_over_cH','relative_speed_over_c','directional_expansion_rms','beta_dot_a']:
        row=[i['model_union']['1.0'][str(mag)][key][bound] for mag in [0.,.005] for bound in ['lower','upper']]
        lines.append('| '+key+' | '+' | '.join(f'{v:.9g}' for v in row)+' |')
    rows=[next(r for r in m['model_union'] if r['calibration_fullsky_rms_mag']==mag) for mag in [0.,.005]]
    lines.append('| beta^T s beta | '+' | '.join(f'{v:.9g}' for row in rows for v in row['outer_range'])+' |')
    lines+=['','## Depth response and geometry comparison','',
       '| Variant | Slope nominal p5 | Depth RMS upper | Optimal z | z0/pivot RMS error | beta.a box ratio | Mixed exact-box ratio, 0 mmag |',
       '|---|---:|---:|---:|---:|---:|---:|']
    for name,v in variants.items():
        values=[v['slope_p5'],v['depth_contrast_rms_interval']['upper'],v['optimal_pivot'],v['rms_z0_error_over_pivot'],
                v['beta_dot_a_actual_box_width_ratio'],v['mixed_actual_box_ratio_zero_mag']]
        lines.append('| '+name+' | '+' | '.join(f'{x:.8g}' for x in values)+' |')
    lines+=['','The box comparisons replace the whole joint ellipsoid by its coordinate-support box; they do not isolate covariance off-diagonals or compare with a different independent-data law.',
        'The mixed legacy triangle-bound ratio is deliberately excluded from the geometry-comparison column.','']
    (root/'NUMERICAL_TABLES.md').write_text('\n'.join(lines))
    print(json.dumps({'max_p11_zero_response':result['maximum_p11_zero_response'],
                     'mixed_max_endpoint_gap':result['mixed_max_endpoint_gap'],'box_comparison':result['box_comparison']},indent=2))


if __name__=='__main__':main()
