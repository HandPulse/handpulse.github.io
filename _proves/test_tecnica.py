# Tècnica del llançament: fila a sota de la porteria (només Complet), «Directe» marcat, es desa amb el toc a la porteria i surt a l'informe
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5)]
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, t):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", t))
        for nom, dev, det in (("tauleta", {"viewport": {"width": 1280, "height": 800}}, "com"), ("mòbil", p.devices["Pixel 7"], "com"), ("mòbil Essencial", p.devices["Pixel 7"], "ess")):
            M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-21", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 6, "n": "Rival Sis"}, {"d": 16, "n": "Porter Rival", "gk": True}], "acts": [], "seq": 0, "squad": [1, 3, 5], "upd": 1, "det": det}
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-21"}}, "guideV": 1}
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print("== " + nom + ":")
            async def shot(rival, tec, res):
                if rival:
                    if nom == "tauleta": await pg.evaluate(VIS, "[data-act='rplayer'][data-v='6']")
                    else: await pg.evaluate(VIS, "#qui [data-act='rival']"); await pg.wait_for_timeout(80); await pg.evaluate(VIS, "[data-act='rplayer'][data-v='6']")
                else: await pg.evaluate(VIS, "#qui [data-act='player'][data-v='3']")
                await pg.evaluate(VIS, "#que [data-act='ptype'][data-v='LL']"); await pg.wait_for_timeout(100)
                if await pg.evaluate("() => window.__peli.step() === 'zona'"): await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']")
                await pg.wait_for_timeout(120)
                fila = await pg.evaluate("() => { const f = document.querySelector('#que .gptec'); return f ? { n: f.querySelectorAll('button').length, sel: (f.querySelector('.sel') || {}).getAttribute ? f.querySelector('.sel').getAttribute('data-v') : null, dins: [...f.querySelectorAll('button')].every(x => x.getBoundingClientRect().right <= innerWidth + 0.5) } : null; }")
                if tec: await pg.evaluate(VIS, "#que [data-act='tech'][data-v='%s']" % tec); await pg.wait_for_timeout(120)
                await pg.evaluate(VIS, "#que [data-act='gres'][data-v='%s']" % res); await pg.wait_for_timeout(200)
                return fila, await pg.evaluate("() => { const l = window.__peli.m.acts; const a = l[l.length - 1]; return a ? [a.e, a.a, a.tc || null] : null; }")
            f1, a1 = await shot(False, "ROS", "G:5"); f2, a2 = await shot(False, None, "A:2"); f3, a3 = await shot(True, "VAS", "A:3")
            if det == "com":
                ok(f1 and f1["n"] == 7 and f1["sel"] == "DIR" and f1["dins"], "la fila de 7 tècniques, amb «Directe» marcat i dins la pantalla: %s" % f1)
                ok(a1 == ["N", "G", "ROS"] and a2 == ["N", "A", "DIR"] and a3 == ["R", "A", "VAS"], "desat: %s · %s · %s" % (a1, a2, a3))
                await pg.evaluate("() => { document.querySelector(\"[data-act='report'], [data-act='rep']\") ? document.querySelector(\"[data-act='report'], [data-act='rep']\").click() : null; }"); await pg.wait_for_timeout(500)
                if not await pg.evaluate("() => !!document.querySelector('#rep .repcard.tec')"):
                    await pg.evaluate("() => window.__peli.openReport ? window.__peli.openReport() : null"); await pg.wait_for_timeout(500)
                t = await pg.evaluate("() => [...document.querySelectorAll('#rep .repcard.tec tbody tr')].map(r => r.textContent.replace(/\\s+/g, ' '))")
                ok(any("Rosca" in x and "11100%" in x.replace(" ", "") for x in t) and any("Vaselina" in x for x in t), "taula «Per tècnica» a l'informe: %s" % t)
            else:
                ok(f1 is None and a1 == ["N", "G", None], "al nivell Essencial no surt la fila ni es desa la tècnica: %s · %s" % (f1, a1))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
