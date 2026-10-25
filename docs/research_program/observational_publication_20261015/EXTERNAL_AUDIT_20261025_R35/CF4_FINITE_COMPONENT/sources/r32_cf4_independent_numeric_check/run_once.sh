#!/usr/bin/env bash
set -u
cd /mnt/extdrive/workdir/htt_open_data/r32_cf4_independent_numeric_check || exit 97
started=$(date +%s.%N)
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /usr/bin/timeout --signal=TERM --kill-after=1s 47s /usr/bin/time -v -o TIME.txt /usr/bin/prlimit --as=6442450944 -- /home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python checker.py > stdout.log 2> stderr.log
rc=$?
ended=$(date +%s.%N)
/usr/bin/python3 - "$started" "$ended" "$rc" <<'PY'
import hashlib,json,os,re,sys,time
from pathlib import Path
out=Path('/mnt/extdrive/workdir/htt_open_data/r32_cf4_independent_numeric_check')
a,b,rc=float(sys.argv[1]),float(sys.argv[2]),int(sys.argv[3]);raw=(out/'TIME.txt').read_text() if (out/'TIME.txt').exists() else ''
m=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',raw)
receipt={'start_unix':a,'end_unix':b,'whole_command_seconds':b-a,'exit_code':rc,'max_rss_kib':int(m.group(1)) if m else None,'rss_limit_bytes':6442450944,'threads':1,'subcommand_timeout_seconds':47,'whole_budget_seconds':50,'output_hashes':{p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in ('checker.py','PREPARATION.json','CHECK_RESULT.json','stdout.log','stderr.log','TIME.txt') if (out/p).exists()}}
p=out/'RUN_RECEIPT.json';t=out/'RUN_RECEIPT.tmp';t.write_text(json.dumps(receipt,indent=2));t.replace(p)
with open(p,'rb') as f:os.fsync(f.fileno())
print(json.dumps(receipt),flush=True)
PY
exit "$rc"
