# Jugades amb estrella per a la xerrada (botó ★, «Totes», informe i PDF) i mapes dels llançadors rivals al PDF de la fitxa del rival
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 7, 8, 9)]
RD = [4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 17]   # 12 llançadors rivals diferents
def A(i, e, d, a, t, **kw):
    x = {"i": i, "t": t, "p": 1, "e": e, "d": d, "a": a, "k": None, "z": "9C" if a in ("G", "A", "F", "P") else None, "g": 5 if a in ("G", "A") else None, "s": None, "gk": 1, "rgk": 16}; x.update(kw); return x
def match(mid, date, plays, cur=False):
    acts = [A(i + 1, e, d, a, 20 * (i + 1), **kw) for i, (e, d, a, kw) in enumerate(plays)]
    return {"id": mid, "rival": "CH Prova", "date": date, "durada": 30, "part": 1 if cur else 2, "clock": {"acc": 900 if cur else 3600, "start": None}, "gk": 1, "rgk": None,
            "rivals": [{"d": d, "n": "Rival " + str(d)} for d in RD], "acts": acts, "seq": len(acts), "squad": [1, 2, 3, 4, 5, 6, 7, 8, 9], "comp": "Lliga", "jor": "", "lloc": "", "upd": 1, "det": "ess"}
PREV = [("R", d, "G", {"z": "9E"}) for d in RD] + [("R", d, "A", {"z": "6C"}) for d in RD] + [("N", 3, "G", {}), ("N", 5, "F", {})]
MS = [match("P01", "2026-10-03", PREV), match("P02", "2026-10-10", PREV), match("P03", "2026-10-24", [("N", 2, "G", {}), ("R", 4, "G", {}), ("N", 7, "PER", {"k": "MP"})], cur=True)]
IDX = {mm["id"]: {"rival": mm["rival"], "n": len(mm["acts"]), "upd": 1, "sc": [0, 0], "date": mm["date"], "comp": "Lliga", "jor": "", "lloc": "", "done": mm["id"] != "P03", "tr": 0} for mm in MS}
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P03", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": IDX, "guideV": 1}
INIT = "window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); " + \
       "".join("{ const M = " + json.dumps(mm) + "; " + ("M.clock.start = Date.now() - 1000; " if mm["id"] == "P03" else "") + "localStorage.setItem('peli-directe:m:" + mm["id"] + "', JSON.stringify(M)); } " for mm in MS) + "}"
PRINT = "() => { window.print = () => {}; const b = document.querySelector(\"#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']\"); if (b) b.click(); return !!b; }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(INIT)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(700)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            print(nom + ":")
            # A) el botó ★ de la barra de baix
            fb = await pg.evaluate("() => { const b = document.querySelector(\"#foot [data-act='starlast']\"); if (!b) return null; const r = b.getBoundingClientRect(); const c = document.querySelector('#foot [data-act=fixlast]').getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), hc: Math.round(c.height) }; }")
            await pg.evaluate("() => document.querySelector(\"#foot [data-act='starlast']\").click()"); await pg.wait_for_timeout(250)
            s1 = await pg.evaluate("() => [window.__peli.m.acts.filter(a => a.star).map(a => a.i), document.querySelector(\"#foot [data-act='starlast']\").classList.contains('on'), (document.getElementById('toast') || {}).textContent || '']")
            ok(fb and fb["w"] >= 40 and fb["h"] >= fb["hc"] and s1[0] == [3] and s1[1] and "destacada" in s1[2], "★ a la barra (%s px): destaca l'última acció %s · «%s»" % (fb, s1[0], s1[2][:60]))
            await pg.evaluate("() => document.querySelector(\"#foot [data-act='starlast']\").click()"); await pg.wait_for_timeout(250)
            s2 = await pg.evaluate("() => window.__peli.m.acts.filter(a => a.star).map(a => a.i)")
            ok(s2 == [], "un segon toc la desmarca")
            # «Totes les accions»: l'estrella de la primera fila (acció 1) i, després, l'última amb el botó
            await pg.evaluate("() => document.querySelector(\"#foot [data-act='all']\").click()"); await pg.wait_for_timeout(250)
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='star'][data-v='1']\").click()"); await pg.wait_for_timeout(250)
            s3 = await pg.evaluate("() => [window.__peli.m.acts.filter(a => a.star).map(a => a.i), document.querySelector(\"#ov [data-act='star'][data-v='1']\").textContent]")
            ok(s3[0] == [1] and s3[1] == "★", "a «Totes», l'estrella de la fila marca l'acció 1 (%s)" % s3)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); document.querySelector(\"#foot [data-act='starlast']\").click(); }"); await pg.wait_for_timeout(250)
            # informe i PDF
            await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(500)
            st = await pg.evaluate("() => { const c = document.querySelector('#rep .repcard.stars'); return c ? { vis: c.checkVisibility(), li: [...c.querySelectorAll('li')].map(x => x.textContent.trim()) } : null; }")
            ok(st and st["vis"] and len(st["li"]) == 2, "a l'informe, «Jugades per a la xerrada»: %s" % (st or {}).get("li"))
            await pg.evaluate(PRINT); await pg.wait_for_timeout(800)
            pdf = await pg.evaluate("() => [...document.querySelectorAll('#print section.pp')].some(x => x.innerHTML.includes('starl'))")
            ok(pdf, "les jugades amb estrella surten al PDF de l'informe")
            if nom == "mòbil": await pg.screenshot(path="/tmp/estrelles_mobil.png")
            # B) la fitxa del rival en PDF: els mapes de cada llançador, en pàgines amb capçalera i logo
            await pg.evaluate("() => { const ov = document.getElementById('rep'); const c = document.querySelector(\"#rep [data-act='rclose'], #rep [data-act='close']\"); if (c) c.click(); }"); await pg.wait_for_timeout(200)
            await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === 'RIV:CH Prova')); s.value = 'RIV:CH Prova'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(600)
            pant = await pg.evaluate("() => document.querySelectorAll('#rep .pmgrid .repcard.pmap').length")
            await pg.evaluate(PRINT); await pg.wait_for_timeout(800)
            fx = await pg.evaluate("""() => [...document.querySelectorAll('#print section.pp')].map(sec => ({ t: (sec.querySelector('.ptitle') || {}).textContent || '', logo: !!sec.querySelector('.plogo'), mapes: sec.querySelectorAll('.repcard.pmap').length }))""")
            mp = [x for x in fx if x["t"].startswith("On xuta cada jugador del rival")]
            ok(pant == 13 and len(mp) == 2 and all(x["logo"] for x in fx) and [x["mapes"] for x in mp] == [10, 3], "fitxa del rival: %d mapes a la pantalla · PDF: %s" % (pant, [(x["t"][:40], x["mapes"], "logo" if x["logo"] else "SENSE LOGO") for x in fx]))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
