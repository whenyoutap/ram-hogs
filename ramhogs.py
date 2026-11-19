#!/usr/bin/env python3
"""RAM hogs: which apps are using your computer's memory right now, processes grouped by name. Offline, read-only (it never closes anything).

    python ramhogs.py            the live dashboard in your browser (this computer only)
    python ramhogs.py --list     print the top apps once, in the terminal
    python ramhogs.py --watch    the terminal list, refreshed every 2 seconds

Every app is one line, all its processes added up (Chrome runs dozens). Windows, macOS and Linux. Python 3.8+, standard library only.
"""
import argparse, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ramhogs import engine  # noqa: E402

GB = 2 ** 30


def table(s, top):
    used, total = s["used"], s["total"]
    lines = [f"RAM in use: {used / GB:.1f} of {total / GB:.1f} GB ({used / total:.0%})", ""]
    if not s["apps"]: return "\n".join(lines + ["(no processes could be read)"])
    width = max(len(a["name"]) for a in s["apps"][:top])
    for a in s["apps"][:top]:
        share = a["bytes"] / total; bar = "#" * max(1, round(share * 60))
        lines.append(f"{a['name']:<{width}}  {a['bytes'] / GB:5.2f} GB  {share:5.1%}  {bar}  ({a['procs']} process{'es' if a['procs'] != 1 else ''})")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Which apps are using your RAM. Offline and read-only.")
    ap.add_argument("--list", action="store_true", help="print the top apps once")
    ap.add_argument("--watch", action="store_true", help="keep printing every 2 seconds")
    ap.add_argument("--top", type=int, default=10, help="how many apps to show (default 10)")
    ap.add_argument("--port", type=int, default=8767, help="dashboard port (default 8767)")
    ap.add_argument("--no-browser", action="store_true", help="don't open the browser")
    a = ap.parse_args()
    if a.top < 1: ap.error("--top must be 1 or more")
    if a.list: return print(table(engine.snapshot(), a.top))
    if a.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear"); print(table(engine.snapshot(), a.top)); time.sleep(2)
        except KeyboardInterrupt: return
    from ramhogs import server
    server.serve(a.port, not a.no_browser, top=max(a.top, 12))


if __name__ == "__main__":
    main()
