import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ramhogs import engine


class T(unittest.TestCase):
    def test_tasklist_parse_and_group(self):
        text = '"chrome.exe","1","Console","1","210,000 K"\n"chrome.exe","2","Console","1","90.000 K"\n"Code.exe","3","Console","1","300,000 K"\n"bad"\n'
        procs = engine.parse_tasklist(text)
        self.assertEqual(procs, [("chrome.exe", 210000 * 1024), ("chrome.exe", 90000 * 1024), ("Code.exe", 300000 * 1024)])
        g = engine.group(procs)
        self.assertEqual([(a["name"], a["procs"]) for a in g], [("Chrome", 2), ("VS Code", 1)])   # Chrome 300,000 K ties VS Code: stable sort keeps first
        self.assertEqual(g[0]["bytes"], 300000 * 1024)

    def test_meminfo(self):
        self.assertEqual(engine.parse_meminfo("MemTotal:  1000 kB\nMemFree: 10 kB\nMemAvailable:   400 kB\n"), (1024000, 409600))

    def test_top(self):
        self.assertEqual(len(engine.group([(f"p{i}", i) for i in range(20)], top=5)), 5)

    def test_snapshot_here(self):
        s = engine.snapshot(top=5)
        self.assertGreater(s["total"], 0); self.assertLessEqual(len(s["apps"]), 5); self.assertGreaterEqual(s["used"], 0)


if __name__ == "__main__":
    unittest.main()
