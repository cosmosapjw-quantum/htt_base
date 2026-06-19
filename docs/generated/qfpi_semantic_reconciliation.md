# Q/F/Pi Semantic Reconciliation

owner: COMMON
implementation_scope: semantic_firewall
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
config_hash: sha256:manual-rev-r076
input_hashes:
- htt/mio/formalism/normalized_score.py
- htt/mio/formalism/filling_fraction.py
- htt/mio/formalism/exceedance.py
- htt/htt/htt/infer/posterior_exceedance.py
- htt/htt/htt/departure/posterior_pushforward.py
- htt/htt/htt/core/departure_posteriors.py
- scripts/verify_formalism_figure_labels.py
sky_support_status: mixed_not_applicable_and_inherited
null_mock_status: mixed_not_applicable_and_inherited
generating_command: manual semantic reconciliation from REV-R076 tests
git_commit_or_worktree_state: pending_rev_r076_commit
caveats:
- not native transfer
- no family identification
- no geometry-detection claim
- MIO diagnostics do not create posterior odds, evidence, or truth certificates
- HTT posterior exceedance summaries are model-conditional and not MIO Pi

## Namespace Rules

| Quantity | Owner | Public name | Allowed meaning | Forbidden reading |
| --- | --- | --- | --- | --- |
| `Q` | MIO | policy-normalized diagnostic score | `x_C` under an explicit numerator and denominator policy | occupancy posterior, evidence, geometry/family label |
| `F` | MIO | certified filling fraction | sign-clean sample-wise filling under an admissible ceiling | posterior odds, material occupancy, clipped score |
| `Pi_MIO` | MIO | empirical diagnostic exceedance curve | registered threshold exceedance over Q/F diagnostic samples | posterior probability, p-value, HTT inference |
| `P_post` / `Pi_HTT` | HTT | model-conditional posterior exceedance | posterior pushforward exceedance over HTT samples | MIO diagnostic Pi, truth probability, model-family certificate |
| `G_F` | MIO | depth-gap diagnostic | binned filling-depth contrast with floor/split/null metadata | global-tilt confirmation or family evidence |

## Implemented Fences

- `htt.infer.posterior_exceedance.posterior_exceedance_summary` emits
  `quantity_name=P_post`, `owner=HTT`, and `mio_pi_compatible=false`.
- `mio.formalism.exceedance.build_exceedance_curve` rejects HTT posterior
  pushforward source kinds and reserved posterior/probability/evidence language.
- `scripts/verify_formalism_figure_labels.py` rejects MIO `Pi` rows whose
  `measure_kind` is `htt_posterior_pushforward_distribution`.
- Public manuscript/figure surfaces use policy-normalized `Q`, `Pi_MIO`, and
  `Pi_HTT` wording instead of Q occupancy or bare Pi across report boundaries.

## Verification

- `tests/htt/test_posterior_exceedance.py`
- `tests/mio/test_exceedance.py`
- `tests/contracts/test_qfpi_semantic_split.py`
- `tests/contracts/test_formalism_figure_labels.py`
- `scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json`
