"""
htt/integration/to_mio.py — HTT → MIO Integration Adapter
=============================================================
C-16 deliverable. Constructs a PosteriorExportBundle from HTT outputs.

Reads the integrated_pipeline_results.json structure:
  departure[model]['layer_1_departure']['x'] → x posterior
  departure[model]['layer_2_occupancy']['Q'] → Q posterior
  departure[model]['layer_3_exceedance']['Pi'] → Pi exceedance
  evidence[model]['lnB'] → Bayes factor
  filling_fraction → F summary
"""
import sys, json
from pathlib import Path

__all__ = ['build_posterior_bundle']


def _get_nested(d, *keys, default=0.0):
    """Safely traverse nested dict."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, None)
        else:
            return default
        if d is None:
            return default
    return d


def build_posterior_bundle(results_path: str = None,
                           model: str = 'FLRW_tilt') -> 'PosteriorExportBundle':
    """Build a PosteriorExportBundle from HTT pipeline results.

    Parameters
    ----------
    results_path : str, optional
        Path to integrated_pipeline_results.json.
    model : str
        Reference model for posteriors (default: FLRW_tilt as best-fit).
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / 'workspace'))
    from contracts.htt_to_mio import PosteriorExportBundle

    if results_path is None:
        results_path = str(
            Path(__file__).resolve().parent.parent.parent.parent
            / 'workspace' / 'results' / 'integrated_pipeline_results.json'
        )

    with open(results_path) as f:
        data = json.load(f)

    dep = data.get('departure', {}).get(model, {})
    ev_model = data.get('evidence', {}).get(model, {})
    ff = data.get('filling_fraction', {})

    # Layer 1: x
    x_data = _get_nested(dep, 'layer_1_departure', 'x', default={})
    x_med = x_data.get('median', 0.0) if isinstance(x_data, dict) else 0.0
    x_68 = tuple(x_data.get('hpd_68', [0.0, 0.0])) if isinstance(x_data, dict) else (0.0, 0.0)
    x_95 = tuple(x_data.get('hpd_95', [0.0, 0.0])) if isinstance(x_data, dict) else (0.0, 0.0)

    # Layer 2: Q
    Q_data = _get_nested(dep, 'layer_2_occupancy', 'Q', default={})
    Q_med = Q_data.get('median', 0.0) if isinstance(Q_data, dict) else 0.0
    Q_68 = tuple(Q_data.get('hpd_68', [0.0, 0.0])) if isinstance(Q_data, dict) else (0.0, 0.0)

    # Layer 3: Pi (exceedance at threshold q*=0.05)
    Pi_data = _get_nested(dep, 'layer_3_exceedance', 'Pi', default={})
    if isinstance(Pi_data, dict):
        Pi_med = Pi_data.get('0.05', 0.0)
        Pi_68 = (Pi_data.get('0.1', 0.0), Pi_data.get('0.01', 1.0))
    else:
        Pi_med = 0.0
        Pi_68 = (0.0, 0.0)

    # Evidence
    ln_B = ev_model.get('lnB', 0.0) if isinstance(ev_model, dict) else 0.0
    model_evidences = {
        name: info.get('lnB', 0.0) if isinstance(info, dict) else 0.0
        for name, info in data.get('evidence', {}).items()
    }

    # Filling fraction
    F_med = ff.get('F_S3_mc_median', ff.get('F_S3_point', 0.0))
    F_68 = tuple(ff.get('F_S3_mc_68', [0.0, 0.0]))

    n_live = ev_model.get('neff', 500) if isinstance(ev_model, dict) else 500

    return PosteriorExportBundle(
        x_median=x_med, x_hpd68=x_68, x_hpd95=x_95,
        Q_median=Q_med, Q_hpd68=Q_68,
        Pi_median=Pi_med, Pi_hpd68=Pi_68,
        ln_B_total=ln_B, model_evidences=model_evidences,
        F_median=F_med, F_hpd68=F_68,
        n_live=n_live,
    )
