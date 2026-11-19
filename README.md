# RAM hogs

Shows which apps are using your computer's memory right now, as a live dashboard or a list in the terminal. Processes with the
same name are added up on one line: Chrome alone often runs 30 or more (tabs, extensions and helpers run as separate processes). It runs entirely on your computer and only reads;
it never closes or changes anything.

## Run it

You need Python 3.8 or newer ([python.org](https://www.python.org/downloads/)). Nothing else to install.

```
python ramhogs.py
```

Your browser opens the dashboard: total memory in use, and the apps using the most, updated every second.

```
python ramhogs.py --list     print the top 10 once
python ramhogs.py --watch    keep the list updating in the terminal
python ramhogs.py --top 20   show more apps
```

Press `H` on the dashboard to hide the header and footer (for a screen recording).

## What to do with it

Close the app at the top if you don't need it, from its own window or Task Manager (Windows), Activity Monitor (macOS) or
`kill` (Linux). Browsers often top the list because they split work into many processes.

## How it measures

- Windows: `tasklist` (each process's working set) and the system's own memory total.
- macOS: `ps` for each process; `sysctl` and `vm_stat` for the total.
- Linux: each process's anonymous resident memory (`RssAnon` in /proc); the total from /proc/meminfo.

Memory shared between processes of the same app counts in each one, so an app can show a little more than Task Manager's
Memory column. The total in use comes from the operating system. Sizes are in binary gigabytes (1 GB = 1024³ bytes), as Windows shows them.

## Privacy

No internet, no telemetry, no accounts. The dashboard listens on 127.0.0.1 only. The memory data needs a random token made
for this run, and requests whose Host or Origin isn't this dashboard are refused. It shows app names only, never window titles or file names.

## Tests

```
python tests/test_engine.py
```
