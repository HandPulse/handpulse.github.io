# Glossari: el botó «?» de l'informe obre «Què vol dir cada xifra» amb 10 termes, traduïts (en castellà, cap text en català)
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}, {"d": 7, "n": "Jugador 7", "gk": False}]
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-08", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": [{"i": 1, "t": 30, "p": 1, "e": "N", "d": 7, "a": "G", "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": None}], "seq": 1, "squad": [1, 7], "upd": 1}
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        for lang in ("ca", "es"):
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 1, "upd": 1, "sc": [1, 0], "date": "2026-11-08"}}, "guideV": 1, "lang": lang}
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800})
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); localStorage.setItem('peli-directe:m:P01', " + json.dumps(json.dumps(M)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            r = await pg.evaluate("""() => { const b = document.querySelector("#rep [data-act='gloss']"); if (!b) return null; b.click();
              return new Promise(res => setTimeout(() => res({ costat: !!(b.nextElementSibling && b.nextElementSibling.getAttribute('data-act') === 'rcsv'), tit: (document.querySelector('#ov h2') || {}).textContent, dt: [...document.querySelectorAll('#ov dl.gloss dt')].map(x => x.textContent), dd: [...document.querySelectorAll('#ov dl.gloss dd')].map(x => x.textContent) }), 300)); }""")
            print(lang + ":")
            ok(r and r["costat"] and len(r["dt"]) == 10 and len(r["dd"]) == 10, "botó «?» al costat d'«Excel» · «%s» amb %d termes" % ((r or {}).get("tit"), len((r or {}).get("dt", []))))
            if lang == "es":
                cat = [x for x in r["dd"] + r["dt"] if any(w in x for w in ("vol dir", "llançaments", "aturades", "pèrdues", "Gols dividits"))]
                ok(not cat, "en castellà, cap text en català (%s)" % (cat[:1] or "cap"))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
