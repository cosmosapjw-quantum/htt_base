# CAS17-C02/C03 source definition freeze

Successor source-recovery record only. It preserves rather than alters the
historical `c02_c03_scaling_conformal_input_blocker_v1_20261010` receipt.
It is not a Lean proof, four-axis verdict, or scientific admission.

## Frozen identities

| source | SHA-256 |
|---|---|
| `cas/contracts/CAS-17.json` | `123c73d56cf1c4d85acfce8536161011d4cb42b91f93e7bc0e3e67780296877e` |
| `supplements/DOSSIER_POSITIVE_BRIDGE.md` | `00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd` |
| `statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` |
| `ADDED_BOOK_INTEGRATION.md` | `977125a6efe3dc38f2eabb833b5feebe8e203752c58e6273e51b01edb3009dbf` |

## C02 constant-scale interface

The sources fix signature `(-,+,+,+)`, physical velocity `U=c u`, observer
`o`, sourceward unit direction `n`, and `K=-o+n`. For constant `lambda>0`,
`g_lambda=lambda^2 g`, `u_lambda=lambda^-1 u`,
`o_lambda=lambda^-1 o`, `n_lambda=lambda^-1 n`,
`K_lambda=lambda^-1 K`, and observer-normalized affine length
`r_lambda=lambda*r`.

They explicitly state invariance of `I=Z0=g(K,u)` and beta; scaling
`D_A,D_L` by `lambda`; and scaling the slope
`H=c*(partial z / partial D_A)|_0` by `lambda^-1`. Coordinate covariant
`B_ab=nabla_(a U_b)` scales by `lambda`, while measured orthonormal-tetrad
components scale by `lambda^-1`. Coordinate contravariant `A` scales by
`lambda^-2`, and its measured norm by `lambda^-1`.

`NATIVE_INFERENCE_THEOREMS.md` defines the common free calibration offset
`kappa` and gives `kappa'=kappa-5 log10(lambda)`. It defines `Kc,M2` as
length^-2 but distinct full-ray bounds: `Kc` bounds the optical tidal-operator
norm, while `M2` bounds `|d^2 Z/ds^2|` for affine `s`, with
`K(0)=-o+n`. `L` bounds that affine parameter. The source then distinguishes
affine `s_i` from area distance `r_i` through the displayed eta inequalities;
it does not identify them. Their common scaling is
`Kc'=lambda^-2 Kc`, `M2'=lambda^-2 M2`, `L'=lambda L`.

`D_L` is conditional on the documented reciprocity/transparency and
affine-normalization conditions. Nothing here yields a calibrated absolute
acceleration scale.

## C03 general-conformal interface

For smooth `phi`, the source fixes `g'=exp(2 phi) g`, `U'=exp(-phi) U`, and
`h^{ab}=g^{ab}+U^a U^b/c^2`, with local identity
`A'^a=exp(-2 phi)(A^a+c^2 h^{ab} nabla_b phi)`.

For the same eikonal covector, the measured frequency used at the endpoints
transforms as `nu'=exp(-phi) nu`; with this endpoint convention it fixes
`1+z'=exp(phi_o-phi_e)(1+z)`. These statements are not the constant-scale
case. In particular `phi(p)=0` need not remove the spatial-gradient correction,
and unparameterized null-path preservation does not preserve calibrated
finite-distance data.

## Exact remaining interface

The sources now bind the symbols and transformations. A kernel proof still
requires an actual formal Lorentz metric, Levi-Civita connection, endpoint/null
data, and measured-tetrad model. Assuming the displayed transformations as
Lean hypotheses would be circular and is not authorized.
