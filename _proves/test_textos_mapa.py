# Mapes de l'informe: cap text d'una zona s'encavalca amb el d'una altra (franges de penetració i de 6-9 m, números de dues xifres)
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7, 9)]
ZONES = ["EE", "PE", "PC", "PD", "ED", "6E", "6C", "6D", "9E", "9C", "9D"]
acts = []; i = 0
for e in ("N", "R"):
    for z in ZONES:
        for k in range(25):
            i += 1; acts.append({"i": i, "t": 10 * (i % 340), "p": 1 + i % 2, "e": e, "d": [3, 5, 7, 9][k % 4] if e == "N" else 6, "a": "G" if k < 16 else "A", "k": None, "z": z, "g": 1 + k % 9, "s": None, "gk": 1, "rgk": 16})
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-15", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 6, "n": "Rival"}], "acts": acts, "seq": i, "squad": [1, 3, 5, 7, 9], "upd": 1}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": i, "upd": 1, "sc": [0, 0], "date": "2026-11-15", "done": True}}, "guideV": 1}
MESURA = """() => { let n = 0, ex = [];
  document.querySelectorAll('#rep svg').forEach(svg => {
    const T = [...svg.querySelectorAll('g[data-k^="map:"] text')].map(t => ({ g: t.closest('g'), r: t.getBoundingClientRect(), s: t.textContent }));
    for (let a = 0; a < T.length; a++) for (let b = a + 1; b < T.length; b++) {
      const x = T[a], y = T[b]; if (x.g === y.g || !x.r.width || !y.r.width) continue;
      if (x.r.left < y.r.right - 1 && y.r.left < x.r.right - 1 && x.r.top < y.r.bottom - 1 && y.r.top < x.r.bottom - 1) { n++; if (ex.length < 3) ex.push(x.s + ' / ' + y.s); }
    } });
  return { n, ex, mapes: document.querySelectorAll('#rep svg').length }; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        for dn, vp in (("ordinador", {"width": 1366, "height": 900}), ("tauleta", {"width": 1280, "height": 800}), ("mòbil", {"width": 412, "height": 900})):
            b = await p.chromium.launch(); ctx = await b.new_context(viewport=vp)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); localStorage.setItem('peli-directe:m:P01', " + json.dumps(json.dumps(M)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            tot, exs, nm = 0, [], 0
            for tab in ("resum", "mapes"):
                await pg.evaluate("(t) => { const b = [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === t); if (b) b.click(); }", tab); await pg.wait_for_timeout(400)
                r = await pg.evaluate(MESURA); tot += r["n"]; exs += r["ex"]; nm += r["mapes"]
            ok = tot == 0 and nm > 0 and not errs; mal += 0 if ok else 1
            print("%s %-10s %d mapes · textos encavalcats: %d %s · errors: %s" % ("✓" if ok else "✗", dn, nm, tot, exs[:2], errs or "cap"))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
