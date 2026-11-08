# Velocitat en un mòbil de gamma mitjana (processador 4 vegades més lent): obrir l'app, cada toc en un partit de 250 accions, informe i fitxa
import asyncio, json, random, sys, os
from playwright.async_api import async_playwright
FITX = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/peligrograma_directe.html"
random.seed(11)
DS = [1, 2, 3, 4, 6, 9, 12, 13, 15, 17, 21, 24, 28, 31, 32, 33]
ROSTER = [{"d": d, "n": "Jugador Número " + str(d), "gk": d in (1, 12)} for d in DS]
RIV = [[d, "Rival " + str(d)] for d in (3, 5, 7, 8, 10, 11, 14, 16, 18, 20, 22, 23, 25, 30)]
def acts(n):
    out = []
    for i in range(n):
        a = random.choice(["G", "G", "A", "F", "P", "PER", "BLQ", "2M", "G", "A", "TG"]); e = random.choice(["N", "N", "R"])
        d = random.choice(DS[1:]) if e == "N" else random.choice(RIV)[0]
        x = {"i": i + 1, "t": 13 * (i + 1), "p": 1 if i < n // 2 else 2, "e": e, "d": d, "a": a, "k": random.choice(["MP", "PS", "CM", "FA"]) if a == "PER" else None,
             "z": random.choice(["9C", "6C", "9D", "7M"]) if a in ("G", "A", "F", "P") else None, "g": random.randint(1, 9) if a in ("G", "A") else None, "s": None, "gk": 1, "rgk": 16}
        if a == "PER" and x["k"] in ("MP", "CM", "FA"): x["od"] = random.choice(RIV)[0] if e == "N" else random.choice(DS[1:])
        if a == "2M": x["od"] = random.choice(RIV)[0] if e == "N" else random.choice(DS[1:])
        if a == "P": x["rbe"] = random.choice(["N", "R"]); x["rbd"] = 4
        if x["z"] == "7M": x["pv"] = random.choice(DS[1:]) if e == "N" else 7
        out.append(x)
    return out
MS = []
for k in range(16):
    mid = "P%02d" % (k + 1); n = 250 if k == 15 else 150
    MS.append({"id": mid, "rival": "Rival " + mid, "date": "2026-%02d-%02d" % (9 + k // 10, 1 + (k % 10) * 3), "durada": 30, "part": 2, "clock": {"acc": 3600 if k < 15 else 1700, "start": None},
               "gk": 1, "rgk": 16, "rivals": RIV, "acts": acts(n), "seq": n, "squad": DS, "upd": 1, "det": "com"})
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": mm["id"] != "P16", "tr": 0} for mm in MS}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P16", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX}
INIT = "window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + \
    "".join("localStorage.setItem('peli-directe:m:" + mm["id"] + "', " + json.dumps(json.dumps(mm)) + "); " for mm in MS) + "}"
CLICK = "(s) => { const e = [...document.querySelectorAll(s)].find(x => x.getBoundingClientRect().width); if (!e) return -1; const t0 = performance.now(); e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return performance.now() - t0; }"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(**p.devices["Pixel 7"]); await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        await pg.goto("file://" + FITX); await pg.wait_for_timeout(500)   # primera càrrega: es desen les dades
        cdp = await ctx.new_cdp_session(pg); await cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        t0 = await pg.evaluate("() => performance.now()")
        await pg.reload(); await pg.wait_for_selector("#qui [data-act='player']", timeout=20000)
        obrir = await pg.evaluate("() => performance.now()")
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(200)
        ts = []
        for k in range(24):
            seq = [("#qui [data-act='player'][data-v='%d']" % DS[1 + k % 14]), "#que [data-act='action'][data-v='%s']" % ["G", "A", "F", "PER"][k % 4]]
            for sel in seq: ts.append(await pg.evaluate(CLICK, sel)); await pg.wait_for_timeout(30)
            for _ in range(5):
                st = await pg.evaluate("() => window.__peli.step()")
                if st == "zona": ts.append(await pg.evaluate(CLICK, "[data-act='zone'][data-v='9C']"))
                elif st == "porteria": ts.append(await pg.evaluate(CLICK, "[data-act='goal'][data-v='5']"))
                elif st == "tipus": ts.append(await pg.evaluate(CLICK, "[data-act='tipus'][data-v='MP']"))
                elif st == "opp": ts.append(await pg.evaluate(CLICK, "#on [data-act='opp'][data-v='']"))
                else: break
                await pg.wait_for_timeout(30)
        ts = [x for x in ts if x >= 0]; ts.sort()
        rep = await pg.evaluate(CLICK, "[data-act='report']"); await pg.wait_for_timeout(300)
        tabs = []
        for t in ("jugadors", "parcials", "rival", "compara"):
            tabs.append((t, round(await pg.evaluate("(v) => { const e = [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === v); if (!e) return -1; const t0 = performance.now(); e.click(); return performance.now() - t0; }", t))))
            await pg.wait_for_timeout(100)
        await pg.evaluate("(v) => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === v).click()", "jugadors"); await pg.wait_for_timeout(150)
        fx = await pg.evaluate(CLICK, "#rep table.rt [data-act='pfitxa']")
        print("Mòbil de gamma mitjana (processador ×4 més lent) · partit en curs de 250 accions · temporada de 16 partits")
        print("  obrir l'app: %d ms" % round(obrir))
        print("  cada toc: mitjana %d ms · el 90%% per sota de %d ms · el més lent %d ms (%d tocs)" % (round(sum(ts) / len(ts)), round(ts[int(len(ts) * 0.9)]), round(ts[-1]), len(ts)))
        print("  obrir l'informe: %d ms · pestanyes: %s · fitxa d'un jugador: %d ms" % (round(rep), ", ".join("%s %d ms" % x for x in tabs), round(fx)))
        print("  mida de l'app: %d kB · errors: %s" % (os.path.getsize(FITX) // 1024, errs or "cap"))
        await b.close()
asyncio.run(main())
