"""Read-only identity and Pantheon row-convention check for this source report."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[5]
DATA_DIR = Path(__file__).resolve().parent
PANTHEON = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f/Pantheon_SH0ES.dat')
D03 = REPO / 'docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D03_PANTHEON_CF4/results/host_SN.npz'
PROJECTION = REPO / 'docs/research_program/observational_publication_20261015/FRONTIER_20261020/projection/RESULT.json'
SOURCE_IDS = {'PANTHEON_DISTANCES_README', 'PANTHEON_ONLY_COSMOSIS_LIKELIHOOD',
              'PANTHEON_SHOES_COSMOSIS_LIKELIHOOD', 'CF4_SN_EDD_ALL_COMPILATION_NOTEBOOK'}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-root', type=Path, default=Path('/mnt/extdrive/workdir/htt_open_data/research20261022'))
    args = parser.parse_args()

    manifest = json.loads((DATA_DIR / 'ACQUISITION_MANIFEST.json').read_text())
    source_checks = []
    for spec in manifest['resources']:
        if spec['id'] not in SOURCE_IDS:
            continue
        path = args.raw_root / spec['path']
        receipt = json.loads(Path(str(path) + '.receipt.json').read_text())
        size, sha = path.stat().st_size, digest(path)
        assert size == spec['expected_bytes'] == receipt['bytes']
        assert sha == receipt['sha256'] and receipt['url'] == spec['url']
        source_checks.append({'id': spec['id'], 'bytes': size, 'sha256': sha})

    pantheon_receipt = json.loads(Path(str(PANTHEON) + '.receipt.json').read_text())
    assert digest(PANTHEON) == pantheon_receipt['sha256'] == '1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8'
    assert PANTHEON.stat().st_size == pantheon_receipt['bytes'] == 579283
    assert digest(D03) == json.loads(PROJECTION.read_text())['source_npz_sha256']

    with PANTHEON.open(newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter=' ', skipinitialspace=True))
    assert len(rows) == 1701
    for column in ('zHD', 'zCMB', 'zHEL', 'm_b_corr'):
        assert column in rows[0]

    with np.load(D03, allow_pickle=False) as data:
        indices = data['row_index'].copy()
        cached_cmb = data['zCMB'].copy()
    assert indices.shape == (651,) and np.issubdtype(indices.dtype, np.integer)
    assert len(np.unique(indices)) == 651 and min(indices) >= 0 and max(indices) < len(rows)

    all_hd = np.array([float(row['zHD']) for row in rows])
    all_cmb = np.array([float(row['zCMB']) for row in rows])
    assert np.array_equal(all_cmb[indices], cached_cmb)
    delta = all_hd - all_cmb
    selected_delta = delta[indices]
    result = {
        'source_checks': source_checks,
        'pantheon_sha256': digest(PANTHEON),
        'd03_sha256': digest(D03),
        'all_rows': len(rows),
        'all_zHD_ne_zCMB': int(np.count_nonzero(delta)),
        'd03_rows': len(indices),
        'd03_zHD_ne_zCMB': int(np.count_nonzero(selected_delta)),
        'd03_zHD_gt_0p01': int(np.count_nonzero(all_hd[indices] > 0.01)),
        'd03_median_abs_zHD_minus_zCMB': float(np.median(np.abs(selected_delta))),
        'd03_max_abs_zHD_minus_zCMB': float(np.max(np.abs(selected_delta))),
        'd03_zCMB_array_matches_original_table': True,
    }
    assert (result['all_zHD_ne_zCMB'], result['d03_zHD_ne_zCMB'], result['d03_zHD_gt_0p01']) == (1692, 645, 556)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
