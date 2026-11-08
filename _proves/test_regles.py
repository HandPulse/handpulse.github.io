# Revisió de les preguntes de cada acció, als 3 nivells, al mòbil i a la tauleta, comparades amb les regles dels tècnics
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/peligrograma_directe.html"
ROSTER = [{"d": d, "n": "J" + str(d), "gk": d == 1} for d in (1, 2, 3, 5, 6, 7, 9)]
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {}}
# (nom, equip, accions inicials, preguntes esperades per nivell, camps que s'han de desar a Complet)
F = [
  ("Pèrdua mal passe", "N", [("A", "PER"), ("T", "MP")], {"com": ["opp"], "rap": [], "ess": []}, ["od"]),
  ("Pèrdua mal bot", "N", [("A", "PER"), ("T", "CM")], {"com": ["opp"], "rap": [], "ess": []}, ["od"]),
  ("Pèrdua falta en atac", "N", [("A", "PER"), ("T", "FA")], {"com": ["opp"], "rap": [], "ess": []}, ["od"]),
  ("Pèrdua joc passiu", "N", [("A", "PER"), ("T", "JP")], {"com": ["opp"], "rap": [], "ess": []}, ["od"]),
  ("Pèrdua passos", "N", [("A", "PER"), ("T", "PS")], {"com": [], "rap": [], "ess": []}, []),
  ("2 minuts", "N", [("A", "2M")], {"com": ["opp"], "rap": ["opp"], "ess": ["opp"]}, ["od"]),
  ("Gol de 7 m", "N", [("A", "G"), ("Z", "7M")], {"com": ["porteria", "prov7"], "rap": ["prov7"], "ess": None}, ["pv"]),
  ("Pal (rebot)", "N", [("A", "P"), ("Z", "9C")], {"com": ["rebot"], "rap": [], "ess": []}, ["rbe"]),
  ("Blocatge (de qui i rebot)", "N", [("A", "BLQ")], {"com": ["opp", "rebot"], "rap": [], "ess": []}, ["od", "rbe"]),
  ("Assistència + gol", "N", [("A", "GA"), ("Z", "6C")], {"com": ["porteria", "assist"], "rap": ["assist"], "ess": ["assist"]}, ["s"]),
  ("Pèrdua del rival (mal passe)", "R", [("A", "PER"), ("T", "MP")], {"com": ["opp"], "rap": [], "ess": []}, ["od"]),
  ("2 minuts al rival", "R", [("A", "2M")], {"com": ["opp"], "rap": ["opp"], "ess": ["opp"]}, ["od"]),
  ("7 m del rival", "R", [("A", "G"), ("Z", "7M")], {"com": ["porteria", "prov7"], "rap": ["prov7"], "ess": None}, ["pv"]),
]
async def main():
    async with async_playwright() as p:
        mal = 0; tot = 0
        for nom, dev in (("mobil", p.devices["Pixel 7"]), ("tauleta", {"viewport": {"width": 1280, "height": 800}})):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); document.querySelector(\"#home [data-act='partits']\").click(); }"); await pg.wait_for_timeout(100)
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='pnew']\").click()"); await pg.wait_for_timeout(150)
            await pg.evaluate("() => { const s = document.getElementById('nfix'); if (s) { s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); } const set = (id, v) => { const e = document.getElementById(id); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); } }; set('nriv', 'CH Prova'); set('nrivals', '4 R4\\n7 R7\\n11 R11'); }")
            await pg.evaluate("() => { document.querySelector(\"[data-act='sqall']\").click(); document.querySelector(\"[data-act='nstart']\").click(); }"); await pg.wait_for_timeout(350)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
            tap = lambda s: pg.evaluate(VIS, s)
            st = lambda: pg.evaluate("() => window.__peli.step()")
            print(nom + ":")
            for lv in ("com", "rap", "ess"):
                await pg.evaluate("(l) => { window.__peli.m.det = l; }", lv)
                for ix, (fn, eq, init, exp, camps) in enumerate(F):
                    if exp.get(lv) is None: continue
                    tot += 1
                    # el rellotge avança 2′30″ entre cas i cas (perquè cap exclusió bloquegi el jugador) i es van alternant els jugadors
                    await pg.evaluate("() => { window.__peli.m.clock.acc = (window.__peli.m.clock.acc || 0) + 150; }")
                    nd = [2, 3, 5, 6, 7, 9][ix % 6]; rd = [4, 7, 11][ix % 3]
                    if eq == "N": await tap("#qui [data-act='player'][data-v='" + str(nd) + "']")
                    else:
                        if nom == "mobil": await tap("#qui [data-act='rival']")
                        await tap("[data-act='rplayer'][data-v='" + str(rd) + "']")
                    vist = []
                    for k, v in init:
                        if k == "A": await tap("#que [data-act='action'][data-v='" + v + "']")
                        elif k == "T":
                            s0 = await st()
                            if s0 == "tipus": vist.append("tipus"); await tap("[data-act='tipus'][data-v='" + v + "']")
                        elif k == "Z":
                            s0 = await st()
                            if s0 == "zona": await tap("[data-act='zone'][data-v='" + v + "']")
                    for _ in range(8):
                        s0 = await st()
                        if s0 in ("qui", "cap"): break
                        vist.append(s0)
                        if s0 == "porteria": await tap("[data-act='goal'][data-v='5']")
                        elif s0 == "opp": await tap("#on [data-act='opp'][data-v]:not([data-v='']):not([data-v='PF']):not([data-v='PR'])")
                        elif s0 == "prov7": await tap("#on [data-act='prov7'][data-v]:not([data-v=''])")
                        elif s0 == "rebot": await tap("#on [data-act='rebot'][data-v]:not([data-v='']):not([data-v='A'])")
                        elif s0 == "assist": await tap("#on [data-act='assist'][data-v]:not([data-v=''])")
                        elif s0 == "zona": await tap("[data-act='zone'][data-v='9C']")
                        else: break
                    vist = [x for x in vist if x not in ("tipus", "zona")]
                    a = await pg.evaluate("() => window.__peli.m.acts.slice(-1)[0] || {}")
                    falten = [c for c in (camps if lv == "com" else [c for c in camps if (c == "od" and "opp" in exp[lv]) or (c == "pv" and "prov7" in exp[lv]) or (c == "s" and "assist" in exp[lv])]) if a.get(c) in (None, "")]
                    ok = vist == exp[lv] and not falten
                    if not ok: mal += 1
                    print("   %-4s %-28s preguntes: %-24s %s" % (lv, fn, ", ".join(vist) or "cap", "✓" if ok else "✗ esperat: " + (", ".join(exp[lv]) or "cap") + (" · falta desar " + ", ".join(falten) if falten else "")))
            print("   errors: " + str(errs or "cap"))
            await b.close()
        print("RESUM: %d casos · incorrectes: %d" % (tot, mal))
asyncio.run(main())
