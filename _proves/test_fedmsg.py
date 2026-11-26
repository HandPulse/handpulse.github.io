# Missatge clar quan la federació no deixa llegir la classificació ni el calendari (web nova des del 17/11/2026), en català i en castellà
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
URL = "https://resultadosbalonmano.isquad.es/clasificacion.php?seleccion=0&id=1038558&id_ambito=0&id_territorial=17&id_superficie=1&iframe=0&id_categoria=3077&id_competicion=211806"
async def main():
    async with async_playwright() as p:
        mal = 0
        for lang, esp in (("ca", "La federació ha canviat la seva web"), ("es", "La federación ha cambiado su web")):
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": [{"d": 1, "n": "Porter", "gk": True}], "seen": 1, "gkFixAt": "x", "index": {}, "guideV": 1, "compUrl": URL, "lang": lang}
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800}); crides = []
            async def rt(r):
                crides.append(1); await r.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": False, "error": "No s'ha pogut llegir la classificació ni el calendari de la federació."}))
            await ctx.route("https://script.google.com/**", rt)
            await ctx.add_init_script("window.__hpTest = true; localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + ");")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.wait_for_timeout(800)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); window.__peli.setLeagueApi('https://script.google.com/macros/s/PROVA/exec'); window.__peli.leagueFetch(true, false); }"); await pg.wait_for_timeout(1200)
            err = await pg.evaluate("() => window.__peli.lg.err || ''")
            toast = await pg.evaluate("(e) => document.body.innerText.includes(e)", esp)
            await pg.evaluate("() => { const x = document.querySelector(\"#home [data-act='standings']\"); if (x) x.click(); }"); await pg.wait_for_timeout(400)
            fin = await pg.evaluate("(e) => { const o = document.getElementById('ov'); return !!o && !o.hidden && o.innerText.includes(e); }", esp)
            ok = bool(crides) and err.startswith(esp) and toast and fin and not errs; mal += 0 if ok else 1
            print("%s %s · petició feta: %s · error desat: «%s…» · avís: %s · finestra de la classificació: %s · errors: %s" % ("✓" if ok else "✗", lang, bool(crides), err[:45], toast, fin, errs or "cap"))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
