#!/usr/bin/env bash
set -u
task=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12b_conventional_rodrigues_v1_20261011
oracle=/home/cosmosapjw/lean_oracles/viii_oracle
label=attempt11_audit
cp "$task/raw/AxiomAudit.lean" "$task/raw/${label}_audit_source.lean" || exit 97
audit_hash=$(sha256sum "$task/raw/${label}_audit_source.lean" | cut -d ' ' -f 1)
candidate_hash=$(sha256sum "$task/lean/ConventionalRodrigues.lean" | cut -d ' ' -f 1)
scalar_import_hash=$(sha256sum "$task/raw/imports/ScalarWrapper.olean" | cut -d ' ' -f 1)
candidate_import_hash=$(sha256sum "$task/raw/imports/ConventionalRodrigues.olean" | cut -d ' ' -f 1)
cd "$oracle" || exit 99
cmd=(lake env bash -c "LEAN_PATH=$task/raw/imports:\$LEAN_PATH lean -R $task/raw $task/raw/AxiomAudit.lean")
argv_json=$(printf '%s\n' "${cmd[@]}" | jq -R . | jq -s .)
printf '%s\n' "$argv_json" > "$task/raw/${label}.argv.json"
"${cmd[@]}" > "$task/raw/${label}.stdout.log" 2> "$task/raw/${label}.stderr.log"
code=$?
jq -n --arg label "$label" --arg cwd "$oracle" --argjson argv "$argv_json" \
  --argjson exit_code "$code" --arg audit_source_snapshot_sha256 "$audit_hash" \
  --arg candidate_source_sha256 "$candidate_hash" \
  --arg scalar_wrapper_olean_sha256 "$scalar_import_hash" \
  --arg conventional_rodrigues_olean_sha256 "$candidate_import_hash" \
  '{label:$label, mode:"audit", cwd:$cwd, argv:$argv, exit_code:$exit_code,
    audit_source_snapshot_sha256:$audit_source_snapshot_sha256,
    candidate_source_sha256:$candidate_source_sha256,
    scalar_wrapper_olean_sha256:$scalar_wrapper_olean_sha256,
    conventional_rodrigues_olean_sha256:$conventional_rodrigues_olean_sha256}' \
  > "$task/raw/${label}.receipt.json"
exit "$code"
