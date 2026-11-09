# CSV amb les columnes noves, correccions de textos per idioma (identificadors fixos) i política de seguretat a l'index.html
import asyncio, json, sys, os, csv, io
DIR = os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5)]
W0 = 1794200000000
ACTS = [{"i": 1, "t": 75, "p": 1, "e": "N", "d": 2, "a": "G", "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": None, "w": W0, "star": 1},
        {"i": 2, "t": 130, "p": 1, "e": "R", "d": 4, "a": "F", "k": None, "z": "9E", "g": None, "s": None, "gk": 1, "rgk": None, "w": W0 + 55000},
        {"i": 3, "t": 200, "p": 1, "e": "N", "d": 3, "a": "PER", "k": "MP", "z": None, "g": None, "s": None, "gk": 1, "rgk": None}]
M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-08", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": ACTS, "seq": 3, "squad": [1, 2, 3, 4, 5], "upd": 1, "det": "ess"}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 3, "upd": 1, "sc": [1, 0], "date": "2026-11-08"}}, "guideV": 1}
INIT = "window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800}, accept_downloads=True); await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); errs = []; csp = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:150])); pg.on("console", lambda m: csp.append(m.text[:160]) if "Content Security Policy" in m.text or "Content-Security-Policy" in m.text else None)
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(700)
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
        # 1) CSV: les tres columnes noves al final
        await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(500)
        async with pg.expect_download() as dl:
            await pg.evaluate("() => document.querySelector(\"#rep [data-act='rcsv']\").click()")
        d = await dl.value; path = "/tmp/hp_accions.csv"; await d.save_as(path)
        rows = list(csv.reader(io.StringIO(open(path, encoding="utf-8-sig").read()), delimiter=";"))
        h = rows[0]; byi = {r[h.index("Minut")] + r[h.index("Dorsal")]: r for r in rows[1:]}
        g = next(r for r in rows[1:] if r[h.index("Acció")] == "Gol"); per = next(r for r in rows[1:] if r[h.index("Acció")] == "Pèrdua")
        import datetime; hw = datetime.datetime.fromtimestamp(W0 / 1000).strftime("%H:%M:%S")
        print("CSV:")
        ok(h[-3:] == ["Segon", "Hora real", "Destacada"] and h[:4] == ["Data", "Partit", "Part", "Minut"], "columnes: les d'abans al seu lloc i, al final, %s" % h[-3:])
        ok(g[-3:] == ["75", hw, "★"] and per[-3:] == ["200", "", ""], "gol: %s · pèrdua sense hora real ni estrella: %s" % (g[-3:], per[-3:]))
        await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
        # 2) correccions de textos: en català i en castellà, sense tocar la resta
        print("Correccions de textos:")
        await pg.evaluate("() => { window.__peli.tfix.ca['Totes les accions'] = 'Totes les jugades'; document.querySelector(\"#foot [data-act='all']\").click(); }"); await pg.wait_for_timeout(300)
        ca = await pg.evaluate("() => [document.querySelector('#ov h2').textContent, (document.querySelector('#ov p.note') || {}).textContent]")
        ok(ca[0] == "Totes les jugades" and ca[1] == "Toca una capçalera per ordenar.", "català: títol corregit «%s» · la resta igual «%s»" % tuple(ca))
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); const a = JSON.parse(localStorage.getItem('peli-directe:app')); a.lang = 'es'; localStorage.setItem('peli-directe:app', JSON.stringify(a)); }")
        await pg.reload(); await pg.wait_for_timeout(700)
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); window.__peli.tfix.es['Totes les accions'] = 'Todas las jugadas'; document.querySelector(\"#foot [data-act='all']\").click(); }"); await pg.wait_for_timeout(300)
        es = await pg.evaluate("() => [document.querySelector('#ov h2').textContent, (document.querySelector('#ov p.note') || {}).textContent, window.__peli.app.lang]")
        ok(es[0] == "Todas las jugadas" and es[1] == "Toca una cabecera para ordenar." , "castellà (%s): títol corregit «%s» · la resta, la traducció de sempre «%s»" % (es[2], es[0], es[1]))
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); }")
        # 3) política de seguretat: cap avís en l'ús normal, i un programa d'una altra web queda bloquejat
        print("Política de seguretat:")
        meta = await pg.evaluate("() => !!document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]')")
        csp_us = list(csp)
        bloc = await pg.evaluate("""() => new Promise(r => { let v = null; document.addEventListener('securitypolicyviolation', e => { v = e.blockedURI; }); const s = document.createElement('script'); s.src = 'https://exemple.com/codi.js'; document.head.appendChild(s); setTimeout(() => r(v), 600); })""")
        ok(meta and not csp_us, "a l'index.html hi és, i en l'ús normal no bloqueja res (avisos: %s)" % (csp_us or "cap"))
        ok(bloc and "exemple.com" in bloc, "un programa d'una altra web queda bloquejat (%s)" % bloc)
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
