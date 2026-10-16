# HTT six-paper READY sibling checkpoint / replay

Parent: `cosmosapjw-quantum/htt_base` PR #543 commit `eac75859f38bf223d5e5ee215ae0b65a1617ceaa`.
New publication branch: `research/htt-sixpaper-ready-siblings-20261016` (draft; no main merge).

Authoritative six-paper DAG final status after this checkpoint: **12/42 completed_scoped** (X01, X03, V01, K01, B01 newly completed), 30 pending, seven external_missing nodes. Pending independent ready queue: X02, L01, S02, K02. All six manuscripts remain NOT_READY_TO_SUBMIT. The 245-card engineering backlog was not modified.

Actual restored inputs:
- `inputs/htt_six_paper_h03/inputs/selected_source_observables.npz`, 35,970 CF4 groups, expected SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`.
- `inputs/source/*` restored from `archives/HTT_SIX_PAPER_P2_L01_FINITE_SOURCE_v1_20261016.zip`, original complete archive SHA256 `43cf6a29dea7cbece3e81f6367101db6c2e15b6f4f39b8e14f67baa888edbf0e`.
- `archives/S2_SOURCE_CONDITIONAL_FINAL.zip`, original complete archive SHA256 `303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219`.
- Ancestor P1/S01 archive remains separately available in the Library and has not been overwritten.

In a newly extracted directory, with Python 3.13, NumPy 2.3.5, pytest 9.0.2, run:

```sh
cd htt_sixpaper_next_20261016/outputs
python build_ready_ledgers.py
python source_conditioned_readiness.py
python run_v01_k01_demo.py
python -m pytest -q test_publication_frame_kinematics.py test_ready_ledgers.py test_source_conditioned_readiness.py
```

Record any dependency/version variations. No healpy, Astropy, full HTT-repository checkout, native Bianchi solver or physical likelihood is required for these scoped tests. These checks do **not** establish physical inference. Reported result JSONs are deterministic under the expected baseline.

The external Dropbox AniCLASS source ZIP was located by metadata only and not included as source bytes. Do not reclassify B02 as verified merely because an archive exists. `S02/L01` source physical missing inputs are explicitly retained.
