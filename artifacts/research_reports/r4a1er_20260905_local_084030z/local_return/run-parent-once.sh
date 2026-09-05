#!/bin/bash
set -u
. /mnt/sn850x2t/htt_base_e2e/R4A1E_LOCAL_EXISTING_R2_20260905T084030Z/result/environment.sh
test ! -e "$D/CAS_ADJUDICATION_R4A1NF_DOMAIN.json" || exit 73
test ! -e "$RUN/adjudication.started" || exit 73
"$PY" -B -c 'import json,os; from pathlib import Path; r=Path(os.environ["RUN"]); w=Path(os.environ["WT"]); assert (r/"source-binding.exit").read_text().strip()=="0"; assert json.loads((w/"docs/research_reports/verifiers/r4a1nf/CAS_SOURCE_BINDINGS_R4A1NF_DOMAIN.json").read_text())["ok"] is True' || exit 74
date -u +%FT%TZ > "$RUN/adjudication.started"
"$PY" .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract "$D/CAS_CONTRACT_R4A1NF_DOMAIN.json" \
  --run-spec "$D/CAS_RUN_SPEC_R4A1NF_DOMAIN.json" \
  --out "$D/CAS_ADJUDICATION_R4A1NF_DOMAIN.json" \
  > "$RUN/adjudication.stdout" 2> "$RUN/adjudication.stderr"
CAS_EXIT=$?
printf '%s\n' "$CAS_EXIT" > "$RUN/adjudication.exit"
date -u +%FT%TZ > "$RUN/adjudication.completed"
exit "$CAS_EXIT"
