#!/usr/bin/env python3
"""Optional owner-Codex direct local-source replay; no downloads or repo mutation.

File hashes must match declared source identities. Refuses missing files rather
than regenerating masks, resetting Git or mixing distinct Planck products.
"""
from __future__ import annotations
import argparse,os,shutil,tempfile
from pathlib import Path
from l01_source import EXPECTED,sha256_file
from run_l01 import run,UPSTREAM_LOOP5_SHA,UPSTREAM_RESULT16_SHA

P='docs/research_program/theory_obs_application_20261015/'
PATHS={
'source/retained_common_support_coefficients.npz':[
 P+'loop8_mes_eps_20261016/inputs/loop5/retained_common_support_coefficients.npz',
 P+'loop5/results/planck_multisplit_spin_v1/retained_common_support_coefficients.npz'],
'source/baseline_response_matrices.npz':[P+'loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz'],
'source/ell17_32_mask_response.npz':[P+'loop12_smica_power_envelope_local_20261016/results/ell17_32_source_v1/ell17_32_mask_response.npz'],
'source/processing_coefficients.npz':[
 P+'loop8_mes_eps_20261016/inputs/ffp_response/processing_coefficients.npz',
 'docs/observational_reboot_20261014/results/smica_response_scan_v2/processing_coefficients.npz'],
'source_sourcejson/result.json':[
 P+'loop8_mes_eps_20261016/inputs/loop5/result.json',
 P+'loop5/results/planck_multisplit_spin_v1/result.json'],
'source_sourcejson/result_2.json':[P+'loop9_smica_finite_response/results/response_v1/result.json']
}


def locate(repo_root:Path):
 root=Path(repo_root)
 if not (root/'AGENTS.md').is_file():raise FileNotFoundError('HTT existing repository AGENTS.md not found')
 selected={}
 for name,candidates in PATHS.items():
  expected=(EXPECTED[Path(name).name] if name.startswith('source/') else (UPSTREAM_LOOP5_SHA if name.endswith('/result.json') else UPSTREAM_RESULT16_SHA))
  found=[]
  for rel in candidates:
   f=root/rel
   if f.is_file():
    if sha256_file(f)==expected:found.append(f)
    else:raise ValueError('An existing candidate source mismatches locked SHA: '+str(f))
  if not found:raise FileNotFoundError('Missing pinned original source: '+name+'; candidates='+str(candidates))
  selected[name]=found[0]
 return selected


def replay(repo_root:Path,out:Path):
 if Path(out).exists():raise FileExistsError('refuse overwriting existing output')
 files=locate(repo_root)
 with tempfile.TemporaryDirectory(prefix='htt-p2-l01-locked-') as tmp:
  stage=Path(tmp)
  for name,source in files.items():
   dst=stage/name;dst.parent.mkdir(parents=True,exist_ok=True)
   try:os.link(source,dst)
   except OSError:shutil.copyfile(source,dst)
  return run(stage,out)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
 x=replay(args.repo_root,args.output_dir)
 print({'status':'SOURCE_LOCKED_P2_L01_REPLAY','T_K6_32':x['temperature_source_geometry']['combined'],
        'n_pol_products':len(x['source_products']['polarization_EB'])})
