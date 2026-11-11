# La manera nova d'apuntar: «Llançament» a la fase 2 i la porteria nova (resultat i lloc en un toc), amb tots els camins
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 8, 9)]
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
FIRST = "() => { const pn = document.querySelector('.panel.now'); const b = pn && [...pn.querySelectorAll('button')].find(x => x.getBoundingClientRect().width && /^\\d/.test(x.textContent.trim())); if (b) { b.click(); return b.textContent.trim().slice(0, 12); } return null; }"
# (nom, equip, dorsal, botó de la fase 2, zona, toc a la porteria, preguntes esperades després, camps esperats)
CASOS = [("Llançament i gol", "N", 3, "LL", "9C", "G:5", [], {"a": "G", "z": "9C", "g": 5, "as": None}),
         ("Assistència + llançament i gol", "N", 3, "LLA", "9C", "G:1", ["assist"], {"a": "G", "g": 1, "s": "*"}),
         ("Assistència + llançament i aturada", "N", 3, "LLA", "6C", "A:2", ["assist"], {"a": "A", "g": 2, "s": "*"}),
         ("Assistència + llançament i fora", "N", 3, "LLA", "9E", "F:T", ["assist"], {"a": "F", "fz": "T", "s": "*"}),
         ("Pal amb rebot", "N", 3, "LL", "9C", "P:TL:R", ["rebot"], {"a": "P", "pz": "TL", "po": "rebot", "rbe": "*"}),
         ("Pal amb fora", "N", 3, "LL", "9C", "P:L2:F", [], {"a": "P", "pz": "L2", "po": "fora", "rbe": None}),
         ("Fora", "N", 3, "LL", "9E", "F:R3", [], {"a": "F", "fz": "R3"}),
         ("Blocat per un defensor", "N", 3, "LL", "9C", "B", ["opp"], {"a": "B", "od": "*"}),
         ("7 m del rival, aturada", "R", 6, "LL", "7M", "A:5", [], {"a": "A", "z": "7M", "g": 5, "pv": "*"}),
         ("Contraatac directe", "N", 3, "CD", "6C", "G:9", [], {"a": "G", "ty": "CD", "g": 9}),
         ("Camp a camp", "N", 3, "CC", None, "G:5", [], {"a": "G", "ty": "CC", "g": 5}),
         ("Al porter: el rival li xuta i l'atura", "N", 1, "LL", "9C", "A:3", [], {"e": "R", "a": "A", "g": 3})]
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom_dev, dev, det in (("tauleta", {"viewport": {"width": 1280, "height": 800}}, "com"), ("mòbil", p.devices["Pixel 7"], "com"), ("mòbil Essencial", p.devices["Pixel 7"], "ess")):
            M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-14", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 1, "rgk": 16, "rivals": [{"d": 6, "n": "Rival Sis"}, {"d": 9, "n": "Rival Nou"}, {"d": 16, "n": "Porter Rival", "gk": True}], "acts": [], "seq": 0, "squad": [1, 2, 3, 4, 5, 6, 8, 9], "upd": 1, "det": det}
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-14"}}, "guideV": 1}
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print("== " + nom_dev + ":")
            casos = [c for c in CASOS if not (det == "ess" and c[0] not in ("Llançament i gol", "Fora", "Camp a camp"))]
            for nom, e, d, bt, z, gr, preg, esp in casos:
                n0 = await pg.evaluate("() => window.__peli.m.acts.length")
                if e == "N": await pg.evaluate(VIS, "#qui [data-act='player'][data-v='%d']" % d)
                elif nom_dev == "tauleta": await pg.evaluate(VIS, "[data-act='rplayer'][data-v='%d']" % d)
                else:
                    await pg.evaluate(VIS, "#qui [data-act='rival']"); await pg.wait_for_timeout(100)
                    if not await pg.evaluate(VIS, "[data-act='rplayer'][data-v='%d']" % d):
                        for ch in str(d): await pg.evaluate(VIS, "[data-act='digit'][data-v='%s']" % ch)
                        await pg.evaluate(VIS, "[data-act='padok']")
                await pg.wait_for_timeout(120)
                await pg.evaluate(VIS, "#que [data-act='ptype'][data-v='%s']" % bt); await pg.wait_for_timeout(150)
                vist = []
                for k in range(6):
                    st = await pg.evaluate("() => window.__peli.pending ? window.__peli.step() : 'fet'")
                    if st == "fet": break
                    vist.append(st)
                    if st == "zona": await pg.evaluate(VIS, "[data-act='zone'][data-v='%s']" % z)
                    elif st == "resultat":
                        ok_g = await pg.evaluate("() => !!document.querySelector('#que .gp .gpg') && document.querySelectorAll('#que [data-act=gres]').length")
                        await pg.evaluate(VIS, "#que [data-act='gres'][data-v='%s']" % gr)
                    else: await pg.evaluate(FIRST)
                    await pg.wait_for_timeout(150)
                a = await pg.evaluate("() => { const l = window.__peli.m.acts; return l.length ? l[l.length - 1] : null; }")
                n1 = await pg.evaluate("() => window.__peli.m.acts.length")
                q = [x for x in vist if x not in ("zona", "resultat", "prov7")]
                bo = n1 == n0 + 1 and a and (a["e"] == e and a["d"] == d or nom.startswith("Al porter")) and q == preg and all((a.get(k2) is not None) if v == "*" else (a.get(k2) == v) for k2, v in esp.items())
                if det == "ess": bo = n1 == n0 + 1 and "zona" not in vist and a and a["a"] == esp["a"] and q == preg
                mal += 0 if bo else 1
                print("   %s %-36s passos %s · desat %s" % ("✓" if bo else "✗", nom, vist, {k2: a.get(k2) for k2 in ("a", "z", "g", "pz", "po", "fz", "ty", "s", "as", "od", "rbe", "pv")} if a else None))
            if nom_dev == "mòbil":
                await pg.evaluate(VIS, "#qui [data-act='player'][data-v='3']"); await pg.evaluate(VIS, "#que [data-act='ptype'][data-v='LL']"); await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']"); await pg.wait_for_timeout(200)
                fit = await pg.evaluate("() => { const g = document.querySelector('#que .gp'); const r = g.getBoundingClientRect(); const bs = [...g.querySelectorAll('button')].map(x => x.getBoundingClientRect()); return { dins: r.right <= innerWidth + 0.5 && bs.every(q => q.right <= innerWidth + 0.5 && q.width >= 30), minH: Math.round(Math.min(...bs.map(q => q.height))) }; }")
                print("   %s la porteria cap a la pantalla del mòbil: %s" % ("✓" if fit["dins"] else "✗", fit)); mal += 0 if fit["dins"] else 1
                await (await pg.query_selector("#que")).screenshot(path="/tmp/porteria_app_mobil.png")
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
