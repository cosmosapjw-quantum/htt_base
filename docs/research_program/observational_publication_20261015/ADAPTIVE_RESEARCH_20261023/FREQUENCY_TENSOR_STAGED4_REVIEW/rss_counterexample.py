"""Synthetic 32 MiB falsifier of sampled-RSS-as-peak, not a production rerun."""
import time
start=time.monotonic()
import json,mmap,pathlib,resource,sys
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r25_frequency_tensor_staged4')
import compute
baseline=compute.rss()
synthetic_cap=baseline+16*1024**2
compute.CAP_RSS=synthetic_cap
clock=compute.Clock(0);clock.begin()
with mmap.mmap(-1,32*1024**2) as block:
 for i in range(0,len(block),4096):block[i]=1
 transient_rss=compute.rss()
 # Production clock has no check during this live allocation interval.
clock.pause()
assert transient_rss>synthetic_cap
assert clock.peak_rss<synthetic_cap
print(json.dumps({'status':'COUNTEREXAMPLE_CONFIRMED','scope':'synthetic sampled RSS observer, no claim of production cap exceedance','baseline_rss_bytes':baseline,'synthetic_cap_bytes':synthetic_cap,'actual_observed_transient_rss_bytes':transient_rss,'clock_reported_peak_rss_bytes':clock.peak_rss,'wall_seconds':time.monotonic()-start,'process_hwm_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024},indent=2))
