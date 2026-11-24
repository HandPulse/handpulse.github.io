# Defenses mixtes a l'informe: qui ha estat marcat i quants minuts, llançaments amb marcatge i sense, i com s'ataca contra la mixta
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7)]
def A(i, t, p, e, d, a, **kw):
    x = {"i": i, "t": t, "p": p, "e": e, "d": d, "a": a, "k": None, "z": "9C", "g": 5, "s": None, "gk": 1, "rgk": 16}; x.update(kw); return x
acts = [A(1, 400, 1, "N", 3, "G", df="4+2", mk=[3, 5]), A(2, 500, 1, "N", 3, "A", df="4+2", mk=[3, 5]), A(3, 2500, 2, "N", 3, "G", df="6:0"),
        A(4, 700, 1, "R", 9, "A", dfN="5+1", mkN=[9]), A(5, 1600, 1, "R", 9, "G", dfN="6:0")]
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-22", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 9, "n": "Rival Nou"}], "acts": acts, "seq": 5, "squad": [1, 3, 5, 7], "upd": 1, "done": True,
     "dfsN": [{"t": 600, "p": 1, "v": "5+1", "mk": [9]}, {"t": 1500, "p": 1, "v": "6:0"}], "dfs": [{"t": 300, "p": 1, "v": "4+2", "mk": [3, 5]}, {"t": 2100, "p": 2, "v": "6:0"}]}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 5, "upd": 1, "sc": [2, 1], "date": "2026-11-22", "done": True}}, "guideV": 1}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); localStorage.setItem('peli-directe:m:P01', " + json.dumps(json.dumps(M)) + "); }")
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
        res = {}
        for nom, v in (("temporada", None), ("partit", "P01")):
            if v: await pg.evaluate("(v) => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === v)); s.value = v; s.dispatchEvent(new Event('change', { bubbles: true })); }", v); await pg.wait_for_timeout(500)
            res[nom] = await pg.evaluate("() => { const c = document.querySelectorAll('#rep .repcard.mixta'); return { n: c.length, files: c.length ? [...c[0].querySelectorAll('tr')].map(t => [...t.children].map(x => x.textContent.trim()).join(' | ')) : [] }; }")
        mal = 0
        for nom, r in res.items():
            f = r["files"]
            ok = r["n"] == 1 and "3 Jugador 3 | el rival | 30 | 1/2 (50%) | 1/1 (100%)" in f and "5 Jugador 5 | el rival | 30 | – | –" in f and "9 Rival Nou | nosaltres | 15 | 0/1 (0%) | 1/1 (100%)" in f \
                 and "Nosaltres | 1/2 (50%) | 1/1 (100%)" in f and "El rival, contra la nostra | 0/1 (0%) | 1/1 (100%)" in f
            mal += 0 if ok else 1
            print("%s informe del %s: %d bloc · %s" % ("✓" if ok else "✗", nom, r["n"], f if not ok else "files correctes"))
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
