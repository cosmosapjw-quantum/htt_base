# OBS-05 independent review

Decision after targeted repair: `PASS_SCOPED_DIAGNOSTIC_REPAIR`. The matched DESI BGS DR1 v1.2 data/window/covariance summary and controller-selected descriptive design are reproducible. Physical baseline reproduction, catalogue low-mode response, calibrated inference, and full OBS-05 acceptance remain `HOLD`.

The independent read-only reviewer did not author or repair the candidate. Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: `UNKNOWN`. Original author request: `gpt-6.1-sol/medium`; targeted repair used an existing `gpt-5.6-terra/medium` agent; observed runtime identities: `UNKNOWN`.

Review found and closed three points: optional HDF5 test now skips without h5py (system pytest 3 passed, 1 skipped; supplied lowell interpreter 4 passed); ownership separates obsstat reader/window diagnostics from HTT descriptive GLS coefficient, covariance, and residual; controller selection is documented as occurring before this run without claiming package preregistration. The reviewer recomputed all 24 stored numeric outputs. The design rank is 3, residual dimension 23, and squared residual norm is 55.372989720482785. The initial test failure is preserved in the first review tool output and summarized in `execution.json`; its summary is not a separate raw log.

Reviewed SHA-256: script `4982bc53e34cc1f260d6824cad2ef628be27803454dc64481dc20cdfc2416cc9`, tests `fb7a674d4949d473e553e40d71f3cb92c4d16d0bd41d7f4b37517f1ded109303`, summary `e44f1109dffa84196d94a712d67ea30336b54beb0c4e7a7b4471230ef32a2ffe`, execution `870f7ba45a6d2cc4c904f069c1ae623f2c8663c0d29146bcf07406a8eecbd494`.

The Gaussian low-mode template and polynomial columns are diagnostic choices. The residual is not a calibrated goodness-of-fit statistic or detection claim. Embedded theory zeros are placeholders, and no duplicate likelihood is formed from overlapping data.
