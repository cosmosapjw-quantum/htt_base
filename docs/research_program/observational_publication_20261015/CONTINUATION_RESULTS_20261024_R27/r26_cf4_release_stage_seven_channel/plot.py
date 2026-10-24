#!/usr/bin/env python3
"""Render the actual conditional seven-channel response or its typed failure."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def render(out: Path) -> None:
    result = json.loads((out/'RESULT.json').read_text())
    response = result['response']
    if isinstance(response, dict):
        maps = response['maps']
        labels = list(maps)
        fig, axes = plt.subplots(1, len(labels), figsize=(5.2*len(labels), 5),
                                 constrained_layout=True)
        if len(labels) == 1:
            axes = [axes]
        scale = max(abs(x) for item in maps.values() for row in item['signed_M7_5x7'] for x in row)
        for ax, name in zip(axes, labels):
            M = np.asarray(maps[name]['signed_M7_5x7'])
            image = ax.imshow(M, cmap='RdBu_r', vmin=-scale, vmax=scale, aspect='auto')
            ax.set_xticks(range(7), response['channel_names'], rotation=50, ha='right')
            ax.set_yticks(range(5), [f'STF{i+1}' for i in range(5)])
            ax.set_title(name.replace('_', ' '))
            for i in range(5):
                for j in range(7):
                    ax.text(j, i, f'{M[i,j]:+.2g}', ha='center', va='center', fontsize=7)
        fig.colorbar(image, ax=axes, label='Fixed E1 derivative per mag')
        fig.suptitle('CF4 release-stage conditional signed response; Gamma7 and cross covariance unknown')
    else:
        fig, ax = plt.subplots(figsize=(11, 3), constrained_layout=True)
        ax.axis('off')
        ax.text(.03, .75, 'CF4 release-stage conditional result', fontsize=16, transform=ax.transAxes)
        ax.text(.03, .45, result['status'], fontsize=12, transform=ax.transAxes)
        ax.text(.03, .18, 'No seven-channel response is available; see RESULT.json for witnesses.',
                fontsize=10, transform=ax.transAxes)
    target = out/'response.png'
    if target.exists():
        raise FileExistsError(target)
    fig.savefig(target, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    render(parser.parse_args().out)
