"""Read exact catalogued source bytes for a static, human-reviewed evidence pass.

Nothing is imported from the target project, extracted to disk, fetched or run.
Offline list generation does not call this reader.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import zipfile
from collections import OrderedDict


class SourceReader:
    def __init__(self, connection, limit=256 * 1024**2):
        self.c = connection
        self.limit = limit
        self.cache = {}
        self.archives = OrderedDict()

    def read(self, file_id):
        f = self.c.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
        if f is None:
            raise ValueError('unknown source file: ' + file_id)
        key = f['content_id'] or (f['source_id'], f['git_blob'] or f['id'])
        if key in self.cache:
            return self.cache[key]
        if f['bytes'] is None or f['bytes'] > self.limit:
            raise ValueError('source size unknown or over read limit: ' + f['path'])
        if f['container_id']:
            parent = self.c.execute('SELECT path FROM files WHERE id=?', (f['container_id'],)).fetchone()
            name = f['path'][len(parent['path']) + 2:]
            if name in self.archives.get(f['container_id'],{}):
                return self._checked(self.archives[f['container_id']][name],f,key)
            data = self.read(f['container_id'])
            buf = io.BytesIO(data)
            is_zip = zipfile.is_zipfile(buf)
            buf.seek(0)  # is_zipfile seeks; TAR must start at its original header.
            if is_zip:
                with zipfile.ZipFile(buf) as archive:
                    info = archive.getinfo(name)
                    if info.file_size > self.limit:
                        raise ValueError('archive member over read limit')
                    data = archive.read(info)
            else:
                container=f['container_id']
                if container not in self.archives:
                    wanted={r['path'][len(parent['path'])+2:] for r in self.c.execute('SELECT path FROM files WHERE container_id=? AND content_id IS NOT NULL',(container,))}
                    saved={};saved_bytes=0
                    with tarfile.open(fileobj=buf, mode='r:*') as archive:
                        for member in archive:
                            if member.name not in wanted or not member.isfile() or member.size>self.limit:continue
                            # Cache only catalogued text, never large observational
                            # members. A compressed TAR is traversed once per cache.
                            if saved_bytes+member.size>32*1024**2 and member.name!=name:continue
                            with archive.extractfile(member) as stream:saved[member.name]=stream.read(self.limit+1)
                            saved_bytes+=member.size
                    self.archives[container]=saved
                    while len(self.archives)>3:self.archives.popitem(last=False)
                if name in self.archives[container]:
                    data=self.archives[container][name]
                else:
                    buf.seek(0)
                    with tarfile.open(fileobj=buf,mode='r:*') as archive:
                        member=archive.getmember(name)
                        if not member.isfile() or member.size>self.limit:raise ValueError('archive member is not an allowed regular file')
                        with archive.extractfile(member) as stream:data=stream.read(self.limit+1)
        else:
            source = self.c.execute('SELECT * FROM sources WHERE id=?', (f['source_id'],)).fetchone()
            location = Path(source['locator'])
            if f['git_blob']:
                prefix = ['git', '-c', 'core.fsmonitor=false', '-c', 'log.showSignature=false']
                prefix += ['--git-dir', str(location)] if (location/'objects').is_dir() else ['-C', str(location)]
                data = subprocess.check_output(prefix + ['cat-file', 'blob', f['git_blob']],
                    stderr=subprocess.PIPE, env=dict(os.environ, GIT_NO_LAZY_FETCH='1'))
            else:
                target=location if source['kind']=='curated_navigation' else location/f['path']
                with target.open('rb') as stream:
                    data = stream.read(self.limit + 1)
        return self._checked(data,f,key)

    def _checked(self,data,f,key):
        if len(data) != f['bytes']:
            raise ValueError('source byte count differs: ' + f['path'])
        if f['content_id'] and hashlib.sha256(data).hexdigest() != f['content_id'].split(':')[0]:
            raise ValueError('source content differs from catalog: ' + f['path'])
        # Small text is reused across version/path aliases; large containers are
        # not retained so a long review does not accumulate an archive cache.
        if len(data) <= 8 * 1024**2:
            self.cache[key] = data
        return data
