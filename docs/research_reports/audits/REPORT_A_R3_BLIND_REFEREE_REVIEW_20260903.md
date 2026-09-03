# Report A R3 blind referee review

## Verdict

```text
MAJOR_REVISION_BOUNDED
/
THEORY_CORE_SURVIVES
/
FINITE_NULL_THEOREMS_MUST_BE_SEPARATED
/
PUBLICATION_LAYER_NEEDS_PROVENANCE_COMPRESSION
/
NO_OBSERVATIONAL_EXECUTION
```

The report has a coherent and potentially publishable theory/methods spine.
The tensor representation, cyclic-domain orbit theorem, conditional MES
functional interpretation, processed-response quotient, continuum/discrete
firewall, and conditional numerical-error theorem survive at their stated
evidence grades. The required revision is bounded and does not require a new
Planck or FFP10 run.

## P1 finding R3-STAT-01

The R2F candidate states the exchangeable-row rank theorem and a generic
randomization-group result as one formula over all observation/reference rows.
This is too broad. Group invariance validates ranking over the specified group
or a valid sample from that orbit; it does not make arbitrary external rows
exchangeable.

An exact two-state example invariant under the subgroup swapping rows 0 and 1
gives all-row p-values `1/4` and `1/2`, with

```text
P(p_all <= 1/2) = 1
size excess = 1/2.
```

The actual two-element group-orbit p-values are `1/2` and `1`, with zero
super-uniformity violation. The manuscript must state two separate theorems.

## P1 finding R3-STAT-02

The four-row adaptive-selection bullets call the 24 enumeration elements
“rows”. They are permutations. The mathematical counts are otherwise correct.

## P2 finding R3-WRITE-01

The abstract contains PR number, local test, and CI-status detail. That material
belongs in the provenance appendix, not the scientific abstract. The bounded
revision keeps the image condition and stable inverse idea but removes branch
metadata from the abstract.

## P2 finding R3-NOT-01

The photon energy symbol `epsilon` collides visually with the MES multipole
amplitudes `epsilon_l`. The revision uses `E_gamma` and fixes omitted tensor-index
spacing.

## Remaining publication tasks

1. Flatten the R3 candidate or its predecessor into the report branch.
2. Replace the appendix citation-key list with a formal bibliography.
3. Move detailed PR/test/CI status from the scholarly main text to the
   provenance appendix or an audit companion.
4. Add theory figures only after their source and caption claims are registered.
5. Perform a final fresh-context referee pass on the flattened exact head.

## Claim boundary

No observational result, empirical velocity, boost subtraction, global tilt,
physical shear/vorticity estimate, foreground cause, Bianchi-family
attribution, finite-HEALPix no-go, BASS solver claim, merge, or publication
approval is introduced.
