# Local cleanup receipt — 2026-10-14

Scope: repository housekeeping only. No historical CAS verdict, scientific
claim, source identity, or task accounting was changed.

The current host reports Codex CLI `0.162.1`. The former global CUH-G
descriptor, hooks, services and launchers were absent at inspection. The
repository `.cuh` had 200 ignored regular files (11,825,048 bytes) and no
live open handle. Historical RETURN files retain their original `.cuh` path
references as provenance.

Before removing `.cuh` and the three owner-designated numbered copies, all
203 files were saved and individually SHA-256 checked against the archive at
`/home/cosmosapjw/.codex/backups/htt_base_retired_local_20261014/repo_local_retirement.tar.gz`.
Archive SHA-256:
`c8d3be25dd235fba52e59d43430bc3e37da41ce7271bf8b8e6aec93179e58b5d`.
The adjacent `manifest.json` records each original relative path, byte count,
mtime and SHA-256. This is a local backup, not a Git publication or new
runtime registration. The removed numbered files were
`proof_dag_driver (1).sh`, `CLAUDE_CODE_HANDOFF_KO (1).md`, and
`htt_proof_tools (1).zip`; their unsuffixed files remain.

The exact ignored CAS-03-C02 `lean/.lake` dependency/build cache (7.3 GiB
allocated) was removed after confirming its nine dependency checkouts were
clean and pinned by the adjacent `lake-manifest.json`, no live handle, and the
Lean source, toolchain and raw receipts outside `.lake`. Rebuilding it may
require network access and time. Hashed `raw/imports/*.olean` proof inputs
were not removed.

The root `THEORY_INHERITANCE.sqlite.gz` (59,025,657 bytes, SHA-256
`17288a47268253aa3e0eb4b6a7f8027562dd8995febd0b917db8632772521614`)
was removed after byte comparison with the single matching member
`TYPEFREE_RESEARCH_LOOP1_20260928/THEORY_INHERITANCE.sqlite.gz` in the retained
`TYPEFREE_RESEARCH_LOOP1_20260928.zip` (archive SHA-256
`0f896823faa03ed82b8cf484cfc893a56ea913e259dc16d59c50d5f97e68670c`).
This leaves a historical root-path input absent until restored. To restore
exact bytes before replaying a task that needs that path:

```sh
python3 - <<'PY'
from pathlib import Path
import zipfile
root = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
with zipfile.ZipFile(root / 'TYPEFREE_RESEARCH_LOOP1_20260928.zip') as archive:
    data = archive.read('TYPEFREE_RESEARCH_LOOP1_20260928/THEORY_INHERITANCE.sqlite.gz')
(root / 'THEORY_INHERITANCE.sqlite.gz').write_bytes(data)
PY
```

No unrelated ignored evidence, other database, historical worktree, or frozen
assignment was deleted.

The owner later confirmed that the remaining `(1)` copies were content
duplicates. The tracked root-level audit report was byte-identical to
`docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report/AUDIT_REPORT.md`
(SHA-256 `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`).
Its historical manifest and references remain unchanged. The nine files in
`htt_proof_tools (1)/htt_proof_tools/` and that audit copy were separately
archived, then removed after confirming no open handles. This second archive
is `/home/cosmosapjw/.codex/backups/htt_base_retired_local_20261014/numbered_duplicates_20261014.tar.gz`
(SHA-256 `d74778080b65efd4e1cc3c65f32ede99264b5f90a15c94770ba45dae0f698cbb`);
the adjacent JSON records all ten file hashes and sizes. Six of the nine
tool files match root files byte for byte. Two root tools have since changed,
and one numbered prompt has no root counterpart; their original bytes remain
in the backup for historical replay.
