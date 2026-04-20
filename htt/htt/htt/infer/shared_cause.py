"""
htt/infer/shared_cause.py — Shared-Cause vs Null Competition
=============================================================
P-16 deliverable. Implements the S2 (shared-cause) model and
M_null (independent systematics) for Bayes factor comparison.
"""
from dataclasses import dataclass
import hashlib
import json
import platform
from typing import Any, Mapping

import numpy as np

from common.sky_geometry import spherical_mean

__all__ = [
    'SharedCauseResult',
    'run_shared_cause_test',
    'shared_cause_report_artifact',
]


@dataclass(frozen=True)
class SharedCauseResult:
    """Result of shared-cause vs null comparison."""
    lnB_S2_vs_null: float
    S2_preferred: bool
    survives_ablation: bool
    direction_l: float
    direction_b: float
    amplitude: float
    classification: str  # 'decisive', 'strong', 'moderate', 'inconclusive'

    @property
    def is_decisive(self) -> bool:
        return self.lnB_S2_vs_null > 5


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for report configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _classify(delta: float) -> str:
    """Jeffreys-style qualitative label for lnB."""
    if delta > 5:
        return 'decisive'
    if delta > 2.5:
        return 'strong'
    if delta > 1:
        return 'moderate'
    return 'inconclusive'


def _fit_axis_amplitude(obs_data: dict) -> tuple[float, float, float]:
    """Fit a shared low-z axis/amplitude directly from observed surveys."""
    from .dipole_vector_likelihood import DipoleVectorLikelihood

    dp = obs_data['dipole_observations']
    cf4 = dp['cf4_watkins_2023']
    cw = dp['catwise_bohme_2025']
    radio = dp['radio_secrest_2021']

    direction_rows = [
        (
            'CF4',
            cf4.get('l_deg', DipoleVectorLikelihood.CF4_L),
            cf4.get('b_deg', DipoleVectorLikelihood.CF4_B),
            DipoleVectorLikelihood.CF4_SIGMA_DEG,
        ),
        (
            'CatWISE',
            cw.get('l_deg', DipoleVectorLikelihood.CW_L),
            cw.get('b_deg', DipoleVectorLikelihood.CW_B),
            DipoleVectorLikelihood.CW_SIGMA_DEG,
        ),
        (
            'Radio',
            radio.get('l_deg', DipoleVectorLikelihood.RADIO_L),
            radio.get('b_deg', DipoleVectorLikelihood.RADIO_B),
            DipoleVectorLikelihood.RADIO_SIGMA_DEG,
        ),
    ]
    l_vals = np.array([float(row[1]) for row in direction_rows], dtype=float)
    b_vals = np.array([float(row[2]) for row in direction_rows], dtype=float)
    w_dir = np.array([1.0 / float(row[3])**2 for row in direction_rows], dtype=float)
    mean = spherical_mean(l_vals, b_vals, w_dir)
    if np.isnan(mean['l_deg']) or np.isnan(mean['b_deg']):
        raise ValueError("shared-cause axis fit is degenerate")

    amplitude_rows = [
        (cf4['beta'], cf4['sigma']),
        (cw['eps1'], cw['sigma_stat']),
        (radio['eps1'], radio['sigma_stat']),
    ]
    values = np.array([float(row[0]) for row in amplitude_rows], dtype=float)
    sigmas = np.array([float(row[1]) for row in amplitude_rows], dtype=float)
    w_amp = 1.0 / sigmas**2
    amplitude = float(np.sum(w_amp * values) / np.sum(w_amp))
    return amplitude, float(mean['l_deg']), float(mean['b_deg'])


def _resolve_axis_amplitude(
    obs_data: dict,
    A_best: float | None,
    l_best: float | None,
    b_best: float | None,
) -> tuple[float, float, float, str]:
    """Resolve user-supplied and/or data-fitted shared-cause parameters."""
    fitted_A, fitted_l, fitted_b = _fit_axis_amplitude(obs_data)

    resolved_A = fitted_A if A_best is None else float(A_best)
    resolved_l = fitted_l if l_best is None else float(l_best)
    resolved_b = fitted_b if b_best is None else float(b_best)

    n_user = sum(value is not None for value in (A_best, l_best, b_best))
    if n_user == 0:
        fit_mode = 'weighted_data_fit'
    elif n_user == 3:
        fit_mode = 'user_supplied'
    else:
        fit_mode = 'hybrid_user_data_fit'
    return resolved_A, resolved_l, resolved_b, fit_mode


def _ablation_entries(
    obs_data: dict,
    A_best: float | None,
    l_best: float | None,
    b_best: float | None,
) -> list[dict[str, Any]]:
    """Per-survey ablation diagnostics for the shared-cause test."""
    from .dipole_vector_likelihood import DipoleVectorLikelihood
    from .matched_complexity import LowZAblation

    abl = LowZAblation(obs_data)
    entries: list[dict[str, Any]] = []
    for survey in ['CF4', 'CatWISE', 'Radio']:
        obs_mod = abl.ablate(survey)
        A_mod, l_mod, b_mod, fit_mode = _resolve_axis_amplitude(
            obs_mod,
            A_best=A_best,
            l_best=l_best,
            b_best=b_best,
        )
        dvl_mod = DipoleVectorLikelihood(obs_mod, control='C1')
        lnB_mod = (
            dvl_mod.directional_log_likelihood(l_mod, b_mod, A_mod)
            - dvl_mod.scalar_log_likelihood(0.0)
        )
        entries.append({
            'survey_removed': survey,
            'lnB_S2_vs_null': float(lnB_mod),
            'S2_preferred': bool(lnB_mod > 5.0),
            'fit_mode': fit_mode,
            'direction_l': float(l_mod),
            'direction_b': float(b_mod),
            'amplitude': float(A_mod),
        })
    return entries


def run_shared_cause_test(obs_data: dict,
                          A_best: float | None = None,
                          l_best: float | None = None,
                          b_best: float | None = None) -> SharedCauseResult:
    """Run the shared-cause vs null comparison.

    Uses the directional likelihood to compare:
      S2: single axis (l, b, A) explaining all surveys
      M_null: β = 0 with each survey noise-only
    """
    from .dipole_vector_likelihood import DipoleVectorLikelihood

    dvl = DipoleVectorLikelihood(obs_data, control='C1')
    A_fit, l_fit, b_fit, _ = _resolve_axis_amplitude(
        obs_data,
        A_best=A_best,
        l_best=l_best,
        b_best=b_best,
    )

    logL_S2 = dvl.directional_log_likelihood(l_fit, b_fit, A_fit)
    logL_null = dvl.scalar_log_likelihood(0.0)
    delta = logL_S2 - logL_null

    ablations = _ablation_entries(
        obs_data,
        A_best=A_best,
        l_best=l_best,
        b_best=b_best,
    )
    survives = all(entry['lnB_S2_vs_null'] >= 3.0 for entry in ablations)

    return SharedCauseResult(
        lnB_S2_vs_null=float(delta),
        S2_preferred=delta > 5,
        survives_ablation=survives,
        direction_l=l_fit,
        direction_b=b_fit,
        amplitude=A_fit,
        classification=_classify(float(delta)),
    )


def shared_cause_report_artifact(
    obs_data: dict,
    *,
    A_best: float | None = None,
    l_best: float | None = None,
    b_best: float | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``shared_cause_report_v1.json`` from the current low-z inputs."""
    result = run_shared_cause_test(
        obs_data,
        A_best=A_best,
        l_best=l_best,
        b_best=b_best,
    )
    _, _, _, fit_mode = _resolve_axis_amplitude(
        obs_data,
        A_best=A_best,
        l_best=l_best,
        b_best=b_best,
    )
    ablations = _ablation_entries(
        obs_data,
        A_best=A_best,
        l_best=l_best,
        b_best=b_best,
    )
    extra = dict(metadata or {})
    config_payload = {
        'A_best': A_best,
        'l_best': l_best,
        'b_best': b_best,
        'metadata': extra,
    }
    return _jsonify({
        'artifact_name': 'shared_cause_report_v1.json',
        'generated_by': extra.get(
            'generated_by',
            'htt.infer.shared_cause.shared_cause_report_artifact',
        ),
        'git_commit': extra.get('git_commit', ''),
        'config_hash': _config_hash(config_payload),
        'input_data_hashes': list(extra.get('input_data_hashes', [])),
        'random_seed': extra.get('random_seed'),
        'wall_time_sec': extra.get('wall_time_sec'),
        'python_version': extra.get('python_version', platform.python_version()),
        'numpy_version': extra.get('numpy_version', np.__version__),
        'claim_tier': extra.get('claim_tier', 'REPORT'),
        'scope_label': extra.get('scope_label', 'report'),
        'production_allowed': False,
        'fit_mode': fit_mode,
        'lnB_S2_vs_null': float(result.lnB_S2_vs_null),
        'S2_preferred': bool(result.S2_preferred),
        'survives_ablation': bool(result.survives_ablation),
        'direction_l': float(result.direction_l),
        'direction_b': float(result.direction_b),
        'amplitude': float(result.amplitude),
        'classification': result.classification,
        'ablation_checks': ablations,
    })
