# Objectius de millora: s'afegeixen des de la fitxa, l'estat es calcula bé, es conserven, es poden treure i surten al PDF
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7, 9)]
acts = []; i = [0]
def A(e, d, a, p, **kw):
    i[0] += 1; x = {"i": i[0], "t": (p - 1) * 1800 + 10 * (i[0] % 170) + 5, "p": p, "e": e, "d": d, "a": a, "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": 16}; x.update(kw); acts.append(x)
# l'equip (amb els llançaments del 7): 1a part 29 de 50 (58 %, contra 6-0), 2a part 18 de 46 (39 %, contra 5-1); de 9 m 17 de 50 (34 %), de 6 m 26 de 40 (65 %)
for p, df, gf, gn in ((1, "6-0", 8, 16), (2, "5-1", 4, 10)):
    for k in range(20): A("N", [3, 5, 9][k % 3], "G" if k < gf else "F", p, z="9C", df=df)
    for k in range(20): A("N", [3, 5, 9][k % 3], "G" if k < gn else "F", p, z="6C", df=df)
for k, t in enumerate(["MP"] * 6 + ["PS"] * 3 + ["FA"] * 3): A("N", [3, 5, 9][k % 3], "PER", 1 + k % 2, k=t, z=None)
for k in range(24): A("R", 4, "G", 1 + k % 2, ty="CD" if k < 8 else None)
# el jugador 7: 10 llançaments a porteria, 6 a baix a l'esquerra (zona 7); i 6 de 7 m, 4 gols
for k in range(10): A("N", 7, "G" if k % 2 == 0 else "A", 1, z="9E", g=7 if k < 6 else 2)
for k in range(6): A("N", 7, "G" if k < 4 else "A", 2, z="7M", g=5)
half = len(acts) // 2
MS = [{"id": "P0%d" % (n + 1), "rival": "Rival %d" % n, "date": "2026-10-%02d" % (10 + 7 * n), "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": 16, "rivals": [],
       "acts": part, "seq": len(part), "squad": [1, 3, 5, 7, 9], "upd": 1} for n, part in enumerate((acts[:half], acts[half:]))]
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "done": True, "tr": 0} for mm in MS}

async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1}
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 900})
        await ctx.add_init_script("window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}")
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
        async def fitxa():
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close'], #rep [data-act='rclose']\"); if (c && c.offsetParent) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === '7' && /Jugador 7/.test(o.textContent))); s.value = '7'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(500)
        async def afegeix(m, t, pl="", ln="", dl=""):
            await pg.evaluate("() => document.querySelector(\"#rep [data-act='objadd']\").click()"); await pg.wait_for_timeout(250)
            await pg.evaluate("(a) => { document.getElementById('objm').value = a[0]; document.getElementById('objt').value = a[1]; document.getElementById('objp').value = a[2]; document.getElementById('objl').value = a[3]; document.getElementById('objd').value = a[4]; document.querySelector(\"#ov [data-act='objsave']\").click(); }", [m, t, pl, ln, dl]); await pg.wait_for_timeout(300)
        LLEGEIX = "() => [...document.querySelectorAll('#rep .repcard.objs .obj')].map(o => o.textContent.replace(/\\s+/g, ' ').replace('Treu', '').trim())"
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
        await fitxa()
        await afegeix("ef9", "45", "Dues sessions de 9 m a la setmana", "https://drive.google.com/planificacio", "2026-12-20")
        for m, t in (("ef7", "75"), ("per", "1")): await afegeix(m, t)
        await afegeix("gol", "5", "", "javascript:alert(1)", "")
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
        o = await pg.evaluate(LLEGEIX)
        for x in o: print("      " + x)
        ok(len(o) == 3 and "Assolit" in o[0] and "Ara: 50%" in o[0] and "En progrés" in o[1] and "Ara: 67%" in o[1] and "Assolit" in o[2] and "Ara: 0" in o[2], "els tres objectius, amb l'estat correcte (l'enllaç perillós no s'accepta)")
        ok("Pla d'acció: Dues sessions de 9 m a la setmana" in o[0] and "Planificació: https://drive.google.com/planificacio" in o[0] and "Data límit: 20/12/2026" in o[0], "pla d'acció, enllaç i data límit a la fitxa")
        await pg.reload(); await pg.wait_for_timeout(600); await fitxa()
        ok(len(await pg.evaluate(LLEGEIX)) == 3, "es conserven en tornar a obrir l'app")
        await pg.evaluate("() => document.querySelectorAll(\"#rep [data-act='objdel']\")[2].click()"); await pg.wait_for_timeout(300)
        o2 = await pg.evaluate(LLEGEIX)
        ok(len(o2) == 2 and not any("Pèrdues" in x for x in o2), "es pot treure un objectiu")
        await pg.evaluate("() => { const b = [...document.querySelectorAll('#rep .pfx button')].find(x => x.getAttribute('data-act') !== 'pshare'); b.click(); }"); await pg.wait_for_timeout(900)
        pdf = await pg.evaluate("() => { const c = document.querySelector('#print .repcard.objs'); return c ? [c.querySelectorAll('.obj').length, c.querySelectorAll('button').length + c.querySelectorAll('a').length] : null; }")
        ok(pdf == [2, 0], "al PDF de la fitxa surten els objectius, sense botons (%s)" % (pdf,))
        await pg.evaluate("() => { const a = JSON.parse(localStorage.getItem('peli-directe:app')); a.lang = 'es'; localStorage.setItem('peli-directe:app', JSON.stringify(a)); }")
        await pg.reload(); await pg.wait_for_timeout(600); await fitxa()
        es = await pg.evaluate("() => { const c = document.querySelector('#rep .repcard.objs'); return c ? c.querySelector('h3').textContent + ' | ' + c.textContent.replace(/\\s+/g, ' ').slice(0, 120) : ''; }")
        ok(es.startswith("Objetivos de mejora") and "Logrado" in es and "Plan de acción" in es and "Eficàcia" not in es, "en castellà: %s" % es[:110])
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
