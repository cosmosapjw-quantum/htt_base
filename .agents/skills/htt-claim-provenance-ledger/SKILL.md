---
name: htt-claim-provenance-ledger
summary: Audit and update claim status, evidence type, owner, and allowed language across HTT/MIO/BASS reports, code comments, figures, and manuscripts.
description: Use when writing or changing scientific claims, result captions, reports, claim ledgers, artifact manifests, status snapshots, or publication-facing text.
---

# HTT Claim Provenance Ledger Skill

## Purpose

Stop claim drift before it reaches reports, figures, manuscripts, or external audit packages.

## Project claim status vocabulary

Use these labels unless a stricter schema is defined in `common/contracts`:

- `IMPLEMENTED`: code exists and is integrated.
- `SMOKE_TESTED`: basic execution/import/collection ran.
- `VALIDATED`: tested, benchmarked, reproduced, or independently checked.
- `DERIVED`: mathematically derived under stated assumptions.
- `SPECIFIED`: design/spec exists, not implemented.
- `CONDITIONAL`: valid only under explicit policy/assumptions.
- `DIAGNOSTIC_ONLY`: useful report/indicator, not production inference.
- `PROPOSED`: planned direction.
- `SPECULATIVE`: unsupported but interesting.
- `DEPRECATED`: no longer controlling.
- `FORBIDDEN`: explicitly disallowed.

## Required claim fields

Each nontrivial claim must identify:

```yaml
claim_id:
text:
owner: common|obsstat|bass_py|BASS_native|htt|mio|tsc_legacy|manuscript
status:
evidence_type: proof|test|artifact|external_transfer|native_transfer|figure|citation|none
transfer_source: none|AniCLASS_external|BASS_native_provisional|BASS_native_validated|empirical_proxy
claim_tier: C0|C1|C2|C3|C4|C5|C6
caveats: []
```

## Required workflow

1. Extract strong claims from changed files.
2. Assign owner/status/evidence.
3. Check forbidden language.
4. Downgrade claims with missing validation or hidden transfer dependence.
5. Update claim ledger artifacts.
6. Add manuscript caption caveats where necessary.

## Forbidden claim patterns

- `model-independent proof of Bianchi geometry`.
- `MIO certifies truth`.
- `HTT evidence and MIO certificate combine into one score`.
- `Teff/TSC solves full polarization`.
- `family identified` without native morphology atlas and equivalence-class breaking.
- `validated` from smoke/demo/toy output.

## Required output

```markdown
## Claim audit
| Claim | Owner | Status | Evidence | Risk | Required fix |
|---|---|---|---|---|---|

## Upgraded claims

## Downgraded claims

## Forbidden drift detected

## Ledger updates needed
```

## Hard prohibitions

- Do not allow `SPECIFIED`/`PROPOSED` claims to appear as `IMPLEMENTED`.
- Do not allow `SMOKE_TESTED` to justify publication-grade validation.
- Do not hide external transfer dependence.
