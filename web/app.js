// RAM hogs dashboard: polls /api/snapshot every second and animates the bars. H hides the header and footer (for recording).
const TOKEN = document.body.dataset.token, GB = 2 ** 30, ROW = 58, rows = new Map();
const $ = (id) => document.getElementById(id), list = $("apps");
function rowFor(name) {
  if (rows.has(name)) return rows.get(name);
  const li = document.createElement("li"); li.className = "app";
  const n = document.createElement("div"); n.className = "name"; const label = document.createElement("span"); label.textContent = name; const p = document.createElement("span"); p.className = "procs"; n.append(label, p);
  const t = document.createElement("div"); t.className = "track2"; const f = document.createElement("div"); f.className = "fill"; t.append(f);
  const g = document.createElement("div"); g.className = "gb";
  li.append(n, t, g); list.append(li); const r = { li, p, f, g }; rows.set(name, r); return r;
}
async function tick() {
  try {
    const s = await (await fetch("/api/snapshot", { headers: { "X-Token": TOKEN } })).json();
    $("used").textContent = (s.used / GB).toFixed(1); $("total").textContent = (s.total / GB).toFixed(1);
    const share = s.used / s.total; $("pct").textContent = Math.round(share * 100) + "% in use";
    const arc = $("arc"); arc.style.strokeDashoffset = String(314.16 * (1 - share)); arc.style.stroke = share > .85 ? "#C03A2B" : "#16120F";
    const apps = s.apps, max = apps.length ? apps[0].bytes : 1, seen = new Set();
    if (apps.length) { const a = apps[0]; $("top").innerHTML = ""; const b = document.createElement("b"); b.textContent = a.name;
      $("top").append("Biggest: ", b, ` · ${(a.bytes / GB).toFixed(2)} GB · ${a.procs} process${a.procs === 1 ? "" : "es"}`); }
    apps.forEach((a, i) => { const r = rowFor(a.name); seen.add(a.name);
      r.li.style.transform = `translateY(${i * ROW}px)`; r.li.classList.toggle("hog", i === 0); r.li.style.opacity = "1";
      r.f.style.width = `${Math.max(1.5, a.bytes / max * 100)}%`; r.g.textContent = `${(a.bytes / GB).toFixed(2)} GB`;
      r.p.textContent = `${a.procs} process${a.procs === 1 ? "" : "es"}`; });
    for (const [name, r] of rows) if (!seen.has(name)) { r.li.remove(); rows.delete(name); }
    list.style.height = `${apps.length * ROW}px`;
  } catch (e) { $("top").textContent = "Can't read memory: " + e.message; }
}
document.addEventListener("keydown", (e) => { if (e.key === "h" || e.key === "H") document.body.classList.toggle("hide"); });
tick(); setInterval(tick, 1000);
