"""Re-evaluate all six retained R31/R32 response conventions on actual Y."""
from pathlib import Path
import csv
import json
import numpy as np

PRODUCT=Path(__file__).resolve().parent
ROOT=PRODUCT.parents[2]
R32=json.loads((ROOT/'PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_05/RESULT.json').read_text())
BASE=ROOT/'PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_05/report/generated'
EXT=Path('/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual')
with np.load(EXT/'ACTUAL_GEOMETRY.npz',allow_pickle=False) as z:Y=z['Y'].copy()
D=np.asarray(R32['common_reference_column_scales'],float)
Minv=np.diag(D**-2)
rows=[]
for key in R32['branches']:
 with np.load(BASE/(key+'_full24.npz'),allow_pickle=False) as z:F=z['F'].copy();a=z['a'].copy()
 C=np.linalg.inv(F@Minv@F.T)
 ell2=float(a@C@a);s0=Y.T@C@a/ell2;res=Y-np.outer(a,s0)
 J0=float(np.sum(res*(C@res)))
 rows.append({'branch':key,'ell':float(np.sqrt(ell2)),
              'rho_min_algebraic_K_CMB':float(np.sqrt(J0)),
              'center_B_norm_K_CMB':float(np.linalg.norm(s0[12:])),
              'F_rank_numeric':int(np.linalg.matrix_rank(F)),
              'source':'R32 repair_05 F,a,metric + actual FULL7 Y; conditional common-response model'})
(EXT/'BRANCH_SENSITIVITY.json').write_text(json.dumps(rows,indent=2)+'\n')
with (PRODUCT/'BRANCH_SENSITIVITY.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(('branch','ell','rho_min_algebraic_microK_CMB','center_B_norm_microK_CMB','F_rank_numeric'))
 for row in rows:w.writerow((row['branch'],row['ell'],row['rho_min_algebraic_K_CMB']*1e6,
                             row['center_B_norm_K_CMB']*1e6,row['F_rank_numeric']))
print(json.dumps(rows,indent=2))
