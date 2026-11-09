# Probabilitat de guanyar (corba, moments clau, en directe al resum ràpid) i ritme del partit, comparats amb un càlcul independent
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys, math
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 7, 8, 9)]
NG = [90, 330, 570, 810, 1050, 1290, 1530, 1770, 2010, 2250, 3150, 3270, 3390, 3510]
RG = [120, 360, 600, 840, 1080, 1320, 1560, 1800, 2040, 2280, 2700, 2940]
def acts_until(tmax):
    out = []
    for k, t in enumerate(range(30, min(3600, tmax + 1), 30)):
        e = "N" if t % 60 == 30 else "R"; a = "G" if (t in NG if e == "N" else t in RG) else "F"
        out.append({"i": k + 1, "t": t, "p": 1 if t < 1800 else 2, "e": e, "d": 2 + k % 7 if e == "N" else 4, "a": a, "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": 16})
    return out
def match(mid, acts, part, acc, cur):
    return {"id": mid, "rival": "CH Prova", "date": "2026-10-24", "durada": 30, "part": part, "clock": {"acc": acc, "start": None}, "gk": 1, "rgk": None, "rivals": [],
            "acts": acts, "seq": len(acts), "squad": [1, 2, 3, 4, 5, 6, 7, 8, 9], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1, "det": "ess"}
# ---- el model, calculat aquí pel seu compte (sense partits anteriors: 0,45 gols per minut cada equip)
def poisP(l, K):
    q = [math.exp(-l)]
    for k in range(1, K + 1): q.append(q[-1] * l / k)
    return q
def winp(diff, eN, eR):
    K = math.ceil(max(eN, eR) * 2 + 15); pn, pr = poisP(eN, K), poisP(eR, K); w = d = 0
    for x in range(K + 1):
        for y in range(K + 1):
            q = pn[x] * pr[y]; f = diff + x - y
            if f > 0: w += q
            elif f == 0: d += q
    return w, d
def at(t, gs, T=3600, M=20, r=0.45):
    gn = sum(1 for e in gs if e == "N"); gr = len(gs) - gn; tm = min(t, T) / 60; rem = max(0, T - t) / 60
    return winp(gn - gr, (gn + r * M) / (tm + M) * rem, (gr + r * M) / (tm + M) * rem)
rd = lambda x: math.floor(x + 0.5)
goals = sorted([(t, "N") for t in NG] + [(t, "R") for t in RG])
keys = []
for k, (t, e) in enumerate(goals):
    d0 = at(t, [g[1] for g in goals[:k]])[0]; d1 = at(t, [g[1] for g in goals[:k + 1]])[0]
    sc = (sum(1 for g in goals[:k + 1] if g[1] == "N"), sum(1 for g in goals[:k + 1] if g[1] == "R")); keys.append((t, d1 - d0, sc, e))
top = sorted(sorted(keys, key=lambda x: -abs(x[1]))[:3], key=lambda x: x[0])
ESPK = ["%d′ %d–%d %s%d%%" % (t // 60, sc[0], sc[1], "+" if d >= 0 else "−", rd(abs(100 * d))) for t, d, sc, e in top]
# ritme: trams de possessió per parts (llançaments i pèrdues), fusionant els seguits del mateix equip
def ritme(acts):
    st = {"N": [0, 0], "R": [0, 0]}
    for p in (1, 2):
        t0 = (p - 1) * 1800; last = None; segs = []
        for a in sorted([a for a in acts if t0 <= a["t"] < (p * 1800 if p == 1 else 1e9)], key=lambda a: (a["t"], a["i"])):
            a0 = last["t"] if last else t0
            if last and last["e"] == a["e"] and segs and segs[-1][0] == a["e"]: segs[-1][2] = a["t"]
            else: segs.append([a["e"], a0, a["t"]])
            last = a
        for e, x, y in segs: st[e][0] += 1; st[e][1] += y - x
    return st
ACTS = acts_until(3600); RIT = ritme(ACTS)
ESPR = "%d possessions, %d s de mitjana" % (RIT["N"][0], rd(RIT["N"][1] / RIT["N"][0]))
# en directe: partit en curs al minut 20 (1200 s)
LIVE = acts_until(1200); wL, dL = at(1200, [a["e"] for a in sorted(LIVE, key=lambda a: a["t"]) if a["a"] == "G"])
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            ms = [match("P05", ACTS, 2, 3600, False), match("P06", LIVE, 1, 1200, True)]
            ms[0]["date"] = "2026-10-17"
            idx = {mm["id"]: {"rival": "CH Prova", "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": mm["id"] == "P05", "tr": 0} for mm in ms}
            app = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P06", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": idx, "guideV": 1}
            init = "window.__hpTest = true; window.print = () => {}; window.open = (u) => { window.__wa = decodeURIComponent(String(u)); return null; }; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app)) + "); " + \
                   "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in ms) + "}"
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(init)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print(nom + ":")
            # informe del P05: pestanya «Parcials»
            await pg.evaluate("() => document.querySelector(\"#home [data-act='seasonrep']\").click()"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === 'P05')); s.value = 'P05'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'parcials').click()"); await pg.wait_for_timeout(400)
            r = await pg.evaluate("""() => { const c = document.querySelector('#rep .wpcard'), h = document.querySelector('#rep .rhcard'); if (!c || !h) return null;
              const pts = c.querySelector('polyline').getAttribute('points').trim().split(' ').map(q => q.split(',').map(Number));
              return { k: [...c.querySelectorAll('ul.wpk li')].map(x => x.textContent.replace(/\\s+/g, ' ').replace(/ · [^·]*? (?=[+−])/, ' ')), primer: pts[0][1], ultim: pts[pts.length - 1][1], ara: !!c.querySelector('p.note'),
                rit: h.querySelector('p.note').textContent, surt: Math.max(document.querySelector('#rep .repbody').scrollWidth - document.querySelector('#rep .repbody').clientWidth, 0) }; }""")
            if r:
                kk = [x.replace(" ", "", 0) for x in r["k"]]
            ok(r and [x.split(" ")[0] + " " + x.split(" ")[1] + " " + x.split(" ")[-1] for x in r["k"]] == ESPK, "moments clau: %s (esperat %s)" % ((r or {}).get("k"), ESPK))
            ok(r and abs(r["ultim"] - 6) < 1 and not r["ara"], "partit acabat: la corba acaba al 100 %% (%s) i no surt «Ara»" % ((r or {}).get("ultim"),))
            ok(r and ESPR in r["rit"] and r["surt"] == 0, "ritme: «%s» (esperat «%s») · se surt %s px" % ((r or {}).get("rit", "")[:80], ESPR, (r or {}).get("surt")))
            if nom == "mòbil":
                await (await pg.query_selector("#rep .wpcard")).screenshot(path="/tmp/wp_card.png"); await (await pg.query_selector("#rep .rhcard")).screenshot(path="/tmp/rh_card.png")
            # PDF: una pàgina pròpia amb logo
            await pg.evaluate("() => { const b = document.querySelector(\"#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']\"); if (b) b.click(); }"); await pg.wait_for_timeout(800)
            pdf = await pg.evaluate("() => [...document.querySelectorAll('#print section.pp')].filter(x => /Probabilitat de guanyar i ritme/.test((x.querySelector('.ptitle') || {}).textContent || '')).map(x => [!!x.querySelector('.plogo'), !!x.querySelector('.wpcard'), !!x.querySelector('.rhcard')])")
            ok(pdf == [[True, True, True]], "al PDF, una pàgina pròpia amb logo, la corba i el ritme: %s" % pdf)
            # en directe: el resum ràpid del partit en curs (minut 20)
            await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose'], #rep [data-act='close']\"); if (c) c.click(); const h = document.querySelector(\"#home [data-act='partits']\"); if (h) h.click(); }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const g = document.querySelector(\"#ov [data-act='gomatch']\"); if (g) g.click(); const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const b = document.querySelector(\"[data-act='brief']\"); if (b) b.click(); else { const m = document.querySelector(\"[data-act='menu']\"); if (m) m.click(); } }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { if (!document.querySelector('.brief')) { const b = document.querySelector(\"[data-act='brief']\"); if (b) b.click(); } }"); await pg.wait_for_timeout(400)
            bw = await pg.evaluate("() => (document.querySelector('.brief p.bwp') || {}).textContent || ''")
            esp = "%d%% · empat %d%%" % (rd(100 * wL), rd(100 * dL))
            ok(esp in bw, "en directe, al resum ràpid: «%s» (esperat «%s»)" % (bw, esp))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
