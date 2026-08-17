import os, sys, time, json, subprocess
from importlib import import_module
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def is_valid_mp4(path: str) -> bool:
    try:
        proc = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return False
        duration = (proc.stdout or '').strip()
        return bool(duration) and duration not in {'N/A', '0'}
    except Exception:
        return False


vdir = os.path.join(PROJECT_ROOT, 'data', 'videos')
mp4s = [os.path.join(vdir, f) for f in os.listdir(vdir) if f.lower().endswith('.mp4')]
valid_mp4s = [p for p in mp4s if is_valid_mp4(p)]
if not valid_mp4s:
    print('NO_VALID_MP4S')
    sys.exit(1)
# pick the smallest valid mp4
valid_mp4s.sort(key=lambda p: os.path.getsize(p))
video = valid_mp4s[0]
print('SELECTED_VIDEO:', video)

# try to measure memory with psutil
try:
    import psutil
    ps = psutil.Process()
    mem_before = ps.memory_info().rss
except Exception:
    ps = None
    mem_before = None

# run pipeline
t0 = time.perf_counter()
t1 = t0
res = {}
success = False
try:
    orchestrator = import_module('app.services.orchestrator')
    t0 = time.perf_counter()
    res = orchestrator.process_video(video)
    success = True
except Exception as e:
    res = {'error': str(e)}
    success = False
finally:
    t1 = time.perf_counter()

if ps:
    mem_after = ps.memory_info().rss
else:
    mem_after = None

out = {
    'video': video,
    'success': success,
    'elapsed_s': t1 - t0,
    'memory_rss_before': mem_before,
    'memory_rss_after': mem_after,
    'result': res,
}
print(json.dumps(out, default=str, indent=2))
