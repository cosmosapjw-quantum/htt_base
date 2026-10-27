"""Recheck the exact public archive intake without executing any cosmology code.

Run: python validate_intake.py /mnt/extdrive/workdir/htt_open_data/r36_atlas_actual
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import zipfile


PREP = Path('/mnt/extdrive/workdir/htt_open_data/r36_atlas_source_preparation')
PREP_SHA256 = 'ffc338ebfb0ed7d8cc5b2d4f8d15c3f0e2762985c93c8e7cc2a267987275d576'
ARCHIVES = (
    'anilos-0.1.0.whl', 'anilos-0.1.0.tar.gz',
    'all_decoupled_plots.zip', 'all_coupled_plots.zip',
    'all_coupled_chains.zip', 'all_decoupled_chains.zip',
)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def archive_members(path):
    if path.name.endswith('.tar.gz'):
        with tarfile.open(path, 'r:gz') as a:
            return [(m.name, m.size) for m in a.getmembers()]
    with zipfile.ZipFile(path) as a:
        return [(m.filename, m.file_size) for m in a.infolist()]


def nested_anilos(path):
    data = path.read_bytes()
    layers = []
    for depth in range(16):
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as a:
            members = a.getmembers()
            nested = [m for m in members if m.isfile() and m.name.endswith('.tar.gz')]
            numeric = [m.name for m in members if m.isfile() and m.name.lower().endswith(('.fits', '.fit', '.npy', '.npz', '.h5', '.hdf5', '.csv', '.dat'))]
            layers.append({'depth': depth, 'compressed_bytes': len(data), 'members': len(members), 'numeric_paths': numeric})
            if not nested:
                return layers
            if len(nested) != 1:
                raise AssertionError('multiple unclassified nested distributions')
            data = a.extractfile(nested[0]).read()
    raise AssertionError('nested distribution depth exceeded')


def main(root):
    assert sha256(PREP/'PREPARATION_RETURN.json') == PREP_SHA256
    receipts = json.loads((root/'downloads.json').read_text())
    assert set(x['path'].rsplit('/', 1)[-1] for x in receipts) == set(ARCHIVES)
    by_name = {Path(x['path']).name: x for x in receipts}
    inventories = {}
    for name in ARCHIVES:
        receipt = by_name[name]
        path = root/'downloads'/name
        assert path.resolve() == Path(receipt['path']).resolve()
        assert receipt['integrity_pass'] and path.stat().st_size == receipt['bytes']
        assert sha256(path) == receipt['sha256']
        saved = json.loads((root/(name+'.inventory.json')).read_text())['members']
        actual = archive_members(path)
        assert actual == [(m['path'], m['size']) for m in saved], name
        inventories[name] = saved

    plots = {}
    for name in ('all_decoupled_plots.zip', 'all_coupled_plots.zip'):
        substantive = [m for m in inventories[name] if m['kind']=='file' and not m['path'].startswith('__MACOSX/')]
        assert substantive and all(m['path'].endswith('.pdf') for m in substantive)
        plots[name] = len(substantive)

    chains = {}
    for name in ('all_coupled_chains.zip', 'all_decoupled_chains.zip'):
        prefix = 'chains/' if name.startswith('all_coupled') else 'decoupled_chains/'
        substantive = [m for m in inventories[name] if m['kind']=='file' and m['path'].startswith(prefix) and m['path'].endswith('.txt')]
        assert substantive
        other = [m['path'] for m in inventories[name] if m['kind']=='file' and not m['path'].startswith('__MACOSX/') and not m['path'].endswith('.DS_Store') and m not in substantive]
        assert not other, other
        with zipfile.ZipFile(root/'downloads'/name) as a:
            columns = {}
            for m in substantive:
                with a.open(m['path']) as f:
                    row = f.readline().split()
                assert len(row) == 20 and all(float(v)==float(v) for v in row)
                columns[m['path']] = len(row)
        chains[name] = {'files': len(substantive), 'first_row_columns': columns}

    wheel = [m['path'] for m in inventories['anilos-0.1.0.whl'] if m['kind']=='file']
    assert all(p.endswith(('.py','.so','.c','.pyx','.txt','.md','.dist-info/METADATA','.dist-info/WHEEL','.dist-info/RECORD','LICENSE')) for p in wheel)
    layers = nested_anilos(root/'downloads'/'anilos-0.1.0.tar.gz')
    assert len(layers)==5
    assert layers[0]['numeric_paths'] == ['anilos-0.1.0/examples/time_case1.npy','anilos-0.1.0/examples/time_case2.npy']
    assert all(not x['numeric_paths'] for x in layers[1:])
    with tarfile.open(root/'downloads'/'anilos-0.1.0.tar.gz', 'r:gz') as a:
        timing_hashes = {}
        for case in (1, 2):
            name = f'time_case{case}.npy'
            member = a.getmember(f'anilos-0.1.0/examples/{name}')
            archive_bytes = a.extractfile(member).read()
            timing_hashes[name] = hashlib.sha256(archive_bytes).hexdigest()
            assert archive_bytes == (PREP/'responses'/f'anilos_{name}').read_bytes()

    trees = {}
    for name, expected in [('anilos_pinned_tree.json',42),('vicente_aniclass_tree.json',314),('bianchi_tree.json',68)]:
        d = json.loads((PREP/'responses'/name).read_text())
        assert d['truncated'] is False and len(d['tree'])==expected
        trees[name] = expected

    candidates = json.loads((root/'aniclass_numeric_candidates.json').read_text())
    assert len(candidates)==4
    assert all(sha256(Path(c['path']))==c['sha256'] for c in candidates)
    zenodo54 = json.loads((PREP/'responses/zenodo48654.json').read_text())
    movies = [f['key'] for f in zenodo54['files']]
    assert len(movies)==4 and all(n.endswith('.mp4') for n in movies)

    return {
        'status':'SOURCE_INVENTORY_CHECK_PASS_SCIENCE_HOLD',
        'archive_count':len(ARCHIVES),
        'archive_sha256':{n:by_name[n]['sha256'] for n in ARCHIVES},
        'plot_pdf_counts':plots,
        'chain_files':chains,
        'anilos_distribution_layers':layers,
        'anilos_timing_npy_sha256':timing_hashes,
        'complete_tree_entries':trees,
        'anilos_wheel_members':len(wheel),
        'aniclass_numeric_candidate_paths':[c['source'] for c in candidates],
        'zenodo48654_movie_files':movies,
        'qualified_external_atlas':False,
        'reason':'Verified files are code/distribution, benchmark timing arrays, input/history tables, posterior chains, plots or movies; no source-described all-m T/E/B coefficient payload with required conventions was found.'
    }


if __name__=='__main__':
    print(json.dumps(main(Path(sys.argv[1])), indent=2))
