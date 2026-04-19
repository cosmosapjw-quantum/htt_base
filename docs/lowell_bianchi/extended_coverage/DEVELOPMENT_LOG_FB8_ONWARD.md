# Development log — FB-8 onward

**Purpose**: canonical ledger of every extended-bundle sub-phase from
FB-8 onward. Entries are append-only: once a row lands it is never
rewritten; a superseding fact is appended as a new row with a
cross-reference.

**Parent**: [INDEX.md](INDEX.md).
**Coordinator plan**:
[EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).

---

## Phase FB-8 — Observer-frame discriminator (extended bundle)

### FB-META-8.0 — pre-flight scan + audit scaffolding

- **Scope**: Read the required FB-8 phase documents plus the rapidity
  and boost-kernel SSOT modules, confirmed that
  `bass.species.tilted.assert_tilt_admissible` exists, and created
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  with the observer-versus-cosmological type-distinction banner and
  seven staged `§FB-8.k` sections.
- **Commit anchor**: see `git log --grep='FB-META-8.0'`.
- **Test delta**: 3,403 passing + 53 skipped → 3,403 passing + 53
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md).
- **Gallery**: no-op (audit/doc scaffolding only).
- **Carry-forward**: sub-phase skeleton plants FB-8.1 through FB-8.7.
- **Notes**: all observer-frame production surfaces for this phase land
  under `htt/bass/observer/`; production composition remains layered via
  `bass.likelihood.observer_frame_adapter`.
