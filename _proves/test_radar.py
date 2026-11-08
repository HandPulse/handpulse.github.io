import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (3, 5, 7, 9)]
def A(i, t, d, a, **kw):
    x = {"i": i, "t": t, "p": 1 if t < 1800 else 2, "e": "N", "d": d, "a": a, "k": None, "z": "9C" if a in ("G", "A", "F", "P") else None, "g": None, "s": None, "gk": 1}
    x.update(kw); return x
def match(mid, date, plays):
    acts = [A(i + 1, 60 * (i + 1), d, a, **kw) for i, (d, a, kw) in enumerate(plays)]
    return {"id": mid, "rival": "Rival " + mid, "date": date, "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": acts, "seq": len(acts),
            "squad": [1, 3, 5, 7, 9], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1}
P01 = match("P01", "2026-10-03", [(7, "G", {}), (7, "G", {}), (7, "G", {}), (7, "F", {}), (9, "G", {"s": 7}), (9, "A", {}), (9, "A", {}), (5, "PER", {"k": "PS"}), (5, "PER", {"k": "PS"}), (5, "BLQ", {}), (3, "2M", {}), (3, "PER", {"k": "MR"})])
P02 = match("P02", "2026-10-10", [(7, "G", {}), (7, "P", {}), (7, "PER", {"k": "MR"}), (9, "G", {}), (9, "G", {}), (5, "G", {}), (5, "BLQ", {}), (3, "PER", {"k": "PS"})])
P03 = match("P03", "2026-10-17", [(7, "G", {}), (7, "G", {}), (9, "F", {}), (9, "PER", {"k": "PS"}), (5, "PER", {"k": "MP"}), (3, "G", {}), (3, "2M", {})])
MS = [P01, P02, P03]
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": True, "tr": 0} for mm in MS}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX}
INIT = "window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + \
       "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}"
# eficàcia ajustada, calculada aquí pel seu compte: (G + 10·pb) / (T + 10), amb pb l'eficàcia de tots els jugadors de camp
def _adj():
    G, T = {}, {}
    for mm in MS:
        for x in mm["acts"]:
            if x["e"] == "N" and x["d"] in (3, 5, 7, 9) and x["a"] in ("G", "A", "F", "P", "B"):
                T[x["d"]] = T.get(x["d"], 0) + 1; G[x["d"]] = G.get(x["d"], 0) + (x["a"] == "G")
    pb = sum(G.values()) / sum(T.values())
    adj = {d: (G.get(d, 0) + 10 * pb) / (T.get(d, 0) + 10) for d in (3, 5, 7, 9)}
    return "%d%% (%d de %d)" % (round(100 * adj[7]), G[7], T[7]), "%d%%" % round(100 * sum(adj.values()) / 4)
EF7, EFM = _adj()
# seguretat i balanç per cada 10 accions, calculats aquí pel seu compte: les accions del balanç (positives i negatives) de cada jugador
def _per10():
    BP, BM, PER = {}, {}, {}
    for mm in MS:
        for x in mm["acts"]:
            if x["e"] != "N": continue
            if x["a"] == "G" and x.get("s") is not None: BP[x["s"]] = BP.get(x["s"], 0) + 1   # assistència
            d = x["d"]
            if d not in (3, 5, 7, 9) or x.get("o"): continue
            if x["a"] in ("G", "7MP", "2MP", "REC", "BLQ"): BP[d] = BP.get(d, 0) + 1
            if x["a"] in ("A", "P", "F", "B", "PER", "2M", "TV"): BM[d] = BM.get(d, 0) + 1
            if x["a"] == "PER": PER[d] = PER.get(d, 0) + 1
    seg = {d: (10 * PER.get(d, 0) / (BP.get(d, 0) + BM.get(d, 0)) if BP.get(d, 0) + BM.get(d, 0) else 0) for d in (3, 5, 7, 9)}
    bal = {d: (10 * (BP.get(d, 0) - BM.get(d, 0)) / (BP.get(d, 0) + BM.get(d, 0)) if BP.get(d, 0) + BM.get(d, 0) else 0) for d in (3, 5, 7, 9)}
    f = lambda v, sg=False: ("+" if sg and v > 0.05 else "") + ("%.1f" % (round(v * 10) / 10)).replace(".", ",").replace(",0", "") if abs(round(v * 10) / 10 - round(v)) < 1e-9 else ("+" if sg and v > 0.05 else "") + ("%.1f" % (round(v * 10) / 10)).replace(".", ",")
    return (f(seg[7]), f(sum(seg.values()) / 4)), (f(bal[7], True), f(sum(bal.values()) / 4, True))
SEG, BAL = _per10()
ESPERAT = {"Gols": ("2", "0,9"), "Eficàcia": (EF7, EFM), "Assistències": ("0,3", "0,1"), "Defensa": ("0", "0,2"), "Seguretat": SEG, "Balanç": BAL, "Disciplina": ("0", "0,2")}
async def main():
    async with async_playwright() as p:
        for nom, dev in (("mobil", p.devices["Pixel 7"]), ("tauleta", {"viewport": {"width": 1024, "height": 748}})):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(INIT)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            async def fitxa(d):
                await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(300)
                await pg.evaluate("""() => { const c = document.querySelector("#ov [data-act='close']"); if (c) c.click(); document.querySelector("#home [data-act='seasonrep']").click(); }"""); await pg.wait_for_timeout(400)
                await pg.evaluate("""() => [...document.querySelectorAll("#rep [data-act='rtab']")].find(x => x.getAttribute('data-v') === 'jugadors').click()"""); await pg.wait_for_timeout(250)
                ok = await pg.evaluate("""(d) => { const b = [...document.querySelectorAll("#rep table.rt [data-act][data-v='" + d + "']")][0]; if (b) b.click(); return b ? b.getAttribute('data-act') : null; }""", d)
                await pg.wait_for_timeout(300); return ok
            act = await fitxa(7)
            r = await pg.evaluate("""() => { const c = [...document.querySelectorAll('.repcard')].find(x => /Perfil del jugador/.test(x.textContent)); if (!c) return null;
              const rows = {}; [...c.querySelectorAll('table.rdtab tr')].slice(1).forEach(tr => { const t = [...tr.children]; rows[t[0].firstChild.textContent.trim()] = [t[1].textContent, t[2].textContent, t[1].className]; });
              return { rows, eixos: c.querySelectorAll('.rdl').length, poligons: c.querySelectorAll('.rdt, .rdp').length, nota: (c.querySelector('h3 small') || {}).textContent, ample: c.scrollWidth - c.clientWidth }; }""")
            if nom == "mobil":
                el = await pg.query_selector("xpath=//div[contains(@class,'repcard')][.//h3[contains(.,'Perfil del jugador')]]")
                if el: await el.screenshot(path="/tmp/radar_mobil.png")
            dif = [] if r else ["no hi ha radar"]
            for k, (v1, v2) in ESPERAT.items():
                g = (r or {}).get("rows", {}).get(k)
                if not g or g[0] != v1 or g[1] != v2: dif.append("%s: %s (esperat %s | %s)" % (k, g, v1, v2))
            classes = {k: v[2] for k, v in (r or {}).get("rows", {}).items()}
            await fitxa(1)
            gk = await pg.evaluate("""() => !![...document.querySelectorAll('.repcard')].find(x => /Perfil del jugador/.test(x.textContent))""")
            await fitxa(7)
            pr = await pg.evaluate("""() => { const b = [...document.querySelectorAll('#rep [data-act]')].find(x => /PDF de la fitxa/.test(x.textContent)); if (!b) return 'sense botó'; b.click(); return 'ok'; }"""); await pg.wait_for_timeout(500)
            prr = await pg.evaluate("""() => { const p = document.getElementById('print'); return p ? (p.querySelectorAll('.rdr').length + ' radar al PDF') : 'sense zona d impressió'; }""")
            print("%s · fitxa oberta amb «%s» · radar: %s eixos, %s formes, «%s», se surt %s px\n   xifres del 7: %s\n   colors (millor/pitjor que la mitjana): %s\n   porter amb radar: %s · PDF de la fitxa: %s, %s · errors: %s" % (
                nom, act, (r or {}).get("eixos"), (r or {}).get("poligons"), (r or {}).get("nota"), (r or {}).get("ample"), "totes correctes" if not dif else dif, classes, gk, pr, prr, errs or "cap"))
            await b.close()
asyncio.run(main())
