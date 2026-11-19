# Acta amb el seu enllaç: s'enganxa l'enllaç a l'informe del partit i s'hi carreguen els noms, la plantilla del rival i els àrbitres
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ACTA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "acta_1596532.json"), encoding="utf-8"))
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": q[0], "n": q[1], "gk": False} for q in ACTA["teams"][0]["ps"][:6]]
M = {"id": "P08", "rival": "Rival", "date": "2026-11-15", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": [], "seq": 0, "squad": [1] + [q[0] for q in ACTA["teams"][0]["ps"][:6]], "upd": 1}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P08": {"rival": "Rival", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-15", "done": True}}, "guideV": 1,
       "compUrl": "https://resultadosbalonmano.isquad.es/maqueta/#v=tabla&id=1038558", "ownId": "215300"}
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, t):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", t))
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); localStorage.setItem('peli-directe:m:P08', " + json.dumps(json.dumps(M)) + "); }")
        demanat = []
        async def resp(route):
            demanat.append(route.request.url); await route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "actes": {"1596532": ACTA}}))
        await ctx.route(re.compile(r".*[?&]a=actes.*"), resp)
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(300)
        hi = await pg.evaluate("() => { const d = document.createElement('div'); d.innerHTML = window.__peli.actaLinkHTML({ id: 'P08' }); return !!d.querySelector('#actalink') && !!d.querySelector(\"[data-act='actalink'][data-v='P08']\"); }")
        ok(hi, "el bloc «Acta de la federació» té el camp i el botó «Carrega»")
        await pg.evaluate("() => window.__peli.actaFromLink('P08', 'https://balonmano.isquad.es/balonmano_acta_completa_pdf.php?id_partido=1596532')"); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("() => { const st = window.__peli.app; const mm = window.__peli.matchOf('P08') || {}; const t = document.querySelector('#toast, .toast'); return { jor: (st.index.P08 || {}).jor, arb: ((st.actaOf || {})['8'] || {}).arb, riv: (mm.rivals || []).length, riv1: (mm.rivals || [])[0], toast: t ? t.textContent : '', bloc: !!document.querySelector('#rep .repcard.actalink') }; }")
        print("      " + str(r)[:300])
        ok(any("id_partido" not in u and "p=1596532" in u for u in demanat), "l'app demana l'acta 1596532 a l'script")
        ok(r["jor"] == "8" and r["arb"] and len(r["arb"]) == 2, "acta lligada a la jornada 8, amb els 2 àrbitres")
        ok(r["riv"] == 14 and r["riv1"] and r["riv1"].get("n"), "la plantilla del rival: 14 jugadors amb dorsal i nom")
        ok("16" in r["toast"] and "14" in r["toast"], "avís: %s" % r["toast"][:90])
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
