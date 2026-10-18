"""Presentation-only labels; never change, reorder or recompute LP endpoints."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
p=HERE/'D07_RESULT.json';r=json.loads(p.read_text());crossings=[]
for level in r['projections']:
    for projection in level['projections']:
        gap=projection['lower_mag']-projection['upper_mag']
        projection['raw_lower_minus_upper_mag']=gap
        projection['endpoint_pair_ordering']='NUMERICALLY_UNRESOLVED_WITHIN_SOLVER_PRECISION' if gap>0 else 'ORDERED_RAW_ENDPOINTS'
        if gap>0:crossings.append({'reference_increment':level['reference_increment'],'target':projection['target'],'raw_lower_minus_upper_mag':gap})
r['finite_endpoint_ordering']={'crossings':crossings,'max_raw_lower_minus_upper_mag':max([x['raw_lower_minus_upper_mag'] for x in crossings],default=0.),
                                'policy':'raw values unchanged; no clamp, reorder, tolerance relaxation or LP rerun; FINITE labels individual solver objectives, not exact floating-point endpoint order'}
p.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
print(json.dumps(r['finite_endpoint_ordering']))
