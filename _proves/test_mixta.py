# Defenses mixtes: el nom «Mixta», la finestra «A qui es marca?», el marcatge desat amb el minut i a cada acció
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import sys
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
import asyncio, json
from playwright.async_api import async_playwright
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7)]
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-23", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 9, "n": "Rival Nou"}, {"d": 6, "n": "Rival Sis"}, {"d": 16, "n": "Porter Rival", "gk": True}], "acts": [], "seq": 0, "squad": [1, 3, 5, 7], "upd": 1, "det": "com"}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-23"}}, "guideV": 1}
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }) || document.querySelector(s); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
OBRE = "() => { if (!document.querySelector('[data-act=\"dfset\"]')) { const x = [...document.querySelectorAll('[data-act]')].find(e => /^df/.test(e.getAttribute('data-act')) && e.getAttribute('data-act') !== 'dfset'); if (x) x.click(); } }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, t):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", t))
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.wait_for_timeout(600)
            print("== " + nom + ":")
            await pg.evaluate(OBRE); await pg.wait_for_timeout(200)
            await pg.evaluate(VIS, "[data-act='dfset'][data-v='N:5+1']"); await pg.wait_for_timeout(250)
            fin = await pg.evaluate("() => [...document.querySelectorAll('[data-act=\"dfmkp\"]')].map(b => b.textContent.trim())")
            ok(fin == ["9 Rival Nou", "6 Rival Sis"], "nostra Mixta 5+1: la finestra mostra els jugadors del rival %s" % fin)
            await pg.evaluate(VIS, "[data-act='dfmkp'][data-v='9']"); await pg.evaluate(VIS, "[data-act='dfmkok']"); await pg.wait_for_timeout(250)
            await pg.evaluate(OBRE); await pg.wait_for_timeout(200)
            await pg.evaluate(VIS, "[data-act='dfset'][data-v='R:4+2']"); await pg.wait_for_timeout(250)
            fin2 = await pg.evaluate("() => [...document.querySelectorAll('[data-act=\"dfmkp\"]')].map(b => b.getAttribute('data-v'))")
            ok(fin2 == ["3", "5", "7"], "Mixta 4+2 del rival: la finestra mostra els nostres jugadors de camp %s" % fin2)
            for d in ("3", "5"): await pg.evaluate(VIS, "[data-act='dfmkp'][data-v='%s']" % d)
            await pg.evaluate(VIS, "[data-act='dfmkok']"); await pg.wait_for_timeout(250)
            st = await pg.evaluate("() => { const m = window.__peli.m; return [m.dfN, m.dfNmk, (m.dfsN || []).slice(-1)[0].mk, m.df, m.dfmk, (m.dfs || []).slice(-1)[0].mk, document.body.textContent.includes('Mixta 5+1 (9)'), document.body.textContent.includes('Mixta 4+2 (3, 5)')]; }")
            ok(st[:6] == ["5+1", [9], [9], "4+2", [3, 5], [3, 5]] and st[6] and st[7], "desat amb el minut i a la capçalera «Mixta 5+1 (9)» i «Mixta 4+2 (3, 5)»: %s" % st)
            # un llançament del rival 9 i un del nostre 3
            if nom == "tauleta": await pg.evaluate(VIS, "[data-act='rplayer'][data-v='9']")
            else: await pg.evaluate(VIS, "#qui [data-act='rival']"); await pg.wait_for_timeout(100); await pg.evaluate(VIS, "[data-act='rplayer'][data-v='9']")
            await pg.evaluate(VIS, "#que [data-act='ptype'][data-v='LL']"); await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']"); await pg.evaluate(VIS, "#que [data-act='gres'][data-v='G:5']"); await pg.wait_for_timeout(250)
            a1 = await pg.evaluate("() => { const a = window.__peli.m.acts.slice(-1)[0]; return a ? [a.e, a.d, a.mkN || null, a.mk || null] : null; }")
            await pg.evaluate(VIS, "#qui [data-act='player'][data-v='3']"); await pg.evaluate(VIS, "#que [data-act='ptype'][data-v='LL']"); await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']"); await pg.evaluate(VIS, "#que [data-act='gres'][data-v='A:2']"); await pg.wait_for_timeout(250)
            a2 = await pg.evaluate("() => { const a = window.__peli.m.acts.slice(-1)[0]; return a ? [a.e, a.d, a.mkN || null, a.mk || null] : null; }")
            ok(a1 == ["R", 9, [9], [3, 5]] and a2 == ["N", 3, [9], [3, 5]], "les accions queden marcades: rival 9 %s · nostre 3 %s" % (a1, a2))
            await pg.evaluate(OBRE); await pg.wait_for_timeout(200); await pg.evaluate(VIS, "[data-act='dfset'][data-v='N:6:0']"); await pg.wait_for_timeout(200)
            st2 = await pg.evaluate("() => [window.__peli.m.dfN, window.__peli.m.dfNmk || null, !!document.querySelector('[data-act=\"dfmkok\"]')]")
            ok(st2 == ["6:0", None, False], "canviar a 6:0 esborra el marcatge i no pregunta res: %s" % st2)
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
