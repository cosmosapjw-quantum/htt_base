"""Plots for the frozen source-only diagnostic; invoked within science budget."""
from pathlib import Path


def plot_summary(summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    output = Path(output)
    metadata = summary["metadata"]
    footer = ("obsstat | C0 | non-claim-bearing source diagnostic | transfer: none\n"
              "Allowed: frozen SDSS source sample; null: source-only, independence NOT_CERTIFIED\n"
              "Covariance: DIAGONAL_WORKING + empirical; forbidden: physical/H02 coverage, CF4 joint law, family identification")
    labels = [f"{window}: {basis}" for window in ("U", "G") for basis in summary["basis"]]
    figures = []
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    x = np.arange(16)
    axes[0].errorbar(x, summary["coefficient_means_mag"], yerr=summary["coefficient_scatter_mag"], fmt="o", capsize=2)
    axes[0].axhline(0, color="black", lw=.7)
    axes[0].set(ylabel="Coefficient mean ± source-box scatter [mag]", title="Uncentered source coefficients")
    axes[1].plot(x, summary["empirical_to_mean_working_variance_ratio"], "o")
    axes[1].axhline(1, color="black", lw=.7)
    axes[1].set(ylabel="Empirical / mean working variance", title="Finite source sample variance ratios")
    for ax in axes:
        ax.set_xticks(x, labels, rotation=90)
    figures.append((fig, "COEFFICIENTS_AND_VARIANCE"))
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(np.asarray(summary["empirical_correlation"], dtype=float), vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(x, labels, rotation=90)
    ax.set_yticks(x, labels)
    ax.set_title("Empirical coefficient correlation; shared windows retained")
    fig.colorbar(im, ax=ax, label="Finite source sample correlation")
    figures.append((fig, "EMPIRICAL_CORRELATION"))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(np.arange(64), summary["T_descriptive"], "o", ms=3)
    ax.axhline(summary["descriptive_threshold"], color="black", linestyle="--", label="Fixed descriptive threshold")
    ax.set(xlabel="Frozen numerically ordered distinct-box index, observer Y0", ylabel="Raw T (no bias centering)",
           title=f"Descriptive exceedances: {summary['K_exceeding_descriptive_threshold']}/64; coverage NOT_CALIBRATED")
    ax.legend()
    figures.append((fig, "RAW_T_DESCRIPTIVE"))
    for fig, stem in figures:
        fig.text(.02, .015, footer, fontsize=6)
        fig.tight_layout(rect=(0, .12, 1, 1))
        for extension in ("png", "pdf"):
            target = output / f"{stem}.{extension}"
            # Open exclusively; never replace an earlier candidate.
            with target.open("xb") as stream:
                fig.savefig(stream, format=extension, dpi=170,
                            metadata={"Title": "SDSS source-only diagnostic", "Creator": metadata["owner"]})
        plt.close(fig)
