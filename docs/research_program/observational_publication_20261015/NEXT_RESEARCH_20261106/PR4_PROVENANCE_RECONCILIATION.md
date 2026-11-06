# PR4 Commander MC100 provenance reconciliation

**Pinned tree:** d7d5ce2a107b25479b8276f9fd4b5d69dbf53ad9.

## Mismatch

In OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-06-PR4-MORPHOLOGY, the Commander MC100 aggregate and independent review coexist with a top-level RESULT.json and INTERPRETATION.md retaining fields from an earlier 30-GHz LFI A/B pilot. The older branch mentions A/B temporal splits, synthetic coadd C, old LFI source hashes, a within-sky scan and an old “matched total ensemble missing” status. These fields are not the same source/estimand as the later Commander MC100 result.

The 30-GHz pilot is not invalidated; its source identity and result must simply remain separate. Do not treat the hybrid wrapper as a single experiment.

## Commander MC100 result for its own estimand

Observed values:
- \(J_{234}=0.023303063048111198\)
- \(|J_{234}|=0.023303063048111198\)
- \(\mathrm{alignment}_{23}^{2}=0.458662167474815\)

For \(N=100\) and plus-one rank convention:
- \(p(J_{234}^{MC}\ge J_{234}^{obs})=44/101=0.4356435644\)
- \(p(|J_{234}^{MC}|\ge|J_{234}^{obs}|)=75/101=0.7425742574\)
- \(p(\mathrm{alignment}_{23,MC}^{2}\ge\mathrm{alignment}_{23,obs}^{2})=23/101=0.2277227723\)

Aggregate and independent review describe processed Commander MC IDs 300–399 and one fixed LoLLiPoP mask. This is C0: one PR4 Commander E-mode \(\ell=2,3,4\) morphology/null experiment. N=100 gives coarse tail resolution. It does not measure T-mode low-\u2113 morphology, observer velocity, global tilt, shear or Bianchi family.

## Append-only repair contract

Do not rewrite/delete frozen historical files. New consumers type two separate estimands:
1. §PR4_30GHz_AB_PILOT§;
2. §PR4_COMMANDER_MC100_E_LOWELL§.

Add a semantic reconciliation artifact/test that checks map/pipeline/source hashes, mask, feature definition, simulation role and p-values within the correct branch; fail if Commander p-values are paired with old LFI source metadata. Update only new report/index consumers and preserve old pilot records/checksums. No claim above C0 until alternate pipeline, T-mode and common boost/Bianchi response are processed under valid matched nulls.
