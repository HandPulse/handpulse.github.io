# Troballes automàtiques: amb una temporada inventada, l'informe de la temporada i la fitxa del jugador diuen exactament el que s'espera
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
ESP_EQUIP = ["Encertem menys a la segona part: 58% a la 1a i 39% a la 2a.", "Des de 9 m encertem el 34%; des de 6 m i els extrems, el 65%.", "Contra la defensa 5-1 encertem el 35%; contra la 6-0, el 60%.", "La pèrdua més freqüent és «Mal passe»: 6 de 12.", "El 33% dels gols que rebem són de contraatac."]
ESP_7 = ["Sol posar la pilota a baix a l'esquerra: 6 de 10 llançaments a porteria.", "En els 7 m: 4 de 6 (67%)."]
async def main():
    async with async_playwright() as p:
        mal = 0
        for lang in ("ca", "es"):
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1, "lang": lang}
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 900})
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(600)
            eq = await pg.evaluate("() => [...document.querySelectorAll('#rep .repcard.trob li')].map(x => x.textContent)")
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === '7' && /Jugador 7/.test(o.textContent))); s.value = '7'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(500)
            j7 = await pg.evaluate("() => [...document.querySelectorAll('#rep .repcard.trob li')].map(x => x.textContent)")
            print(lang + ":")
            if lang == "ca":
                ok1 = all(x in eq for x in ESP_EQUIP); ok2 = all(x in j7 for x in ESP_7)
                print("   %s equip: %s" % ("✓" if ok1 else "✗", eq)); print("   %s jugador 7: %s" % ("✓" if ok2 else "✗", j7)); mal += (0 if ok1 else 1) + (0 if ok2 else 1)
            else:
                cat = [x for x in eq + j7 if any(w in x for w in ("Encertem", "encertem", "pèrdua", "rebem", "Sol posar", "els 7 m"))]
                ok3 = len(eq) >= 4 and not cat; mal += 0 if ok3 else 1
                print("   %s en castellà, cap frase en català: %s" % ("✓" if ok3 else "✗", (eq[:2] if ok3 else cat[:2])))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
