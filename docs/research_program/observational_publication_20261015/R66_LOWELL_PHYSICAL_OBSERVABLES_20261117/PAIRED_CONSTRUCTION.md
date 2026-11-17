# Paired low-ell estimator construction — execution-corrected R66

This secondary construction was motivated by the observed lmax6/lmax8 change. It is exploratory; the primary n64_l6 estimator is retained. The original proposed005a temperature bank was rejected because its I fields arezero. No actual50/50 Commander calibration was performed.

Let z=[U^T q6; U^T q8] and J=[I4;I4]. The executed ideal Gaussian pixel reference supplies the full analytic covariance C8, including the shared physical quadrupole.4096 synthetic joint draws are split by immutable IDs into2048 training and2048 validation rows.

From training rows alone form S8=sum(z_i z_i^T)/2048 and

    W=(J^T S8^-1 J)^-1 J^T S8^-1.

The existing R58 conventional GLS implementation supplies this geometry. WJ=I4 preserves every common sky component exactly. Thus x=Wz=s+Weta when z=Js+eta; the cosmic realization is retained once. There is no doubling of independent skies or factor-of-two cosmic-variance reduction. Full cross terms remain in C8.

Since the ideal covariance is known, the selected conditional law uses

    C_W = W C8 W^T,
    -2 log L = (x-mu)^T C_W^-1 (x-mu) + log det C_W + constant.

The heldout2048 rows validate C_W; they do not replace it, estimate new physical errors, or create independent observational evidence. If only covariance-estimation rows were available, the zero-mean uncentered scatter would instead have N=2048 Wishart degrees and predictive F_(4,2045) scaling2045/(4*2048). That finite-N construction is tested, but the known-covariance Gaussian law is the selected actual analysis.

Executed results: WJ error2.22e-15, training covariance condition1529.64, covariance generalized eigenvalues relative to primary[0.9820665,0.9923945,0.9948141,1.0001179], ellipsoid volume ratio0.9847119. The heldout covariance differs from analytic C_W by0.0580092 in relative Frobenius norm. This small ~1.53% volume reduction does not establish a substantial improvement over conventional reconstruction. The actual PR4 combined quotient norm28.8619654microK remains a released-map proxy.

The exact mean response applies to the declared native physical quadrupole and rank-one downstream DQ family. It does not bind Commander foregrounds, spectra, DQ residual rank, beam or native high-mode response. A result selected after seeing real-data truncation sensitivity cannot be promoted to a discovery PTE. If future source-qualified data are used, freeze the estimator and target and make one independent bias/coverage comparison. Do not optimize repeatedly on the holdout.
