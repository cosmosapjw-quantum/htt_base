"""
htt/core/pipeline_config.py — Pipeline Configuration
======================================================
Extracted from pipeline.py so it can be imported without
triggering the 800-line monolithic execution.
"""
import os
from dataclasses import dataclass

__all__ = ['PipelineConfig']


@dataclass
class PipelineConfig:
    """Configurable pipeline settings. Replaces hardcoded paths."""
    output_dir: str = os.environ.get('HTT_OUTPUT_DIR', '/mnt/user-data/outputs')
    obs_defaults_path: str = None  # None = auto-detect via ssot
    cf4_version: str = 'wfh2009'
    skip_evidence: bool = False
    skip_figures: bool = False
    skip_departure: bool = False
    quick: bool = False

    @property
    def obs_file(self) -> str:
        """Map cf4_version to obs_defaults filename."""
        _map = {
            'wfh2009': 'obs_defaults.json',
            'watkins2023': 'obs_defaults_watkins2023.json',
            'courtois2025': 'obs_defaults_CF4pp.json',
        }
        return self.obs_defaults_path or _map.get(self.cf4_version, 'obs_defaults.json')
