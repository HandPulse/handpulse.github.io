# Hora real de cada acció, els quatre factors i les últimes 5 possessions al resum ràpid, i alertes per probabilitat
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys, math, time
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 7, 8, 9)]
def A(i, e, d, a, t, **kw):
    x = {"i": i, "t": t, "p": 1, "e": e, "d": d, "a": a, "k": None, "z": "9C" if a in ("G", "A", "F", "P") else None, "g": None, "s": None, "gk": 1, "rgk": 16}; x.update(kw); return x
def match(mid, date, plays, cur=False, det="ess", acc=3600):
    acts = [A(i + 1, e, d, a, 10 * (i + 1), **kw) for i, (e, d, a, kw) in enumerate(plays)]
    return {"id": mid, "rival": "Rival " + mid, "date": date, "durada": 30, "part": 1 if cur else 2, "clock": {"acc": acc, "start": None}, "gk": 1, "rgk": None, "rivals": [],
            "acts": acts, "seq": len(acts), "squad": [1, 2, 3, 4, 5, 6, 7, 8, 9], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1, "det": det}
# partits anteriors: equip que perd moltes pilotes (13 pèrdues i 24 llançaments per partit)
PREV = [("N", 2 + k % 7, "PER", {"k": "MP"}) for k in range(13)] + [("N", 2 + k % 7, "G" if k % 2 else "F", {}) for k in range(24)] + [("R", 4, "G", {}) for k in range(10)] + [("R", 4, "A", {}) for k in range(8)]
r = 13 / 37; n = 37; KPER = next(k for k in range(3, 9) if n * (1 - r) * r ** k <= 1)
def app_with(ms, cur):
    idx = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": mm["id"] != cur, "tr": 0} for mm in ms}
    return {"v": 1, "team": "UE Sarrià", "durada": 30, "current": cur, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": idx, "guideV": 1}
def init(ms, cur, running=False):
    j = "window.__hpTest = true; window.open = (u) => { window.__wa = decodeURIComponent(String(u)); return null; }; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app_with(ms, cur))) + "); "
    for mm in ms:
        j += "{ const M = " + json.dumps(mm) + "; " + ("M.clock.start = Date.now() - 1000; " if running and mm["id"] == cur else "") + "localStorage.setItem('peli-directe:m:" + mm["id"] + "', JSON.stringify(M)); } "
    return j + "}"
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
BAR = "() => { const b = document.getElementById('alertbar'); return b && !b.hidden ? b.textContent.trim().replace(/\\s+/g, ' ').slice(0, 120) : ''; }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        # ---- C) alertes de pèrdues, amb i sense partits anteriors (i A: l'hora real de les accions apuntades)
        for nom, ms, esperat in (("amb 2 partits anteriors", [match("P01", "2026-10-03", PREV), match("P02", "2026-10-10", PREV)], KPER), ("sense partits anteriors", [], 3)):
            cur = match("P03", "2026-10-17", [("N", 2, "G", {}), ("R", 4, "G", {})], cur=True, acc=30)   # un gol fa poc: cap avís de «minuts sense marcar»
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800}); await ctx.add_init_script(init(ms + [cur], "P03", running=True))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(700)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print("C) alertes, " + nom + " (esperat: a la pèrdua %d):" % esperat)
            t0 = time.time() * 1000; quan = None
            for k, d in enumerate((3, 5, 7, 9, 2, 4), start=1):
                await pg.evaluate(VIS, "#qui [data-act='player'][data-v='" + str(d) + "']"); await pg.evaluate(VIS, "#que [data-act='action'][data-v='PER']"); await pg.wait_for_timeout(120)
                for q in range(3):
                    if not await pg.evaluate("() => !!window.__peli.pending"): break
                    await pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find(x => x.getBoundingClientRect().width && /^(No ho sé|Salta|Mal passe)$/.test(x.textContent.trim())); if (b) b.click(); }"); await pg.wait_for_timeout(100)
                await pg.wait_for_timeout(500)
                bar = await pg.evaluate(BAR)
                if "pèrdues seguides" in bar and quan is None: quan = (k, bar)
            ok(quan and quan[0] == esperat and (("Poc habitual" in quan[1]) == (esperat != 3 or nom.startswith("amb"))), "l'avís salta a la pèrdua %s: «%s»" % (quan[0] if quan else "cap", quan[1] if quan else ""))
            if nom.startswith("amb"):
                ws = await pg.evaluate("() => window.__peli.m.acts.filter(a => a.a === 'PER').map(a => a.w || 0)")
                ok(len(ws) == 6 and all(w >= t0 - 1000 for w in ws) and ws == sorted(ws), "A) les 6 pèrdues porten l'hora real, en ordre (%s)" % ("sí" if ws and all(ws) else ws))
                vells = await pg.evaluate("() => window.__peli.m.acts.filter(a => a.i <= 2).map(a => a.w)")
                ok(all(v is None for v in vells), "A) les accions d'abans no en porten (no s'inventa cap hora)")
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        # ---- B) resum ràpid: quatre factors i últimes 5 possessions, amb xifres conegudes
        N = [("N", 2, "G", {"ty": "CD"}), ("N", 3, "G", {}), ("N", 4, "G", {}), ("N", 5, "G", {}), ("N", 6, "F", {}), ("N", 7, "F", {}), ("N", 8, "F", {}), ("N", 9, "F", {}),
             ("N", 2, "A", {}), ("N", 3, "A", {}), ("N", 4, "PER", {"k": "MP"}), ("N", 5, "PER", {"k": "MP"}), ("N", 6, "PER", {"k": "MP"}), ("N", 7, "PER", {"k": "PS"})]
        R = [("R", 4, "G", {"ty": "CD"}), ("R", 4, "G", {"ty": "CD"}), ("R", 8, "G", {"ty": "CD"}), ("R", 8, "G", {}), ("R", 10, "G", {}), ("R", 10, "G", {}),
             ("R", 11, "A", {}), ("R", 11, "A", {}), ("R", 12, "A", {}), ("R", 12, "F", {}), ("R", 4, "F", {}), ("R", 8, "PER", {"k": "PS"})]
        seq = []
        for k in range(max(len(N), len(R))):
            if k < len(N): seq.append(N[k])
            if k < len(R): seq.append(R[k])
        cur = match("P04", "2026-10-24", seq, cur=True, acc=1200)
        l5 = [x for x in seq if x[0] == "N" and x[2] in ("G", "A", "F", "P", "B", "PER")][-5:]
        ACTL = {"G": "Gol", "A": "Aturada", "F": "Fora", "PER": "Pèrdua"}; TL = {"MP": "Mal passe", "PS": "Passos"}
        esp5 = " · ".join("%d %s%s" % (x[1], ACTL[x[2]], " (%s)" % TL[x[3]["k"]] if x[2] == "PER" else "") for x in l5)
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(init([cur], "P04", running=True))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); const h = document.querySelector(\"#home [data-act='partits']\"); }")
            await pg.evaluate("() => { const b = document.querySelector(\"[data-act='brief']\"); if (b) b.click(); else { const m = document.querySelector(\"[data-act='menu']\"); if (m) m.click(); } }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { if (!document.querySelector('.brief')) { const b = document.querySelector(\"[data-act='brief']\"); if (b) b.click(); } }"); await pg.wait_for_timeout(400)
            r = await pg.evaluate("""() => { const c = document.querySelector('.brief .bff'); if (!c) return null;
              return { files: [...c.querySelectorAll('.fft tr')].slice(1).map(tr => [...tr.children].map(td => td.textContent.trim() + (td.className && td.className !== 'l' ? ':' + td.className : '')).join(' | ')),
                consells: [...c.querySelectorAll('.badv li')].map(x => x.textContent), ult: [...document.querySelectorAll('.brief p.l5')].map(q => q.querySelector('b').textContent + ' ' + [...q.querySelectorAll('.chip')].map(c => c.textContent).join(' · ')) }; }""")
            print("B) resum ràpid (%s):" % nom)
            ok(r and r["files"] == ["Llançament | 40%:neg | 55%", "Pèrdues | 29%:neg | 8%", "Porteria | 33% | 33%", "Contraatac | 1:neg | 3"], "quatre factors: %s" % (r or {}).get("files"))
            ok(r and r["consells"] == ["Llançament: busqueu llançaments més clars.", "Pèrdues: cuideu la pilota (Mal passe).", "Contraatac: torneu ràpid a defensar."], "consells: %s" % (r or {}).get("consells"))
            ok(r and r["ult"] and r["ult"][0] == "Nosaltres: " + esp5, "últimes 5 possessions: %s" % ((r or {}).get("ult") or ["?"])[0])
            if nom == "mòbil" and await pg.query_selector(".brief"): await (await pg.query_selector(".brief")).screenshot(path="/tmp/brief_mobil.png")
            await pg.evaluate("() => { const b = document.querySelector(\"[data-act='briefwa']\"); if (b) b.click(); }"); await pg.wait_for_timeout(300)
            wa = await pg.evaluate("() => window.__wa || ''")
            ok("Els quatre factors (partit fins ara): Llançament 40% / 55%" in wa and "Últimes 5 possessions" in wa, "text de WhatsApp amb els dos apartats: %s" % ("sí" if wa else "no s'ha obert"))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
