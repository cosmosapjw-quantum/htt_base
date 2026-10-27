#!/usr/bin/env python3
"""Descriptive leave-one-survey checks using each retained full covariance subblock."""
import importlib.util
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r36_sn',HERE/'consumer.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rows=np.genfromtxt(mod.FILES['table'][0],names=True,dtype=None,encoding='utf-8')
raw=np.loadtxt(mod.FILES['covariance'][0])
assert int(raw[0])==1701 and len(raw)==1+1701**2
C=raw[1:].reshape(1701,1701)
idx=mod.selected_indices(rows,.0233)
original=json.loads((HERE/'RESULT.json').read_text())['primary']
assert len(idx)==490 and original['row_key_sha256']==__import__('hashlib').sha256('\n'.join(
    f'{int(i)}|{rows["CID"][i]}|{rows["IDSURVEY"][i]}' for i in idx).encode()).hexdigest()

out=[]
for survey in np.unique(rows['IDSURVEY'][idx]):
    kept=idx[rows['IDSURVEY'][idx]!=survey]
    x=rows[kept]
    sub=C[np.ix_(kept,kept)]
    mod.validate_selected_covariance(sub)
    mu,_=mod.reference(x['zHD'],x['zHEL'],64)
    _,N,A=mod.design(x['RA'],x['DEC'],x['zHD']>=.06)
    f=mod.fit(x['m_b_corr']-mu,sub,N,A)
    out.append({'deleted_IDSURVEY':int(survey),'deleted_rows':int(len(idx)-len(kept)),
                'remaining_rows':len(kept),'rank':f['rank'],
                'delta_T':f.get('delta_T'),'conditional_p':f.get('p_chi2_conditional'),
                'coefficient_change_euclidean_mag':float(np.linalg.norm(
                    np.array(f['coefficients_mag'])-
                    np.array(original['fits']['full']['coefficients_mag']))) if f['status']=='FULL_RANK' else None})
result={'schema':'htt.r36_public_sn_survey_deletion/1','scope':'descriptive correlated cohort sensitivity, not independent tests',
        'primary_rows':490,'surveys':out,
        'minimum_delta_T':min(r['delta_T'] for r in out if r['delta_T'] is not None),
        'maximum_delta_T':max(r['delta_T'] for r in out if r['delta_T'] is not None),
        'no_selection_changes_except_one_survey_deletion':True}
(HERE/'SURVEY_ROBUSTNESS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'survey_count':len(out),'delta_T_range':[result['minimum_delta_T'],result['maximum_delta_T']]}))
