import hashlib
import http.server
import json
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time
import unittest

sys.path.insert(0, '/mnt/extdrive/workdir/htt_open_data/r36_pr4_transfer_repair_preparation')
import fetch_commander_mc as m

ROOT = pathlib.Path(__file__).parent
PREFIX = (m.BASE / 'commander_sim0300_prefix.bin').read_bytes()


class Falsifiers(unittest.TestCase):
    def test_curl_start_record_failure_reaps_real_child(self):
        from unittest.mock import patch
        root=ROOT/'start_record_failure_fixture'; root.mkdir()
        (root/'cache').mkdir(); (root/'attempts').mkdir()
        release=threading.Event(); children=[]
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.send_header('Content-Type','image/fits'); self.end_headers()
                release.wait(10)
            def log_message(self,*a): pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever); thread.start()
        storage=m.Storage(root/'cache',fixture=True)
        item=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[300])[0]
        original_popen=m.subprocess.Popen; original_write=m.write_json
        def popen(*a,**k):
            child=original_popen(*a,**k); children.append(child); return child
        def write(path,value):
            if path.name=='CURL_START.json': raise OSError('fixture injected CURL_START fsync/write failure')
            return original_write(path,value)
        def opener(request,timeout):
            attempt=next((root/'attempts').iterdir())
            return m.CurlResponse(m.urllib.request.Request('http://127.0.0.1:'+str(server.server_port)),attempt,storage)
        try:
            with patch.object(m.subprocess,'Popen',popen),patch.object(m,'write_json',write):
                result=m.acquire(item,storage,root/'attempts',opener)
            self.assertEqual(result['status'],'ERROR')
            time.sleep(.1)
            observations=[{'pid':p.pid,'poll':p.poll(),'stat':pathlib.Path('/proc',str(p.pid),'stat').read_text() if pathlib.Path('/proc',str(p.pid),'stat').exists() else None} for p in children]
            (root/'OBSERVATION.json').write_text(json.dumps({'result':result,'children':observations},indent=2)+'\n')
            self.assertTrue(all(p.poll() is not None for p in children),'curl remains running after constructor record failure and ERROR return')
        finally:
            for child in children:
                if child.poll() is None: child.terminate()
                child.wait(timeout=5)
                child.stdout.close()
            release.set();server.shutdown();thread.join();server.server_close()

    def test_full_catalog_size_stream_and_late_prefix(self):
        root = ROOT / 'full_size_fixture'
        root.mkdir()
        cache = root / 'cache'; cache.mkdir()
        attempts = root / 'attempts'; attempts.mkdir()
        item = m.select(json.loads((m.BASE / 'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()), [300])[0]
        size = item['bytes']
        self.assertEqual(size, 603990720)
        original = PREFIX + b'z' * (2 * m.CHUNK + 17 - len(PREFIX))
        partial = cache / (item['filename'] + '.partial')
        partial.write_bytes(original)
        before = partial.stat()
        class Response:
            status = 200
            headers = {'Content-Type': 'image/fits'}
            def __init__(self): self.position = 0
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self, n):
                end = min(self.position + n, size)
                b = (PREFIX[self.position:end] if self.position < len(PREFIX) else b'')
                b += b'z' * (end - self.position - len(b))
                self.position = end
                return b
        result = m.acquire(item, m.Storage(cache, fixture=True), attempts, lambda *a, **k: Response(), runtime={'requested': 'gpt-6-sol/high', 'observed': 'UNKNOWN'})
        final = cache / item['filename']
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['network_bytes'], size)
        self.assertEqual(result['redundant_prefix_bytes'], len(original))
        self.assertEqual(result['appended_bytes'], size-len(original))
        self.assertEqual(final.stat().st_size, size)
        self.assertEqual(final.stat().st_ino, before.st_ino)
        self.assertEqual(m.digest(final), result['sha256'])
        self.assertEqual(m.digest(next(attempts.glob('*/response.bin'))), result['sha256'])
        self.assertEqual(result['executor_runtime']['requested'], 'gpt-6-sol/high')

    def test_sigterm_owned_parent_reaps_real_curl(self):
        root = ROOT / 'sigterm_fixture'; root.mkdir()
        (root / 'cache').mkdir(); (root / 'attempts').mkdir()
        ready = threading.Event(); release = threading.Event(); seen = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append({'version': self.request_version, 'headers': dict(self.headers)})
                self.send_response(200)
                self.send_header('Content-Type', 'image/fits')
                self.end_headers()
                self.wfile.write(PREFIX + b'z'*8192); self.wfile.flush()
                ready.set(); release.wait(20)
            def log_message(self, *a): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever); thread.start()
        code = '''import sys,pathlib,json,urllib.request
sys.path.insert(0,sys.argv[1])
import fetch_commander_mc as m
r=pathlib.Path(sys.argv[2]);s=m.Storage(r/'cache',fixture=True)
i=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[300])[0]
def opener(req,timeout):
    a=next((r/'attempts').iterdir())
    return m.CurlResponse(urllib.request.Request(sys.argv[3],headers=dict(req.header_items())),a,s)
print(json.dumps(m.acquire(i,s,r/'attempts',opener)),flush=True)
'''
        out=open(root/'worker.stdout','wb'); err=open(root/'worker.stderr','wb')
        worker = subprocess.Popen([sys.executable,'-B','-c',code,str(pathlib.Path(m.__file__).parent),str(root),'http://127.0.0.1:'+str(server.server_port)],stdout=out,stderr=err)
        curl_pid = None
        try:
            self.assertTrue(ready.wait(10), 'local request missing')
            deadline = time.monotonic()+5
            while time.monotonic()<deadline:
                starts=list((root/'attempts').glob('*/CURL_START.json'))
                if starts: break
                time.sleep(.02)
            start=json.loads(starts[0].read_text()); curl_pid=start['pid']
            self.assertEqual(seen[0]['version'], 'HTTP/1.0')
            self.assertEqual(seen[0]['headers']['Accept-Encoding'], 'identity')
            worker.send_signal(signal.SIGTERM)
            worker.wait(timeout=5)
            time.sleep(.4)
            stat_path=pathlib.Path('/proc')/str(curl_pid)/'stat'
            stat=stat_path.read_text() if stat_path.exists() else None
            info={'worker_pid':worker.pid,'worker_exit':worker.returncode,'curl_pid':curl_pid,'curl_stat_after_parent_exit':stat,'observed_request':seen[0],'curl_return_exists':(starts[0].parent/'CURL_RETURN.json').exists(),'attempt_return_exists':(starts[0].parent/'RETURN.json').exists()}
            (root/'OBSERVATION.json').write_text(json.dumps(info,indent=2)+'\n')
            self.assertIsNone(stat, 'owned curl survives terminated acquisition parent')
        finally:
            if worker.poll() is None: worker.kill(); worker.wait()
            if curl_pid and pathlib.Path('/proc',str(curl_pid)).exists():
                os.kill(curl_pid,signal.SIGTERM)
            out.close(); err.close()
            release.set(); server.shutdown(); thread.join(); server.server_close()


if __name__ == '__main__': unittest.main(verbosity=2)
