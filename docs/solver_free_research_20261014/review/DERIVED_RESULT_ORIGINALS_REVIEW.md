# Derived result originals: independent scope review

- Scope: byte publication receipt for analyzed/generated files in three `results/` roots; scientific inference and historical Git removal were outside this review.
- Source commit/tree: `cc7cdcbfeb00b87a9acdf2cbd950f55a45447e42` / `2972e86e536a0b4571e9c55dd52a9cd6c98adc67`.
- Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: `UNKNOWN`. The reviewer was read-only and separate from the writer.
- First finding: `gaia_frame_v1/qualified_rows.npz` copied source IDs, positions and proper motions for all 4,756 downloaded Gaia rows. It was removed from the new inventory. Its historical Git blob remains in the source commit.
- Final scoped decision: PASS for inventory publication. The 836 included files (118,433,377 bytes) matched their source Git blobs, sizes and SHA-256 digests; 527 NPZ files passed full ZIP CRC. Canonical entry digest: `b6068511805ddfcc4078089a3735b9e5ca74269a298b74874288fab6d0fe37ed`.
- The reviewer found no other standalone row-level observational catalogue in the selected roots. Some retained analysis files include published compressed observed summaries such as Union3 bins or CMB bandpowers; their status is stated in the inventory. Raw inputs under `workdir/raw` are excluded.
- Reviewed candidate SHA-256: `DERIVED_RESULT_ORIGINALS.json` = `491d195f422d609daf9c3e126e659ecdb3beca5bf3771d713c121ec286213235`; `DELIVERY.json` = `a10b26eac552984cff70ff9ca393291611e26241a3b6c035cbed24f7911ed92b`; `CODEX_HANDOFF_KO.md` = `1c1b690a44099a9d5e1b0b350db8b9916fa6fef3faf326dde9045b778c139e40`.
- Claim boundary: byte identity and publication scope only. No new empirical survey-law admission, independent likelihood, native transfer or physical detection follows.
