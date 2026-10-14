# CAS12-C01 finite adjoint successor

`KERNEL_CHECKED_FINITE_C01_PENDING_INDEPENDENT_REVIEW`.
Owner: `common` mathematical contracts; scope: CAS-12-C01 only; claim tier:
`C0`; transfer source: `none`. The frozen historical CAS campaign and scientific
admission are unchanged; no historical four-axis validator was run.

For every finite-dimensional real positive inner-product space E, every fixed
linear map L:E→E, every supplied retained subspace V, and arbitrary K,f,g,h:

1. `<K,Lf> = <L* K,f>` for mathlib's actual finite adjoint.
2. Agreement of all V moments is equivalent to `f-g ∈ V⊥`.
3. `L* K ∈ V` iff `<K,Lh>=0` for every `h ∈ V⊥`.
4. `L* K ∈ V` iff every pair agreeing on V has equal output K moments.
5. The explicit premise `∀K∈V, L* K∈V` propagates retained equivalence.

The statements quantify over arbitrary finite dimension, linear maps, and
subspaces. There is no assumption of the desired annihilation conclusion in the
forward proofs. The preservation premise is explicit; an arbitrary operator is
not silently assumed to preserve V. Positive-definiteness belongs to the supplied
inner-product type. This is finite algebra, and does not establish existence of a
continuum weighted adjoint or identify a physical collision operator.

Universal controls prove nonvanishing of the identity-operator self moment for
nonzero K, and zero output for the zero operator. There is no division, so the
zero-dimensional space and zero/rank-deficient operators remain in domain.
Lorentz signature, frames, physical constants, and radiation energy measures are
not encoded or reinterpreted as a positive inner product here.

## Evidence

Inputs are the frozen `EXECUTION_CONTRACT.json`, SHA
`c35359e6b5b34c9b2dd085050acb21f737f6646c95e8abd8b69c6a1d7b694a21`, and
`cas/COMMON_SPEC.md`, SHA
`4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`.

The final `lean/FiniteAdjoint.lean` source SHA is
`5161becb1c1f7bfa1af9018325a95f26b2d02dfe06801bc16c0f6e21e5ce9cd4`.
The elaborated `THEOREM_STATEMENTS.txt` SHA is
`7ad5b5d02a9e08559b4cbe3554d565ced3847e70baf6eba183835515f992953e`.
The `AXIOM_AUDIT.txt` SHA is
`5a1deed18592024abaa53515db4b33148ef9700fec3c59db1ce00bce377a1e3e`.

Actual command: `/usr/bin/python3 <this-directory>/verify.py`; subprocess:
`lake env lean <this-directory>/lean/FiniteAdjoint.lean`, cwd
`/home/cosmosapjw/lean_oracles/viii_oracle`, exit 0. The oracle supplies Lean
4.31.0 and mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, exactly matching
the contract pin. The primary `formal_mathlib/.lake/packages` symlink is broken;
it was left untouched. Full final compiler stdout/stderr and actual command,
version, source/config identities are in `compile_attempt_03.*`.

The disclosed oracle Lake manifest SHA is
`1a7cbb6b0487b078e2e5f768fc9e1bd78e2e36d0d896477cadf1d8971464db08`, which
differs from the frozen environment manifest SHA
`bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed`.
Thus this is a matching Lean/mathlib successor compilation, not exact frozen
environment replay or historical four-axis acceptance.

All nine declarations use only `propext`, `Classical.choice`, and `Quot.sound`.
The final source has no `sorry`, `admit`, or newly declared axiom. The first
failed source and exact failure excerpt are preserved, and the second failed
compile has full logs. See `FIRST_BLOCKER.md`; the first full stdout remains in
the native tool transcript, and is not misrepresented as a captured local log.

Author runtime requested: `gpt-6.1-sol/high`; observed: `UNKNOWN`.
No separate reviewer has yet examined this candidate. The parent owns review.
No commit, publication, historical ledger, or aggregate adjudication is performed
by this author.

The quick memory registry lookup for general Lean/toolchain guidance incidentally
displayed CAS11 historical status/scope summaries. No CAS11 receipt, source,
proof, or detailed result file was opened. No CAS12 sibling axis or historical
Lean source/result was read. The mathematics uses the frozen CAS12 inputs and
pinned mathlib library, with no copied historical proof/evidence. This exposure is
disclosed rather than claiming the session saw only the two neutral inputs.
The three parent-selected CAS11 prerequisite receipt paths and hashes are bound
in `RETURN.json`, after `sha256sum` matched each expected identity. Their contents
were not displayed or read as evidence; no CAS11 status is inferred or promoted
by this successor.

## Remaining boundary

CAS12 C02–C04, weighted-adjoint existence, BE integrability/dominated limits,
continuum q construction, derivative/integral interchange, continuum collision
semantics, and physical/scientific claims are not proved. Scientific admission
remains `HOLD`. Independent review and any aggregate acceptance remain separate.
Claim audit found no claim promotion or active Teff/TSC solver ownership.
