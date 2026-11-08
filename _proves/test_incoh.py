# Detector d'incoherències: doble toc, dos gols en menys de 5 s, aturada amb la porteria buida, i cap avís en un partit normal
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": d, "n": "J" + str(d), "gk": d == 1} for d in (1, 2, 3, 5, 6, 7, 9)]
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {}, "guideV": 1, "det": "ess"}
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
BAR = """() => { const b = document.getElementById('alertbar'); if (!b || b.hidden || !b.classList.contains('chk')) return null; const r = b.getBoundingClientRect();
  return { text: b.textContent.trim().slice(0, 110), dins: r.top >= 0 && r.bottom <= innerHeight + 0.5 && r.left >= -0.5 && r.right <= innerWidth + 0.5,
    botons: [...b.querySelectorAll('button')].map(x => Math.round(x.getBoundingClientRect().height)) }; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, dev in (("mòbil", p.devices["Pixel 7"]), ("tauleta", {"viewport": {"width": 1280, "height": 800}})):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); document.querySelector(\"#home [data-act='partits']\").click(); }"); await pg.wait_for_timeout(100)
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='pnew']\").click()"); await pg.wait_for_timeout(150)
            await pg.evaluate("() => { const s = document.getElementById('nfix'); if (s) { s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); } const e = document.getElementById('nriv'); if (e) { e.value = 'CH Prova'; e.dispatchEvent(new Event('input', { bubbles: true })); } }")
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='ndet'][data-v='ess']\").click()")
            await pg.evaluate("() => { document.querySelector(\"[data-act='sqall']\").click(); document.querySelector(\"[data-act='nstart']\").click(); }"); await pg.wait_for_timeout(200)
            await pg.evaluate("() => { const ok = document.querySelector(\"#nwarn [data-act='nstartok']\"); if (ok) ok.click(); }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            tap = lambda s: pg.evaluate(VIS, s)
            n = lambda: pg.evaluate("() => window.__peli.m.acts.length")
            async def ap(eq, d, a):
                if eq == "N": await tap("#qui [data-act='player'][data-v='" + str(d) + "']")
                else:
                    if nom == "mòbil":
                        await tap("#qui [data-act='rival']")
                        for ch in str(d): await tap("[data-act='digit'][data-v='" + ch + "']")
                        await tap("[data-act='padok']")
                    elif not await tap("[data-act='rplayer'][data-v='" + str(d) + "']"): await tap("[data-act='rnone']")
                await tap("#que [data-act='action'][data-v='" + a + "']"); await pg.wait_for_timeout(120)
                # per si queda alguna pregunta (qui l'ha provocat, etc.), «No ho sé» o «Salta»
                for k in range(3):
                    if not await pg.evaluate("() => !!window.__peli.pending"): break
                    await pg.evaluate("() => { const b = [...document.querySelectorAll('button')].find(x => x.getBoundingClientRect().width && /^(No ho sé|Salta|Sense assistència)$/.test(x.textContent.trim())); if (b) b.click(); }"); await pg.wait_for_timeout(100)
            async def net():
                return await pg.evaluate("() => !window.__peli.pending")
            def ok(cond, txt):
                nonlocal_mal[0] += 0 if cond else 1
                print("   %s %s" % ("✓" if cond else "✗", txt))
            nonlocal_mal = [0]
            print(nom + ":")
            # 1) doble toc
            n0 = await n(); await ap("N", 7, "G"); await ap("N", 7, "G"); r = await pg.evaluate(BAR)
            ok(r and "dues vegades" in r["text"] and r["dins"] and min(r["botons"]) >= 44, "doble toc: %s" % (r,))
            await tap("#alertbar [data-act='chkundo']"); await pg.wait_for_timeout(150)
            ok(await n() == n0 + 1 and await pg.evaluate(BAR) is None, "«Desfés» treu la repetida: %d accions" % (await n() - n0))
            # 2) dos gols seguits del mateix equip, rellotge en marxa
            await pg.evaluate("() => { window.__peli.m.clock.acc = 600; }"); await tap("[data-act='clock']"); await pg.wait_for_timeout(300)
            await ap("N", 9, "G"); await pg.wait_for_timeout(900); await ap("N", 5, "G"); r = await pg.evaluate(BAR)
            ok(r and "5 segons" in r["text"], "dos gols en 1 s: %s" % ((r or {}).get("text"),))
            n1 = await n(); await tap("#alertbar [data-act='chkok']"); await pg.wait_for_timeout(150)
            ok(await n() == n1 and await pg.evaluate(BAR) is None, "«És correcte» els manté: %d accions" % (await n() - n0))
            # 3) aturada amb la porteria buida
            await pg.evaluate("() => { window.__peli.m.gk = 0; }"); await pg.wait_for_timeout(50)
            await ap("R", 4, "A"); r = await pg.evaluate(BAR)
            ok(r and "porteria buida" in r["text"], "aturada amb la porteria buida: %s" % ((r or {}).get("text"),))
            await tap("#alertbar [data-act='chkok']"); await pg.evaluate("() => { window.__peli.m.gk = 1; }")
            # 4) partit normal: cap avís (rival, aturada amb porter, rebot del mateix jugador, pèrdua i recuperació, gol 7 s després)
            await pg.wait_for_timeout(5200)
            avisos = []
            for eq, d, a, w in (("R", 4, "G", 400), ("R", 4, "A", 400), ("N", 7, "A", 300), ("N", 7, "A", 300), ("N", 3, "PER", 300), ("N", 3, "REC", 300), ("N", 2, "F", 300), ("R", 11, "PER", 300), ("N", 6, "G", 7200), ("N", 7, "G", 300)):
                await ap(eq, d, a); await pg.wait_for_timeout(w)
                r = await pg.evaluate(BAR)
                if r: avisos.append(eq + str(d) + a + ": " + r["text"][:60]); await tap("#alertbar [data-act='chkok']")
            nn = await n()
            ok(not avisos and await net(), "partit normal (10 accions, rebot i pèrdua + recuperació): avisos %s · cap acció a mitges: %s" % (avisos or "cap", await net()))
            # 5) se'n va sol i l'acció es queda
            await ap("N", 2, "F"); await ap("N", 2, "F"); r = await pg.evaluate(BAR); n2 = await n()
            await pg.wait_for_timeout(12400)
            ok(r is not None and await pg.evaluate(BAR) is None and await n() == n2, "sense tocar res, l'avís se'n va al cap de 12 s i l'acció es queda")
            if nom == "mòbil":
                await ap("N", 5, "PER"); await ap("N", 5, "PER"); await pg.wait_for_timeout(150); await pg.screenshot(path="/tmp/incoh_mobil.png")
            print("   errors: %s" % (errs or "cap")); mal += nonlocal_mal[0] + (1 if errs else 0)
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
