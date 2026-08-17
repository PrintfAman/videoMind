import os, sys, time, json
from importlib import import_module

vdir = os.path.join(os.getcwd(), 'data', 'videos')
mp4s = [os.path.join(vdir,f) for f in os.listdir(vdir) if f.lower().endswith('.mp4')]
if not mp4s:
    print('NO_MP4S')
    sys.exit(1)
# pick smallest
mp4s.sort(key=lambda p: os.path.getsize(p))
video = mp4s[0]

# try to measure memory with psutil
try:
    import psutil
    ps = psutil.Process()
    mem_before = ps.memory_info().rss
except Exception:
    ps = None
    mem_before = None

# run pipeline
result = {}
try:
    orchestrator = import_module('app.services.orchestrator')
    timings = {}
    # we can instrument per-stage timings from the pipeline results
    t0 = time.perf_counter()
    res = orchestrator.process_video(video)
    t1 = time.perf_counter()
    result['success'] = True
    result['elapsed_s'] = t1 - t0
    result['result'] = res
except Exception as e:
    result['success'] = False
    result['error'] = str(e)

if ps:
    mem_after = ps.memory_info().rss
else:
    mem_after = None

report = {
    'video': video,
    'memory_before': mem_before,
    'memory_after': mem_after,
    'report': result,
}
out_path = os.path.join(os.getcwd(), 'validation_result.json')
with open(out_path, 'w', encoding='utf-8') as fh:
    json.dump(report, fh, indent=2)
print('WROTE', out_path)
