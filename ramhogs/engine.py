"""Which apps are using your RAM. One call, snapshot(), returns the total and available memory and every app with its memory,
summed over all its processes (Chrome runs dozens; they show as one line). Read-only: nothing is closed or changed.

Windows: `tasklist` (the working set of each process) and GlobalMemoryStatusEx. Linux: /proc (RssAnon, anonymous resident memory)
and /proc/meminfo. macOS: `ps` per process, `sysctl` and `vm_stat` for the total. Processes are grouped by name; an app's helpers
with other names show as their own lines.
Memory shared between processes is counted in each one, so an app's sum can be a little higher than Task Manager's
"Memory" column. Standard library only.
"""
import csv, io, os, platform, re, subprocess, time


def _windows_memory():
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullTotalPhys, m.ullAvailPhys


def parse_tasklist(text):
    """`tasklist /fo csv /nh` -> [(name, bytes)]. Mem Usage looks like "123,456 K" (or "123.456 K" in other locales)."""
    out = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 5: continue
        digits = re.sub(r"\D", "", row[4])
        if digits: out.append((row[0], int(digits) * 1024))
    return out


def parse_meminfo(text):
    v = {k: int(n) * 1024 for k, n in re.findall(r"^(\w+):\s+(\d+) kB", text, re.M)}
    return v["MemTotal"], v.get("MemAvailable", v.get("MemFree", 0))


def _linux_procs():
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try:
            st = open(f"/proc/{pid}/status").read()
        except OSError:
            continue
        name, rss = re.search(r"^Name:\s+(.+)$", st, re.M), re.search(r"^RssAnon:\s+(\d+) kB", st, re.M)   # private memory; VmRSS also counts mapped files the OS can drop
        if name and rss: out.append((name[1].strip(), int(rss[1]) * 1024))
    return out


def app_name(proc):
    """Group helpers under the app people know: chrome.exe -> Chrome, msedgewebview2.exe -> Edge WebView."""
    n = re.sub(r"\.(exe|app)$", "", proc.strip(), flags=re.I)
    known = {"msedge": "Edge", "msedgewebview2": "Edge WebView", "chrome": "Chrome", "firefox": "Firefox", "code": "VS Code", "discord": "Discord",
             "slack": "Slack", "teams": "Teams", "ms-teams": "Teams", "spotify": "Spotify", "whatsapp": "WhatsApp", "explorer": "File Explorer",
             "vmmem": "WSL / virtual machines", "vmmemwsl": "WSL / virtual machines", "memory compression": "Memory compression (Windows)",
             "searchhost": "Windows Search", "brave": "Brave", "opera": "Opera", "zoom": "Zoom", "obs64": "OBS"}
    return known.get(n.lower(), n)


def group(procs, top=None):
    apps = {}
    for name, b in procs:
        a = apps.setdefault(app_name(name), {"name": app_name(name), "bytes": 0, "procs": 0})
        a["bytes"] += b; a["procs"] += 1
    ranked = sorted(apps.values(), key=lambda a: -a["bytes"])
    return ranked[:top] if top else ranked


def snapshot(top=None):
    sysname = platform.system()
    if sysname == "Windows":
        text = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        procs, (total, avail) = parse_tasklist(text), _windows_memory()
    elif sysname == "Linux":
        procs, (total, avail) = _linux_procs(), parse_meminfo(open("/proc/meminfo").read())
    elif sysname == "Darwin":
        ps = subprocess.run(["ps", "-axo", "rss=,comm="], capture_output=True, text=True).stdout
        procs = [(os.path.basename(c), int(r) * 1024) for r, c in re.findall(r"^\s*(\d+)\s+(.+)$", ps, re.M)]
        total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip())
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout   # the system's own page counts, not a sum of processes
        page = int((re.search(r"page size of (\d+)", vm) or [0, 4096])[1]); pages = lambda k: int((re.search(rf"{k}:\s+(\d+)", vm) or [0, 0])[1])
        avail = (pages("Pages free") + pages("Pages inactive") + pages("Pages speculative")) * page
    else:
        raise RuntimeError(f"unsupported system: {sysname}")
    return {"t": time.time(), "system": sysname, "total": total, "available": avail, "used": total - avail, "apps": group(procs, top)}
