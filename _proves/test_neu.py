# Neutralització: botó al grup «Pilota», es desa d'un toc, suma al balanç i a la defensa del radar, columna «Neutr.» només si n'hi ha, i al CSV
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys, csv, io
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 7, 8, 9)]
def A(i, e, d, a, t, **kw):
    x = {"i": i, "t": t, "p": 1, "e": e, "d": d, "a": a, "k": None, "z": "9C" if a in ("G", "A", "F") else None, "g": None, "s": None, "gk": 1, "rgk": None}; x.update(kw); return x
def match(mid, date, acts, det, cur):
    return {"id": mid, "rival": "CH Prova", "date": date, "durada": 30, "part": 1 if cur else 2, "clock": {"acc": 600 if cur else 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [],
            "acts": acts, "seq": len(acts), "squad": [1, 2, 3, 4, 5, 6, 7, 8, 9], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1, "det": det}
SENSE = match("P01", "2026-10-31", [A(1, "N", 5, "G", 30), A(2, "N", 5, "REC", 60), A(3, "R", 4, "G", 90)], "com", False)
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        for nom, dev, det in (("tauleta, Complet", {"viewport": {"width": 1280, "height": 800}}, "com"), ("mòbil, Ràpid", p.devices["Pixel 7"], "rap"), ("iPhone SE, Essencial", p.devices["iPhone SE"], "ess")):
            cur = match("P02", "2026-11-07", [A(1, "N", 5, "G", 30), A(2, "N", 5, "REC", 60), A(3, "R", 4, "G", 90)], det, True)
            ms = [SENSE, cur]
            idx = {mm["id"]: {"rival": "CH Prova", "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": mm["id"] == "P01", "tr": 0} for mm in ms}
            app = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P02", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": idx, "guideV": 1}
            init = "window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app)) + "); " + \
                   "".join("{ const M = " + json.dumps(mm) + "; " + ("M.clock.start = Date.now() - 1000; " if mm["id"] == "P02" else "") + "localStorage.setItem('peli-directe:m:" + mm["id"] + "', JSON.stringify(M)); } " for mm in ms) + "}"
            b = await p.chromium.launch(); ctx = await b.new_context(accept_downloads=True, **dev); await ctx.add_init_script(init)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(700)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print(nom + ":")
            await pg.evaluate("() => [...document.querySelectorAll(\"#qui [data-act='player'][data-v='5']\")].find(x => x.getBoundingClientRect().width).click()"); await pg.wait_for_timeout(200)
            bt = await pg.evaluate("""() => { const b = [...document.querySelectorAll("#que [data-act='action'][data-v='NEU']")].find(x => x.getBoundingClientRect().width); if (!b) return null; const r = b.getBoundingClientRect(), q = document.getElementById('que').getBoundingClientRect();
              return { text: b.textContent.trim(), grup: (b.closest('.grp, .qg') || {}).querySelector ? b.closest('.grp, .qg').querySelector('h3').textContent : '', dins: r.right <= innerWidth + 0.5 && r.bottom <= innerHeight + 0.5 && r.left >= q.left - 0.5, h: Math.round(r.height) }; }""")
            ok(bt and bt["text"] == "Neutralització" and bt["grup"] == "Pilota" and bt["dins"], "botó al grup «Pilota», dins de la pantalla: %s" % bt)
            await pg.evaluate("() => [...document.querySelectorAll(\"#que [data-act='action'][data-v='NEU']\")].find(x => x.getBoundingClientRect().width).click()"); await pg.wait_for_timeout(300)
            last = await pg.evaluate("() => { const m = window.__peli.m; return [m.acts[m.acts.length - 1].a, m.acts[m.acts.length - 1].d, !!window.__peli.pending]; }")
            ok(last == ["NEU", 5, False], "es desa d'un toc, sense preguntes: %s" % last)
            # informe del partit en curs: columna «Neutr.», balanç i radar
            await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'jugadors').click()"); await pg.wait_for_timeout(300)
            t = await pg.evaluate("""() => { const tb = document.querySelector('#rep table.rt'); const hs = [...tb.querySelectorAll('tr')[0].children].map(x => x.textContent.trim());
              const row = [...tb.querySelectorAll('tr')].find(tr => (tr.children[0] || {}).textContent === '5'); const v = row ? [...row.children].map(x => x.textContent.trim()) : [];
              return { neu: hs.indexOf('Neutr.') >= 0 ? v[hs.indexOf('Neutr.')] : null, bal: v[hs.indexOf('Balanç')] }; }""")
            ok(t["neu"] == "1" and t["bal"] in ("+3", "3"), "taula de jugadors: «Neutr.» = %s · balanç del 5 = %s (gol + recuperació + neutralització)" % (t["neu"], t["bal"]))
            # informe d'un partit sense neutralitzacions: sense la columna
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === 'P01')); s.value = 'P01'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const t = [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'jugadors'); if (t) t.click(); }"); await pg.wait_for_timeout(300)
            sense = await pg.evaluate("() => [...document.querySelector('#rep table.rt tr').children].some(x => x.textContent.trim() === 'Neutr.')")
            ok(not sense, "en un partit sense neutralitzacions, la taula queda com abans (sense «Neutr.»)")
            # CSV del partit en curs
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === 'P02')); s.value = 'P02'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(400)
            async with pg.expect_download() as dl:
                await pg.evaluate("() => document.querySelector(\"#rep [data-act='rcsv']\").click()")
            d = await dl.value; path = "/tmp/neu.csv"; await d.save_as(path)
            rows = list(csv.reader(io.StringIO(open(path, encoding="utf-8-sig").read()), delimiter=";"))
            ok(any(r[rows[0].index("Acció")] == "Neutralització" and r[rows[0].index("Dorsal")] == "5" for r in rows[1:]), "al CSV, la fila «Neutralització» del 5")
            if nom.startswith("iPhone"):
                await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
                await pg.evaluate("() => [...document.querySelectorAll(\"#qui [data-act='player'][data-v='3']\")].find(x => x.getBoundingClientRect().width).click()"); await pg.wait_for_timeout(250)
                await pg.screenshot(path="/tmp/neu_se.png")
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
