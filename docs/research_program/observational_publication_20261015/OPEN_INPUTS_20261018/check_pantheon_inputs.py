"""Read published release rows/covariance; input qualification, not a fit."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np


def inspect(root):
    root = Path(root)
    table = root/'Pantheon_SH0ES.dat'; cov = root/'Pantheon_SH0ES_STAT_SYS.cov'
    identities = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (table,cov)}
    expected = {'Pantheon_SH0ES.dat':'1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8','Pantheon_SH0ES_STAT_SYS.cov':'abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc'}
    if identities != expected: raise ValueError('Different frozen release input bytes; inspect before reuse')
    rows = np.genfromtxt(table,names=True,dtype=None,encoding='utf-8')
    entries = np.loadtxt(cov)
    n = int(entries[0]); C = entries[1:].reshape(n,n)
    if len(rows) != n or not np.isfinite(C).all(): raise ValueError('Row/covariance contract mismatch')
    asym = float(np.max(np.abs(C-C.T)))
    if np.min(np.diag(C)) <= 0: raise ValueError('Nonpositive covariance diagonal')
    # Preserve raw asymmetry. A separately declared symmetric-part diagnostic
    # never silently substitutes a new covariance into a scientific likelihood.
    S = (C+C.T)/2
    L = np.linalg.cholesky(S)
    eigmin = float(np.linalg.eigvalsh(S)[0])
    corr = S/np.sqrt(np.outer(S.diagonal(),S.diagonal()))
    counts = Counter(rows['CID']); duplicate_rows = sum(v for v in counts.values() if v>1)
    same = np.array([corr[i,j] for i in range(n) for j in range(i) if rows['CID'][i]==rows['CID'][j]])
    return {'owner':'htt','claim_tier':'INPUT_DIAGNOSTIC_ONLY','release_commit':'c447f0fea703fcd0fff57de5000947b5ca81286b',
            'sha256':identities,'rows':n,'distinct_CID_strings':len(counts),
            'repeated_CID_rows':duplicate_rows,'calibrator_rows':int(rows['IS_CALIBRATOR'].sum()),
            'calibrator_unique_CID_strings':len(set(rows['CID'][rows['IS_CALIBRATOR']==1])),
            'covariance_units':'mag^2','max_absolute_asymmetry':asym,
            'raw_is_symmetric_at_1e_minus10':bool(asym <= 1e-10),
            'symmetric_part_only':{'min_eigenvalue':eigmin,'min_cholesky_diagonal':float(L.diagonal().min()),'raw_minus_symmetric_frobenius':float(np.linalg.norm(C-S))},
            'min_diagonal':float(C.diagonal().min()),
            'same_CID_pair_count':int(len(same)),
            'symmetric_part_same_CID_correlation_quantiles':np.quantile(same,[0,.5,1]).tolist(),
            'scope':'Published row count/order contract checked. Raw matrix has measured asymmetry; symmetric-part geometry is a labelled diagnostic, not an adopted likelihood covariance. CID strings are not a canonical cross-survey object identity. No row independence, CF4 independence, physical calibration or significance is admitted.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    out=inspect(a.input_root);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
