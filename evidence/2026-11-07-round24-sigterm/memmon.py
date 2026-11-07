"""Append cgroup memory.current, memory.events and the largest pytest RSS every 5 s."""
import sys, time, datetime, os
out, stop = sys.argv[1], sys.argv[2]
def rd(p):
    try: return open(p).read().strip().replace("\n", " ")
    except OSError as e: return f"ERR {e}"
def pytest_rss():
    best = (0, None)
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
            if b"pytest" in b" ".join(cmd[:4]):
                for line in open(f"/proc/{pid}/status"):
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1]); best = max(best, (kb, pid))
        except OSError: pass
    return f"pytest_max_rss_kb={best[0]} pid={best[1]}"
with open(out, "a", buffering=1) as f:
    while not os.path.exists(stop):
        f.write(f"{datetime.datetime.utcnow():%H:%M:%S} current={rd('/sys/fs/cgroup/memory.current')} "
                f"events=[{rd('/sys/fs/cgroup/memory.events')}] {pytest_rss()}\n")
        time.sleep(5)
