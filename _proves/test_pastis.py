# Gràfic circular dels gols per posició: cada posició compta el que toca, el total coincideix amb la taula, i amb un jugador triat només surten els seus gols
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
ROSTER = [{"d": d, "n": "Jugador " + str(d), "gk": d == 1} for d in (1, 2, 3, 5, 7, 9)]
# gols nostres: zona, tipus, jugador → esperat: EX 3, LAT 4, CEN 2, PEN 2, 7M 2, CA 3, CC 1, SZ 1 = 18
GN = [("EE", None, 2), ("ED", None, 2), ("EE", None, 9), ("9E", None, 3), ("9D", None, 3), ("6E", None, 9), ("6D", None, 5), ("9C", None, 7), ("6C", None, 7),
      ("PN", None, 5), ("PE", None, 5), ("7M", None, 9), ("7M", None, 9), ("9C", "CD", 2), ("6C", "C2", 3), ("EE", "CG", 9), ("9C", "CC", 7), (None, None, 3)]
GR = [("ED", None, 4), ("9C", None, 7), ("9C", None, 7), ("7M", None, 11), ("PC", None, 4)]
ACTS = []
for i, (z, ty, d) in enumerate(GN + [(z, ty, d) for z, ty, d in GR]):
    e = "N" if i < len(GN) else "R"
    a = {"i": i + 1, "t": 30 * (i + 1), "p": 1 if i < 12 else 2, "e": e, "d": d, "a": "G", "z": z, "k": None, "g": 5 if z else None, "s": None, "gk": 1, "rgk": 16}
    if ty: a["ty"] = ty
    ACTS.append(a)
ACTS.append({"i": 99, "t": 999, "p": 2, "e": "N", "d": 2, "a": "A", "z": "9C", "k": None, "g": 5, "s": None, "gk": 1, "rgk": 16})   # un llançament aturat (no és gol)
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-01", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 4, "n": "R4"}, {"d": 7, "n": "R7"}, {"d": 11, "n": "R11"}, {"d": 16, "n": "Porter", "gk": True}],
     "acts": ACTS, "seq": 99, "squad": [1, 2, 3, 5, 7, 9], "upd": 1, "det": "com"}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": len(ACTS), "upd": 1, "sc": [18, 5], "date": "2026-11-01"}}, "guideV": 1}
PIE = """() => [...document.querySelectorAll('#rep .rs-pie .gpcard')].map(c => ({ t: c.querySelector('h3').textContent, n: (c.querySelector('.gpn') || {}).textContent,
  leg: [...c.querySelectorAll('.gpleg li')].map(li => li.querySelector('span').textContent + ' ' + li.querySelector('small').textContent + ' (' + li.querySelector('b').textContent + ')').join(' · ') }))"""
TOT = """() => [...document.querySelectorAll('#rep .rs-types .repcard')].map(c => { const tr = [...c.querySelectorAll('tr.tot')][0]; const tds = tr ? [...tr.querySelectorAll('td')] : []; return tds.length ? tds[tds.length - 2].textContent : '?'; })"""
async def main():
    async with async_playwright() as p:
        for nom, dev, L in (("ordinador", {"viewport": {"width": 1536, "height": 860}}, "ca"), ("mòbil (francès)", p.devices["Pixel 7"], "fr")):
            a = dict(APP); a["lang"] = L
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(a)) + "); localStorage.setItem('peli-directe:m:P01', " + json.dumps(json.dumps(M)) + "); }")
            await ctx.add_init_script("new MutationObserver(() => document.querySelectorAll('#rep details.rmore:not([open])').forEach(d => { d.open = true; })).observe(document, { childList: true, subtree: true });")   # obre «Més detall», com faria l'entrenador
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"[data-act='report']\").click(); }"); await pg.wait_for_timeout(400)
            pie = await pg.evaluate(PIE); tot = await pg.evaluate(TOT)
            print("==== " + nom + " · total de la taula: " + " / ".join(tot))
            for x in pie: print("   %s · centre %s · %s" % (x["t"], x["n"], x["leg"]))
            el = await pg.query_selector("#rep .rs-pie"); await el.scroll_into_view_if_needed(); await el.screenshot(path="/tmp/pastis_%s.png" % ("pc" if nom == "ordinador" else "mobil"))
            # un sol jugador: el 9 (gols: EE, 6E, 7M, 7M, EE de contragol = 5)
            sel = await pg.evaluate("""() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === '9')); if (!s) return false; s.value = '9'; s.dispatchEvent(new Event('change', { bubbles: true })); return true; }""")
            await pg.wait_for_timeout(300)
            if sel:
                pie9 = await pg.evaluate(PIE.replace("#rep .rs-pie .gpcard", "#rep .gpcard"))
                print("   amb el jugador 9: centre %s · %s" % (pie9[0]["n"], pie9[0]["leg"]))
            surt = await pg.evaluate("() => Math.max(document.scrollingElement.scrollWidth - innerWidth, 0)")
            print("   surt de la pantalla: %d px · errors: %s" % (surt, errs or "cap"))
            await b.close()
asyncio.run(main())
