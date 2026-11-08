# Focus de l'entrenament (informe del partit) i progressió i rècords (fitxa del jugador), comprovats amb xifres calculades aquí
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7, 9, 11)]
G7 = [1, 1, 2, 5, 6]          # gols del 7 a cada partit (millora)
CA_R = [1, 2, 1, 2, 6]        # gols rebuts en contraatac (el 5è partit, molts)
MP = [1, 1, 1, 1, 7]          # pèrdues per mal passe
LAT = [(10, 4), (10, 4), (10, 4), (10, 4), (11, 2)]   # llançaments des dels laterals: (llançaments, gols)
def match(n):
    acts = []; i = [0]
    def A(e, d, a, **kw):
        i[0] += 1; x = {"i": i[0], "t": 20 * i[0], "p": 1 if i[0] < 60 else 2, "e": e, "d": d, "a": a, "k": None, "z": None, "g": None, "s": None, "gk": 1, "rgk": 16}; x.update(kw); acts.append(x)
    t, g = LAT[n]
    # laterals: el 7 marca G7[n] (si en té), la resta de gols i fallades les fa el 9; el 7 també llança la resta des del 9 m centre
    g7 = min(G7[n], g)
    for k in range(g7): A("N", 7, "G", z="9E")
    for k in range(g - g7): A("N", 9, "G", z="9D")
    for k in range(t - g): A("N", 9, "F", z="9E")
    for k in range(G7[n] - g7): A("N", 7, "G", z="9C")
    for k in range(2): A("N", 5, "G", z="9C")
    for k in range(2): A("N", 5, "F", z="9C")
    for k in range(MP[n]): A("N", 3, "PER", k="MP")
    A("N", 11, "PER", k="PS"); A("N", 3, "REC"); A("N", 7, "REC")
    for k in range(CA_R[n]): A("R", 4, "G", z="6C", ty="CD")
    for k in range(3): A("R", 8, "G", z="9E")
    for k in range(8): A("R", 8, "A", z="9E")
    return {"id": "P0%d" % (n + 1), "rival": "Rival %d" % (n + 1), "date": "2026-10-%02d" % (3 + 7 * n), "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": 16,
            "rivals": [], "acts": acts, "seq": len(acts), "squad": [1, 3, 5, 7, 9, 11], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1, "done": True}
MS = [match(n) for n in range(5)]
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": True, "tr": 0} for mm in MS}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1}
INIT = "window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + \
       "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}"
# el que hauria de sortir, calculat aquí: P05 comparat amb P01–P04
nP = 4; refCA = sum(CA_R[:4]) / nP; refMP = sum(MP[:4]) / nP; tl = sum(x[0] for x in LAT[:4]); gl = sum(x[1] for x in LAT[:4]); refLAT = gl / tl
f1 = lambda v: (str(round(v * 10) / 10).rstrip("0").rstrip(".") if v != int(v) else str(int(v))).replace(".", ",")
ESP = [(CA_R[4] - refCA, "Gols rebuts · Contraatac: %d · temporada %s per partit" % (CA_R[4], f1(refCA))),
       (0.5 * (MP[4] - refMP), "Pèrdues · Mal passe: %d · temporada %s per partit" % (MP[4], f1(refMP))),
       (LAT[4][0] * refLAT - LAT[4][1], "Llançament · Laterals: %d de %d (%d%%) · temporada %d%%" % (LAT[4][1], LAT[4][0], round(100 * LAT[4][1] / LAT[4][0]), round(100 * refLAT)))]
ESP = [x[1] for x in sorted(ESP, key=lambda x: -x[0])]
async def obre_informe(pg, mid):
    await pg.evaluate("(id) => { const ov = document.getElementById('ov'); if (!ov.hidden) { const c = ov.querySelector(\"[data-act='close']\"); if (c) c.click(); } document.querySelector(\"#home [data-act='seasonrep']\").click(); }", mid); await pg.wait_for_timeout(400)
    await pg.evaluate("(id) => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === id)); if (s) { s.value = id; s.dispatchEvent(new Event('change', { bubbles: true })); } }", mid); await pg.wait_for_timeout(450)
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(INIT)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(500)
            # 1) focus del P05 (comparat amb els anteriors)
            await obre_informe(pg, "P05")
            f = await pg.evaluate("() => { const c = document.querySelector('#rep .repcard.focus'); return c ? { sub: (c.querySelector('p.note') || c.querySelector('h3 small')).textContent, items: [...c.querySelectorAll('li')].map(x => x.textContent.trim()), vis: c.checkVisibility() } : null; }")
            ok1 = f and f["items"] == ESP and f["vis"]; mal += 0 if ok1 else 1
            print("%s %s · focus del P05: %s" % ("✓" if ok1 else "✗", nom, json.dumps(f, ensure_ascii=False)))
            if not ok1: print("   esperat: %s" % ESP)
            if nom == "mòbil": await (await pg.query_selector("#rep .repcard.focus")).screenshot(path="/tmp/focus_mobil.png")
            # 2) primer partit: sense prou partits anteriors
            await obre_informe(pg, "P01")
            f0 = await pg.evaluate("() => { const c = document.querySelector('#rep .repcard.focus'); return c ? { sub: (c.querySelector('p.note') || c.querySelector('h3 small')).textContent.slice(0, 70), items: [...c.querySelectorAll('li')].map(x => x.textContent.trim()) } : null; }")
            ok2 = f0 and "encara no hi ha prou" in f0["sub"]; mal += 0 if ok2 else 1
            print("%s %s · focus del P01: %s" % ("✓" if ok2 else "✗", nom, json.dumps(f0, ensure_ascii=False)))
            # 3) fitxa del 7 des del P05: progressió, rècords i fites
            await obre_informe(pg, "P05")
            await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'jugadors').click()"); await pg.wait_for_timeout(250)
            await pg.evaluate("() => { const b = [...document.querySelectorAll(\"#rep table.rt [data-act][data-v='7']\")][0]; if (b) b.click(); }"); await pg.wait_for_timeout(400)
            pr = await pg.evaluate("""() => { const c = document.querySelector('#rep .repcard.prog'); if (!c) return null;
              const rows = {}; [...c.querySelectorAll('table.rt tr')].slice(1).forEach(tr => { const t = [...tr.children]; rows[t[0].textContent.trim()] = [t[1].textContent, t[2].textContent, t[1].className]; });
              const tw = c.querySelector('.tw'); return { taula: tw ? Math.max(tw.scrollWidth - tw.clientWidth, 0) : 0, rows, recs: [...c.querySelectorAll('ul.recs li')].map(x => x.textContent.replace(/\\s+/g, ' ').trim()), fites: [...c.querySelectorAll('.fita')].map(x => x.textContent), surt: Math.max(c.scrollWidth - c.clientWidth, 0) }; }""")
            last = sum(G7[2:]) / 3; prev = sum(G7[:2]) / 2
            gp = pr and pr["rows"].get("Gols per partit")
            ok3 = pr and gp and gp[0] == f1(last) + " ▲" and gp[1] == f1(prev) and gp[2] == "pos" and any(r.startswith("Més gols en un partit%d" % max(G7)) for r in pr["recs"]) and \
                  "%d gols" % 10 in pr["fites"] and "5 partits jugats" in pr["fites"] and pr["surt"] == 0 and pr["taula"] == 0 and not any("recuperacions en un partit1" in r for r in pr["recs"])
            mal += 0 if ok3 else 1
            print("%s %s · fitxa del 7: gols per partit %s · rècords %s · fites %s · se surt %s px · la taula se surt %s px" % ("✓" if ok3 else "✗", nom, gp, [r[:45] for r in (pr or {}).get("recs", [])][:3], (pr or {}).get("fites"), (pr or {}).get("surt"), (pr or {}).get("taula")))
            if nom == "mòbil" and pr: await (await pg.query_selector("#rep .repcard.prog")).screenshot(path="/tmp/prog_mobil.png")
            # 4) al PDF de l'informe hi ha el focus
            pdf = await pg.evaluate("""() => new Promise(r => { const t = [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'resum'); if (t) t.click();
              setTimeout(() => { const b = document.querySelector(\"#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']\"); if (b) b.click(); setTimeout(() => r([...document.querySelectorAll('section.pp')].map(x => x.innerHTML).join('').includes('focusl')), 900); }, 300); })""")
            mal += 0 if pdf else 1
            print("%s %s · el focus surt al PDF: %s · errors %s" % ("✓" if pdf else "✗", nom, pdf, errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
