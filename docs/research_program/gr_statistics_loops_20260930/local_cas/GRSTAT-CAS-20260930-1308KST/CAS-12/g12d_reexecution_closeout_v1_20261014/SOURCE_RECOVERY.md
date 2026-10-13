# G12-D re-execution closeout — SOURCE RECOVERY

All paths relative to repo root `/home/cosmosapjw/Dropbox/bianchi/htt_base` unless absolute. Read-only; no git state changed.
Repo HEAD at read time: `c5a683eba0ef1a7d10cc5a7bd6cb6b853bc69eb1` (branch `r2/03-cmb-response-20261014`, dirty checkout preserved).

## Card
- `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256 `2d0b6da9…c4af6f`) member `HTT_ALL_OBLIGATIONS_20261011/tasks/G12-D.json`
  (sha256 `de5f850165feb272fa36580335c658c953c2d98344b7a6029a743fdf8d26dda1`, equals the prior unit's `packet_sha256`).
  lean_steps L1–L5, acceptance X1–X4, pitfall "do not infer Tmax / common envelope from bolometric energy".

## Definitions and domains (all recovered; nothing missing)
| Item | Source citation |
|---|---|
| W = exp(bE)/(exp(bE)−1)², formal small-E expansion vs analytic limit kept separate | `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-12.json:40` and `:108` (sha256 `5a682716…f6fae`) |
| Both f,g ≤ F_b=(exp(bE)−1)⁻¹, b>0, no condensate; measure C E² dE dΩ | `cas/contracts/CAS-12.json:47`, `:62`, `:82` |
| "One-sided IR and UV convergence" | `cas/contracts/CAS-12.json:89` |
| "BE-REF both states required" | `cas/contracts/CAS-12.json:75`, `:95`, `:113` |
| dν = C E² dE dΩ | `supplements/TEFF_POSITIVE_BRIDGE.md:39` (sha256 `f04d96fe…3ff21b`) |
| (A2) sup over z between f,g of z(1+ξz) ≤ W a.e. | `supplements/TEFF_POSITIVE_BRIDGE.md:48-50` |
| (A5) 0 ≤ f,g ≤ F_b, b>0, W = F_b(1+F_b) | `supplements/TEFF_POSITIVE_BRIDGE.md:95-98` |
| IR W=O(E⁻²), UV exponential, "bounded angular kernels times nonnegative powers of E" | `supplements/TEFF_POSITIVE_BRIDGE.md:100` |
| Mixture T ≤ Tmax, nonpositive common log-fugacity ⇒ (A5) with b = 1/(k_B Tmax); reference β ≥ b, η ≤ 0; Tmax not inferred from bolometric energy | `supplements/TEFF_POSITIVE_BRIDGE.md:102` |
| TEFF-A4: "bounded-angular/polynomial-energy targets"; assumptions "fine state AND reference satisfy the envelope", "no singular condensate is included" | `supplements/TEFF_CLAIMS.json:84-92` |
| Lean encodings `occupation`, `inverseTemperature`, `mixtureOccupation`, `energyAngularMeasure`, `kernelDensity`, `weightedKernelMeasure` | prior frozen interface `CAS-12/g12d_uv_integrability_envelope_v1_20261011/lean/G12DInterface.lean:11-31` (sha256 `340d348e…5edff`), reused unchanged |
| Actual right-sided IR limit | `CAS-12/c03_planck_ir_limit_v1_20261011/PlanckIR.lean:11` (source sha256 `5ae963f5a7fd584e038856a0f3da627db6dc2b60c57b9e070fc27f67979995a3`), commit `0a20701de` "CAS-12: prove Planck IR limit sublemma" |
| Card `existing_reuse` "PR #499 formal small-E expansion and coefficient" | commit `20a15b77e` "CAS-12-C03: verify Planck-weight expansion" (unit `CAS-12/c03_planck_weight_v1_20261008`); used only as provenance of the formal series — NOT used as evidence for the analytic limit |
| Prior G12-D unit | commit `947aa8370` "G12-D: prove conditional BE UV and weighted integrability bridge"; RETURN.json sha256 `77fee86d…537d`, REVIEW.md `b746b1e4…79ec`, CONTRACT.json `0bc49bcc…654a`, PARENT_SOURCEBOUND_COMPILE.json `4084c4a9…fcd` |
| Implementation (`htt/`) | `grep -rni condensate htt/ --include=*.py` → no hits; no implementation-side definition needed |

Contract hash identities checked this session: CAS-12.json `5a6827166fe318e37ac9e503a91d6f729155cbef48f450cd9daf0896e47fa6ae`,
TEFF_POSITIVE_BRIDGE.md `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`, package zip
`2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f` — all equal to the prior CONTRACT.json `source_identity`.

## Missing definitions
None. "Condensate exclusion" has no formal definition in the sources beyond "no singular condensate is included"
(TEFF_CLAIMS.json:92) and the η ≤ 0 regular branch; this unit formalizes only that regular-branch/no-atom reading
(targets C11–C13) and does not claim a physical condensate-exclusion theorem.
