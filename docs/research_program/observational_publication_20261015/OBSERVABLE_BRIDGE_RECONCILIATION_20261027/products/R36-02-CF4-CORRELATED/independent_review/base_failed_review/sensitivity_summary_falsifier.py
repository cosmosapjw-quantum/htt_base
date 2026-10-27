"""Minimal independent falsifier for the saved matched-radius sensitivity claim."""
import json
from pathlib import Path
import numpy as np

root=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED')
ext=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
summary=json.loads((root/'SENSITIVITY.json').read_text())
with np.load(ext/'SENSITIVITY_MATRICES.npz') as f:
    subset=f['exclude_FP'][72:108,72:108]
with np.load(ext/'STAGE_C.npz') as f:
    same_radius_full=f['total'][72:108,72:108]
reported=summary['results']['exclude_FP']['bands_sum_blocks'][2]['trace_ratio_to_full_sample']
expected=float(np.trace(subset)/np.trace(same_radius_full))
print(json.dumps({'case':'exclude_FP','R_hinv_Mpc':20,'reported':reported,'expected':expected}),flush=True)
np.testing.assert_allclose(reported,expected,rtol=1e-12,atol=1e-14,
    err_msg='Footprint/method sensitivity must hold the smoothing radius fixed')
