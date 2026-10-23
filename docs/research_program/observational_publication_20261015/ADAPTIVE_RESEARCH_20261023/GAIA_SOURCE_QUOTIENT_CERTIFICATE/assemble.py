"""Assemble immutable candidate identities and cumulative process accounting."""
import hashlib,json,re,resource,time
from decimal import Decimal
from pathlib import Path
ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate')
RAW=ROOT/'raw'
start=time.monotonic()

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def metric(label,kind,status):
 p=RAW/f'time_{label}.txt'
 s=p.read_text()
 m=re.search(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(\S+)',s)
 parts=m.group(1).split(':')
 sec=Decimal(parts[-1])+Decimal(parts[-2])*60 if len(parts)==2 else Decimal(parts[-1])+Decimal(parts[-2])*60+Decimal(parts[-3])*3600
 rss=int(re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',s).group(1))*1024
 exit_status=int(re.search(r'Exit status:\s*(\d+)',s).group(1))
 assert exit_status==status
 return dict(label=label,kind=kind,elapsed_seconds=float(sec),max_rss_bytes=rss,exit_status=exit_status,time_evidence=str(p))

commands=[metric('01','certificate_initial',0),metric('02','certificate_full_profiles',0),
 metric('controls_01','control_first_failure',1),metric('controls_02','controls_repair',0),
 metric('controls_03','controls_final',0),metric('03','certificate_final',0),
 metric('backend_01','backend_premise_probe',0),metric('package_01','package_hash_attempt_01',0),
 metric('package_02','package_hash_final',0)]
actual=sum((Decimal(str(x['elapsed_seconds'])) for x in commands),Decimal(0))
assert actual==Decimal('14.89'),actual
maxrss=max(x['max_rss_bytes'] for x in commands)
source={
 'packet_id':'b20cec4107786152ef8e4ffbb0097ec83dd4f2a77a31c32c6935fcaf2adf62ff',
 'task_id':'R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE',
 'input_identity':'sha256:4df217b0798bbb247523dae173fc4026b966a6208496929477085305a44653ba',
 'agent_id':'/root/rc_b20cec4107786152',
 'requested_model':'gpt-6-sol','requested_effort':'high','observed_runtime':'UNKNOWN'
}
receipt=dict(**source,
 original_task_id='R25-GAIA-PAIR-SEPARATION',
 parent_seven_numeric_commands_seconds=43.16,
 parent_independent_review_seconds=3.84,
 parent_cumulative_before_certificate_seconds=47.0,
 parent_original_cap_seconds=300.0,
 incremental_certificate_cap_seconds=120.0,
 numeric_and_packaging_commands=commands,
 actual_command_elapsed_seconds=float(actual),
 metadata_assembly_charged_upper_seconds=1.0,
 certificate_charge_upper_seconds=float(actual+Decimal('1.0')),
 original_cumulative_charge_upper_seconds=float(actual+Decimal('48.0')),
 original_remaining_lower_seconds=float(Decimal('300')-actual-Decimal('48.0')),
 incremental_remaining_lower_seconds=float(Decimal('120')-actual-Decimal('1.0')),
 max_observed_rss_bytes=maxrss,threads=1,rss_limit_bytes=1073741824,
 raw_first_failure=str(RAW/'controls_stderr_01.txt'),
 raw_controls_final=str(RAW/'controls_03.json'),
 backend_evidence=str(RAW/'backend_01.txt'),
 actual_process_HWM_sources=[x['time_evidence'] for x in commands],
 pair_passes_new=0,downloads_new=0,old_fit_replays_new=0,
 source_law='finite Gaussian/block-independent C0 conditional; actual cross-source covariance UNKNOWN',
 status='CANDIDATE_REQUIRES_FRESH_INDEPENDENT_REVIEW')
receipt['metadata_assembly_internal_elapsed_before_writes_seconds']=time.monotonic()-start
receipt['metadata_assembly_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
(ROOT/'RAW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')

files=['certify.py','test_controls.py','RESULT.json','INTERVALS.npz','CENTER.npy','REPORT.md','RAW_RECEIPT.json','raw/controls_03.json','raw/controls_stderr_01.txt','raw/backend_01.txt']
manifest=dict(schema='htt.gaia_source_quotient_certificate_candidate/1',**source,
 candidate_role='exact archived finite source-law quotient certificate candidate, awaiting independent review',
 input_array='sha256:d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5',
 inventory=[dict(path=f,sha256=sha(ROOT/f),size_bytes=(ROOT/f).stat().st_size) for f in files],
 statuses=dict(arithmetic='CANDIDATE_PASS',independent_review='PENDING',physical_covariance='UNKNOWN',
   selected_source_law='UNKNOWN',unrounded_pair_geometry='UNKNOWN',original_acceptances='UNCHANGED_17_OF_42_ALTERNATE_18_OF_42',R9='UNKNOWN'))
mp=ROOT/'MANIFEST.json'
mp.write_text(json.dumps(manifest,indent=2)+'\n')
mid='sha256:'+sha(mp)
ret=dict(**source,outcome='success',candidate_identity=mid,manifest_sha256=mid[7:],
 candidate_identity_role='MANIFEST.json byte SHA-256',
 raw_receipt=str(ROOT/'RAW_RECEIPT.json'),
 validation_evidence=[str(ROOT/'RESULT.json'),str(ROOT/'INTERVALS.npz'),str(RAW/'controls_03.json'),
   str(RAW/'controls_stderr_01.txt'),str(RAW/'backend_01.txt'),str(ROOT/'REPORT.md'),str(mp)],
 qualified_products=[],
 scientific_status='FINITE_GAUSSIAN_C0_CONDITIONAL_CERTIFICATE_CANDIDATE; INDEPENDENT_REVIEW_PENDING; PHYSICAL_UNKNOWN; ORIGINAL_ACCEPTANCE_UNCHANGED',
 actual_numeric_and_packaging_command_elapsed_seconds=float(actual),
 certificate_charge_upper_seconds=receipt['certificate_charge_upper_seconds'],
 actual_numeric_max_rss_bytes=maxrss,
 limits=dict(original_cumulative_numeric_seconds=300,incremental_certificate_seconds=120,
     rss_bytes=1073741824,threads=1,new_pair_passes=0,new_downloads=0,old_fit_replay=False))
(ROOT/'RETURN.json').write_text(json.dumps(ret,indent=2)+'\n')
print(json.dumps(dict(candidate_identity=mid,actual_command_elapsed_seconds=float(actual),
 conservative_charge_upper_seconds=receipt['certificate_charge_upper_seconds'],
 max_rss_bytes=maxrss,metadata_assembly_internal_elapsed_seconds=time.monotonic()-start)))
