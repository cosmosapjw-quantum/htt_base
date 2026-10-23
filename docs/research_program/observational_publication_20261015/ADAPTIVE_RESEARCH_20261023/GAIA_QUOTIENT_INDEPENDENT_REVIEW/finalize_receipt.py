import json
from pathlib import Path
r=Path('/mnt/extdrive/workdir/htt_open_data/r26_gaia_quotient_blind_review')
p=r/'RAW_RECEIPT.json'; d=json.loads(p.read_text())
for c in d['commands']:
 script=r/('review_checks.py' if c['label']=='independent_checks' else 'correction_checks.py')
 c['command']=f"env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 timeout {c['timeout_seconds']}s bash -c 'ulimit -v 2097152; exec python {script}'"
d['assembly_observed_wall_seconds']=0.09
d['assembly_observed_HWM_bytes']=15344*1024
d['assembly_exit_status']=0
d['measured_arithmetic_plus_primary_assembly_seconds']=12.90
d['final_metadata_time_evidence']=str(r/'raw/finalize_receipt.time')
d['final_metadata_charge']='Included in retained 5.00 s conservative preparation/inspection/assembly debit; no reset.'
p.write_text(json.dumps(d,indent=2)+'\n')
print('Receipt command strings made literal; primary assembly measured 0.09 s and charged within existing 5.00 s allowance.')
