# Informe pel nom: el mateix jugador amb dorsals diferents s'ajunta (indicant-ho una vegada, o sol si el canvi és nou), sense barrejar-lo amb qui porta ara el dorsal antic
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter U", "gk": True}, {"d": 17, "n": "Joan Garcia", "gk": False}, {"d": 7, "n": "Pere Puig", "gk": False}, {"d": 5, "n": "Marc Soler", "gk": False}]
def A(i, d, a="G"): return {"i": i, "t": 30 * i, "p": 1, "e": "N", "d": d, "a": a, "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": None}
def match(mid, date, ds, noms=None):
    mm = {"id": mid, "rival": "Rival " + mid, "date": date, "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": [A(k + 1, d) for k, d in enumerate(ds)], "seq": len(ds), "squad": sorted(set([1] + ds)), "upd": 1}
    if noms: mm["noms"] = noms
    return mm
MS = [match("P01", "2026-10-03", [7, 7, 7]), match("P02", "2026-10-10", [7, 7]), match("P03", "2026-11-07", [7, 17, 17, 17, 17], {"1": "Porter U", "7": "Pere Puig", "17": "Joan Garcia"})]
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "done": True, "tr": 0} for mm in MS}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1}
INIT = "window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}"
GOLS = """() => { const tb = document.querySelector('#rep table.rt'); const hs = [...tb.querySelectorAll('tr')[0].children].map(x => x.textContent.trim()); const gi = hs.indexOf('Gols'); const o = {};
  [...tb.querySelectorAll('tr')].slice(1).forEach(tr => { const d = (tr.children[0] || {}).textContent; if (/^\\d+$/.test(d)) o[d] = tr.children[gi].textContent.trim(); }); return o; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800}); await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
        async def informe():
            await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose'], #ov [data-act='close']\"); if (c && c.offsetParent) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => /Tot l'equip/.test(o.textContent))); s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'jugadors').click()"); await pg.wait_for_timeout(300)
            return await pg.evaluate(GOLS)
        g0 = await informe()
        print("abans d'indicar res: Joan (17) %s gols · Pere (7) %s gols" % (g0.get("17"), g0.get("7")))
        # a la fitxa d'en Joan: «Ha portat un altre dorsal?» → el 7, fins al P02
        await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => /Tot l'equip/.test(o.textContent))); s.value = '17'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => document.querySelector(\"#rep [data-act='dorsprev']\").click()"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { document.getElementById('dpd').value = '7'; const s = document.getElementById('dpf'); s.value = [...s.options].find(o => /^P02/.test(o.textContent)).value; document.querySelector(\"#ov [data-act='dorsadd']\").click(); }"); await pg.wait_for_timeout(400)
        toast = await pg.evaluate("() => (document.getElementById('toast') || {}).textContent || ''")
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
        g1 = await informe()
        ok(g1.get("17") == "9" and g1.get("7") == "1", "indicant que en Joan portava el 7 fins al P02: Joan %s gols (esperat 9) · Pere %s (esperat 1) · «%s»" % (g1.get("17"), g1.get("7"), toast[:70]))
        # un canvi nou de dorsal (en Joan passa al 27): s'ajunta sol
        await pg.evaluate("() => { const a = window.__peli.app; a.roster.find(q => q.n === 'Joan Garcia').d = 27; window.__peli.saveMatch(); }")
        await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
        await pg.evaluate("() => document.querySelector(\"#home [data-act='roster']\") && 0")
        await pg.evaluate("() => { const a = window.__peli.app; a.upd = Date.now(); }")
        await pg.evaluate("() => { const b = document.querySelector(\"#home [data-act='seasonrep']\"); }")
        hist = await pg.evaluate("() => { const ev = new Event('x'); return 1; }")
        await pg.evaluate("() => { const h = document.querySelector('[data-act=\"home\"]'); }")
        # desar l'app (com faria qualsevol acció) perquè l'app vegi el canvi de dorsal
        await pg.evaluate("() => { try { window.__peli.app.lang = window.__peli.app.lang; } catch (e) {} }")
        await pg.evaluate("() => { const b = document.querySelector(\"#home [data-act='seasonrep']\"); if (b) b.click(); }"); await pg.wait_for_timeout(300)
        g2 = await informe()
        dh = await pg.evaluate("() => JSON.stringify(window.__peli.app.dorsHist || [])")
        ok(g2.get("27") == "9" and g2.get("7") == "1", "en Joan canvia al 27: Joan %s gols (esperat 9) · Pere %s · historial: %s" % (g2.get("27"), g2.get("7"), dh[:140]))
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
