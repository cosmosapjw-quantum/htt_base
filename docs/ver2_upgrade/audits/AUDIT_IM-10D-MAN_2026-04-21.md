# AUDIT_IM-10D-MAN_2026-04-21

## Target

- Packet: `IM-10D-MAN`
- Lane: `D`
- Authority: `docs/ver2_upgrade/*` only
- Goal: close the manuscript-upgrade phase on top of the manifest-backed
  D-lane exporter by restoring exporter-owned manuscript hooks, wiring
  claim-tiered prose into the manuscript chapters, and promoting only the
  figures/tables allowed by the live manifest audit.

## RE2 Read Set

1. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_02_IMPLEMENTATION_FIGURES_MANUSCRIPT.md`
2. `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
3. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
4. `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
5. `docs/ver2_upgrade/audits/AUDIT_IM-08V_2026-04-21.md`
6. `docs/ver2_upgrade/audits/AUDIT_IM-09D-FIG_2026-04-21.md`
7. `docs/ver2_upgrade/generated/RESULT_PACK_INDEX.md`
8. `docs/ver2_upgrade/generated/FIGURE_GALLERY_TOPIC_MAP.md`
9. `figures/paper/VER2_MANIFEST_INDEX.md`
10. `docs/manuscript/ch07_results.tex`
11. `docs/manuscript/ch09_discussion.tex`
12. `docs/manuscript/ch11_error_hierarchy.tex`
13. `docs/manuscript/appendices.tex`

## Divergence -> Verification -> Convergence

### Candidate A

- Hand-edit the manuscript prose only and leave the manuscript-generated
  TeX hooks as static files.
- Rejected:
  - reintroduces a second manual summary layer above the live result packs,
  - risks drift between chapter wording and the generated claim/status
    surfaces,
  - leaves the manuscript snippets outside the exporter ownership model.

### Candidate B

- Restore exporter-owned manuscript-generated TeX hooks, derive the
  manuscript-facing summaries from the live pack/status/validation
  artifacts, and wire only the allowed figures into the manuscript.
- Selected:
  - keeps counts and claim tiers derived from the same manifest-backed
    source objects as the D-lane exports,
  - closes the chapter-wiring gap without inventing new science surfaces,
  - preserves the artifact-first promotion rule.

### Candidate C

- Rebuild the manuscript integration around a fresh bespoke export script.
- Rejected:
  - unnecessary rewrite,
  - higher regression risk,
  - no gain over Candidate B.

## Contract / Interface Audit

| Surface | Required contract | Pre-packet gap | Outcome |
|---|---|---|---|
| manuscript hooks | chapter-facing TeX must be generated from shared status/claim/result-pack state | existing `docs/manuscript/generated/*` hooks were stale, exporter no longer owned them | fixed |
| figure promotion | only manifest-ready figures may enter the manuscript | `IM-09D-FIG` created the figures, but manuscript chapters still did not consume them | fixed |
| claim-tier wording | exploratory artifacts must remain diagnostic in prose | chapters did not yet state the result-pack ceilings explicitly | fixed |
| validation ceilings | `warn` campaigns must remain no-claim gates in manuscript text | registry/export layer recorded this, but manuscript prose did not | fixed |
| package ownership | BASS/HTT/MIO/TSC roles must remain distinct in prose | chapter text still lacked a unified crosswalk for the promoted VER2 export family | fixed |

## Three Verification Lanes

### 1. Internal docs + local code

- Re-read the `IM-10D-MAN` prompt and the current manuscript/export state.
- Confirmed the load-bearing gap:
  - `IM-09D-FIG` closed export generation, but the manuscript still had no
    claim-tiered chapter interpretation of the live result packs and
    manifest-ready figures.

### 2. Web CRAG

- Not needed for this packet.
- Reason:
  - no new external literature claims or citations were introduced,
  - the packet closes manuscript wiring against already-generated local
    artifacts and existing chapter references only.

### 3. Integrated phys-math-code audit

- Physics: partial pass
  - the packet does not introduce new physics calculations,
  - the promoted figures/prose remain bounded by the existing manifest
    claim tiers.
- Math: pass
  - the manuscript now distinguishes conditional versus exploratory packs,
    and explicitly states the warn/no-claim validation ceiling.
- Code: pass
  - the exporter once again owns the manuscript-facing generated snippets,
  - chapter text and appendix references now consume those generated hooks
    instead of maintaining a parallel manual summary.

## Patches

1. `scripts/ver2_artifact_export.py`
   - restored exporter ownership of `docs/manuscript/generated/*`
   - added generated manuscript snippets for:
     - result-pack to manuscript mapping,
     - figure-promotion status,
     - validation ceiling wording
2. `scripts/test_ver2_artifact_export.py`
   - updated scope assertions for the post-`IM-10D-MAN` exporter
   - added a regression check that the manuscript validation snippet keeps
     the warn/no-claim ceiling explicit
3. `docs/manuscript/ch07_results.tex`
   - added the manifest-backed VER2 export-closure subsection
   - promoted only conditional Result Packs `A` and `D` into the main text
4. `docs/manuscript/ch09_discussion.tex`
   - added an explicit claim-tier interpretation subsection for the VER2
     export family
5. `docs/manuscript/ch11_error_hierarchy.tex`
   - attached the generated validation-status hook and spelled out the
     warn/no-claim implication for the governance layer
6. `docs/manuscript/appendices.tex`
   - added the result-pack crosswalk appendix
   - quarantined exploratory Result Packs `B`, `C`, and `E` to appendix-only
     figures

## Failure Modes Rechecked

1. `P0` manuscript prose overclaims an exploratory or conditional artifact
   - fixed by explicit pack-role wording in Chapters 7, 9, 11 and the appendix
2. `P0` chapter-facing counts drift from the live manifest-backed status snapshot
   - fixed by exporter-owned manuscript snippets
3. `P1` warn-grade validation campaigns are implicitly treated as scientific validation
   - fixed by explicit warn/no-claim wording in manuscript-generated TeX and chapter prose
4. `P1` diagnostic local-vs-global or MIO outputs are mistaken for HTT posterior semantics
   - fixed by appendix-only quarantine for Packs `B`, `C`, `E` and explicit ownership wording
5. `P1` legacy non-manifest figures are silently promoted by manuscript edits
   - fixed by promoting only the five manifest-ready `ver2_generated` figures and leaving the legacy `83` blocked

## Verification

- `venv/bin/python -m py_compile scripts/ver2_artifact_export.py scripts/test_ver2_artifact_export.py`
  - passed
- `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py -q`
  - `7 passed`
- `venv/bin/python scripts/ver2_artifact_export.py`
  - passed
  - generated `42` export/manuscript surfaces and `5` manifest-ready figure bases
- `venv/bin/python scripts/ver2_artifact_export.py --check`
  - passed
- `rg -n "sec:ver2-export-closure|fig:ver2_pack_[abcde]|fig:ver2_conditional_exports|app:ver2-crosswalk|sec:disc-ver2-claimtiers" docs/manuscript/*.tex`
  - passed

## Remaining Carry-Forward

- `83` legacy paper figures remain `blocked_no_manifest`; this packet only
  promotes the five manifest-ready `ver2_generated` figures.
- The H-lane still lacks a dedicated posterior/evidence serializer beyond
  legacy readers.
- TSC active-service-bundle export remains wording-backed rather than a
  fully automatic manuscript serializer.

## Final Judgment

- Verdict: partial pass, packet closed and ready to land in history.
- Implemented now:
  - exporter-backed manuscript hooks plus claim-tiered chapter/appendix
    wiring for the manifest-backed VER2 export family.
- Do not touch now:
  - legacy figure retrofits or any attempt to promote exploratory/warn-grade
    artifacts beyond the manifest claim ceilings.
