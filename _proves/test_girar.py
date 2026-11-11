# Mòbil girat a la pantalla del partit: avís per girar-lo; mai en vertical, a la tauleta, a l'ordinador ni a l'inici
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
UA = "Mozilla/5.0 (Linux; Android 17; SM-A176B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36"
ROSTER = [{"d": 1, "n": "Porter", "gk": True}, {"d": 7, "n": "Jugador 7", "gk": False}]
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-08", "durada": 30, "part": 1, "clock": {"acc": 60, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": [], "seq": 0, "squad": [1, 7], "upd": 1, "det": "com"}
def app(cur): return {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01" if cur else None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-08"}}, "guideV": 1}
CASOS = [("Galaxy A17 horitzontal, partit", {"viewport": {"width": 832, "height": 330}, "device_scale_factor": 2.8125, "is_mobile": True, "has_touch": True, "user_agent": UA}, True, True),
         ("Galaxy A17 vertical, partit", {"viewport": {"width": 384, "height": 750}, "device_scale_factor": 2.8125, "is_mobile": True, "has_touch": True, "user_agent": UA}, True, False),
         ("Galaxy A17 horitzontal, inici", {"viewport": {"width": 832, "height": 330}, "device_scale_factor": 2.8125, "is_mobile": True, "has_touch": True, "user_agent": UA}, False, False),
         ("Tauleta horitzontal, partit", "Galaxy Tab S4 landscape", True, False),
         ("Portàtil 1366×768, partit", {"viewport": {"width": 1366, "height": 768}}, True, False)]
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, dev, partit, esperat in CASOS:
            d = p.devices[dev] if isinstance(dev, str) else dev
            b = await p.chromium.launch(); ctx = await b.new_context(**d)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app(partit))) + "); const M = " + json.dumps(M) + "; " + ("M.clock.start = Date.now() - 1000; " if partit else "") + "localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.wait_for_timeout(700)
            r = await pg.evaluate("() => { const e = document.getElementById('rotmsg'); return e ? [getComputedStyle(e).display !== 'none', e.textContent] : [false, 'no hi és']; }")
            ok = r[0] == esperat and not errs; mal += 0 if ok else 1
            print("%s %-32s avís %s%s" % ("✓" if ok else "✗", nom, "VISIBLE «%s»" % r[1][:50] if r[0] else "amagat", (" · errors " + str(errs)) if errs else ""))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
