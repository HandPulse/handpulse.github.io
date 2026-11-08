# Interruptors «Botons grans» i «Alt contrast» del menú: s'activen, es recorden, l'alt contrast guanya al mode fosc i torna després d'imprimir
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": d, "n": "Jugador " + str(d), "gk": d in (1, 12)} for d in range(1, 17)]
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-07"}}, "guideV": 1}
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-07", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": [], "seq": 0, "squad": list(range(1, 17)), "upd": 1, "det": "com"}
ESTAT = """() => { const cs = getComputedStyle(document.body), r = document.documentElement; return { tema: r.getAttribute('data-theme') || 'cap', fons: cs.backgroundColor, text: getComputedStyle(r).getPropertyValue('--ink').trim(),
  grans: document.body.classList.contains('bigbtn'), menu: [...document.querySelectorAll("#ov [data-act='bigbtn'] .note, #ov [data-act='hctoggle'] .note")].map(x => x.textContent.trim()) }; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, dev, esquema in (("mòbil, mode clar", p.devices["Pixel 7"], "light"), ("tauleta, mode fosc", {"viewport": {"width": 1280, "height": 800}}, "dark")):
            b = await p.chromium.launch(); ctx = await b.new_context(color_scheme=esquema, **dev)
            await ctx.add_init_script("window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(150)
            e0 = await pg.evaluate(ESTAT)
            await pg.evaluate("() => document.querySelector(\"#board [data-act='menu']\").click()"); await pg.wait_for_timeout(200)
            e1 = await pg.evaluate(ESTAT)
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='hctoggle']\").click()"); await pg.wait_for_timeout(150)
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='bigbtn']\").click()"); await pg.wait_for_timeout(150)
            e2 = await pg.evaluate(ESTAT)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); }"); await pg.wait_for_timeout(150)
            if nom.startswith("tauleta"): await pg.screenshot(path="/tmp/hc_tauleta.png")
            else: await pg.screenshot(path="/tmp/hc_mobil.png")
            # imprimir un informe i tornar
            await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(300)
            pr = await pg.evaluate("() => { const b = document.querySelector(\"#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']\"); if (b) b.click(); return !!b; }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => window.dispatchEvent(new Event('afterprint'))"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(1500)
            e3 = await pg.evaluate(ESTAT)
            abans_obrir = await pg.evaluate("() => { const a = JSON.parse(localStorage.getItem('peli-directe:app') || '{}'); return 'hc=' + a.hc + ' bigBtn=' + a.bigBtn; }")
            await pg.reload(); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(400)
            despres_obrir = await pg.evaluate("() => { const a = JSON.parse(localStorage.getItem('peli-directe:app') || '{}'); return 'hc=' + a.hc + ' bigBtn=' + a.bigBtn + ' · ini=' + sessionStorage.getItem('ini'); }")
            print("   desat abans de tornar a obrir: %s · després: %s" % (abans_obrir, despres_obrir))
            e4 = await pg.evaluate(ESTAT)
            ok = e0["tema"] != "hc" and e2["tema"] == "hc" and e2["grans"] and e2["fons"] in ("rgb(255, 255, 255)",) and e2["text"] == "#000000" and e3["tema"] == "hc" and e4["tema"] == "hc" and e4["grans"] and not errs
            mal += 0 if ok else 1
            print("%s %s:\n   abans: tema %s, fons %s · menú: %s\n   activat: tema %s, fons %s, text %s, botons grans %s · menú: %s\n   després d'imprimir (%s): tema %s · en tornar a obrir: tema %s, botons grans %s · errors %s" % (
                "✓" if ok else "✗", nom, e0["tema"], e0["fons"], e1["menu"], e2["tema"], e2["fons"], e2["text"], e2["grans"], e2["menu"], "botó trobat" if pr else "sense botó", e3["tema"], e4["tema"], e4["grans"], errs or "cap"))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
