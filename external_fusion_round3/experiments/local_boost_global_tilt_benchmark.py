#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.discrimination import classify, fit_centroid_classifier, summarize_simulation  # noqa: E402
from htt_ext.lowell.shells import simulate_shell_poles  # noqa: E402
from htt_ext.types import ShellGrid, SourceModel  # noqa: E402


def main() -> int:
    grid = ShellGrid.from_redshifts([0.02, 0.08, 0.2, 0.45, 0.8, 1.3, 2.0])
    classes = [SourceModel.LOCAL_BOOST, SourceModel.GLOBAL_COHERENT, SourceModel.LOCAL_STRUCTURE, SourceModel.MIXTURE]
    train = {c.value: [] for c in classes}
    for c in classes:
        for seed in range(20260000, 20260080):
            train[c.value].append(summarize_simulation(simulate_shell_poles(grid, model=c, seed=seed)))
    clf = fit_centroid_classifier(train)
    confusion = {c.value: {d.value: 0 for d in classes} for c in classes}
    n_test = 0
    for c in classes:
        for seed in range(20261000, 20261050):
            summary = summarize_simulation(simulate_shell_poles(grid, model=c, seed=seed))
            pred, _ = classify(summary, clf)
            confusion[c.value][pred] += 1
            n_test += 1
    correct = sum(confusion[c.value][c.value] for c in classes)
    accuracy = correct / n_test
    status = "PASS" if accuracy >= 0.60 else "FAIL"
    print(json.dumps({"status": status, "accuracy": accuracy, "n_test": n_test, "confusion": confusion, "classifier": clf}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
