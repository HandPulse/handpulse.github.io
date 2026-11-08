# Partits desats: «Edita · Obre · Esborra», canviar el nom del rival (desat i en curs), nom buit, cancel·lar, mòbil petit i francès
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
ROSTER = [{"d": d, "n": "J" + str(d), "gk": d == 1} for d in (1, 2, 3)]
RIV = {"P01": "C. A. Sabadell Handbol", "P02": "CH Sant Fost", "P03": "OAR GRÀCIA ATH", "P04": "CE Handbol BCN Sants 'a'", "P05": "CH Parets A"}
MS = {k: {"id": k, "rival": r, "date": "2026-10-%02d" % (10 + i), "durada": 30, "part": 1, "clock": {"acc": 0, "start": None}, "gk": 1, "rivals": [], "acts": [], "seq": 0, "squad": [1, 2, 3], "upd": 1, "det": "com"} for i, (k, r) in enumerate(RIV.items())}
IDX = {k: {"rival": r, "n": 0, "upd": 1, "sc": [0, 0], "date": MS[k]["date"], "comp": "", "jor": "", "lloc": "", "done": False, "tr": 0} for k, r in RIV.items()}
def app(L): return {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P05", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1, "lang": L}
LLISTA = "() => [...document.querySelectorAll('#ov .mrow')].map(r => r.querySelector('.mi').textContent.replace(/\\s+/g, ' ').trim().slice(0, 34) + ' → ' + [...r.querySelectorAll('button')].map(b => b.textContent.trim()).join(' · '))"
async def main():
    async with async_playwright() as p:
        for L, dev in (("ca", {"viewport": {"width": 1280, "height": 800}}), ("fr", p.devices["iPhone SE"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            init = "window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app(L))) + "); " + \
                   "".join("localStorage.setItem('peli-directe:m:" + k + "', " + json.dumps(json.dumps(mm)) + "); " for k, mm in MS.items()) + "}"
            await ctx.add_init_script(init)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            await pg.evaluate("() => { const mn = document.querySelector(\"[data-act='menu']\"); if (mn) mn.click(); }"); await pg.wait_for_timeout(150)
            print("==== " + L + (" (iPhone SE)" if L == "fr" else " (tauleta)"))
            print("llista:\n   " + "\n   ".join(await pg.evaluate(LLISTA)))
            await pg.wait_for_timeout(120); surt = await pg.evaluate("() => { const L = document.querySelector('#ov .saved'); const lr = L.getBoundingClientRect(); return [...L.querySelectorAll('.btn')].filter(b => { const r = b.getBoundingClientRect(); return r.right > lr.right + 1 || r.left < lr.left - 1 || b.scrollWidth > b.clientWidth + 1; }).length; }")
            if L == "fr": await (await pg.query_selector("#ov .list")).screenshot(path="/tmp/edita_llista.png")
            # canviar el nom d'un partit desat
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='medit'][data-v='P03']\").click()"); await pg.wait_for_timeout(120)
            v0 = await pg.evaluate("() => { const e = document.getElementById('medriv'); return e ? e.value + ' (seleccionat: ' + (e.selectionEnd - e.selectionStart) + ' lletres)' : 'NO'; }")
            await pg.fill("#medriv", "OAR Gràcia Sabadell Atlètic"); await pg.evaluate("() => document.querySelector(\"#ov [data-act='medsave']\").click()"); await pg.wait_for_timeout(200)
            desat = await pg.evaluate("() => { const mm = window.__peli.store.get('peli-directe:m:P03'); const ix = JSON.parse(localStorage.getItem('peli-directe:app')).index.P03; return mm.rival + ' / índex: ' + ix.rival + ' / accions: ' + mm.acts.length; }")
            fin = await pg.evaluate("() => (document.querySelector('#ov h2') || {}).textContent")
            # nom buit: no es desa
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='medit'][data-v='P02']\").click()"); await pg.wait_for_timeout(100)
            await pg.fill("#medriv", "   "); await pg.evaluate("() => document.querySelector(\"#ov [data-act='medsave']\").click()"); await pg.wait_for_timeout(100)
            buit = await pg.evaluate("() => (document.getElementById('toast') || {}).textContent + ' · segueix a la finestra: ' + !!document.getElementById('medriv') + ' · desat: ' + window.__peli.store.get('peli-directe:m:P02').rival")
            # la fletxa enrere i «Cancel·la» tornen a la llista sense canviar res
            await pg.evaluate("() => { const bk = document.querySelector(\"#ov .bk[data-act='close']\"); if (bk) bk.click(); }"); await pg.wait_for_timeout(100)
            fl = await pg.evaluate("() => !!document.querySelector(\"#ov [data-act='medit']\") ? 'a la llista' : 'NO'")
            # el partit en curs, amb la tecla Retorn: el marcador canvia
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='medit'][data-v='P05']\").click()"); await pg.wait_for_timeout(100)
            await pg.fill("#medriv", "CH Parets"); await pg.press("#medriv", "Enter"); await pg.wait_for_timeout(200)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(120)
            marc = await pg.evaluate("() => window.__peli.m.rival + ' · al marcador: ' + document.body.innerText.includes('CH Parets')")
            print("P03: «%s» → desat: %s · després torna a: «%s»" % (v0, desat, fin))
            print("nom buit: %s" % buit)
            print("fletxa enrere: %s · P05 en curs amb Retorn: %s · botons fora de la pantalla o tallats: %d · errors: %s" % (fl, marc, surt, errs or "cap"))
            await b.close()
asyncio.run(main())
