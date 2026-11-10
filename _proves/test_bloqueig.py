# Acció oberta: la pantalla queda bloquejada fins que es tanca (només la fase actual, rellotge, Enrere, Cancel·la i Desfés); el 7 m pregunta primer el provocat; sense «No ho sé» a la porteria ni al 7 m provocat
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 75, "n": "Porter Nostre", "gk": True}] + [{"d": d, "n": "Jugador " + str(d), "gk": False} for d in (2, 3, 4, 5, 6, 8, 9)]
VIS = "(s) => { const e = [...document.querySelectorAll(s)].find(x => { const r = x.getBoundingClientRect(); return r.width && r.height; }); if (!e) return false; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return true; }"
EST = "() => { const p = window.__peli.pending; return { st: p ? window.__peli.step() : 'fet', p: p ? [p.e, p.d, p.a, p.z || null] : null, n: window.__peli.m.acts.length, lock: document.body.classList.contains('locked'), toast: (document.getElementById('toast') || {}).textContent || '', nose: [...document.querySelectorAll('.panel.now button')].filter(b => b.getBoundingClientRect().width).map(b => b.textContent.trim()).filter(t => /No ho (sé|he vist)/.test(t)) }; }"
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-08", "durada": 30, "part": 1, "clock": {"acc": 300, "start": None}, "gk": 75, "rgk": 16, "rivals": [{"d": 6, "n": "Rival Sis"}, {"d": 9, "n": "Rival Nou"}, {"d": 16, "n": "Porter Rival", "gk": True}], "acts": [], "seq": 0, "squad": [75, 2, 3, 4, 5, 6, 8, 9], "upd": 1, "det": "com"}
        APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": 0, "upd": 1, "sc": [0, 0], "date": "2026-11-08"}}, "guideV": 1}
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800})
        await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); const M = " + json.dumps(M) + "; M.clock.start = Date.now() - 1000; localStorage.setItem('peli-directe:m:P01', JSON.stringify(M)); }")
        pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
        await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
        print("1) aturada del rival de 9 m, tocant el jugador següent amb la porteria oberta:")
        await pg.evaluate(VIS, "[data-act='rplayer'][data-v='6']"); await pg.evaluate(VIS, "#que [data-act='action'][data-v='A']"); await pg.wait_for_timeout(150)
        await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']"); await pg.wait_for_timeout(150)
        e0 = await pg.evaluate(EST)
        ok(e0["st"] == "porteria" and e0["lock"] and not e0["nose"], "fase porteria, pantalla bloquejada, sense «No ho he vist»: %s" % e0)
        await pg.evaluate("() => { const b = [...document.querySelectorAll(\"#qui [data-act='player'][data-v='3']\")][0]; b.click(); }"); await pg.wait_for_timeout(200)
        e1 = await pg.evaluate(EST)
        ok(e1["p"] == ["R", 6, "A", "9C"] and e1["n"] == 0 and "acaba" in e1["toast"], "el toc al nostre 3 no fa res: l'aturada continua oberta i correcta %s · «%s»" % (e1["p"], e1["toast"][:50]))
        run0 = await pg.evaluate("() => !!window.__peli.m.clock.start"); await pg.evaluate("() => document.querySelector(\"[data-act='clock']\").click()"); await pg.wait_for_timeout(150)
        run1 = await pg.evaluate("() => !!window.__peli.m.clock.start"); await pg.evaluate("() => document.querySelector(\"[data-act='clock']\").click()"); await pg.wait_for_timeout(150)
        ok(run0 != run1, "el rellotge funciona amb l'acció oberta (%s → %s)" % (run0, run1))
        await pg.wait_for_timeout(100); await pg.evaluate(VIS, ".panel.now [data-act='back']"); await pg.wait_for_timeout(150); eb = await pg.evaluate(EST)
        ok(eb["st"] == "zona", "«Enrere» torna a la fase anterior (%s)" % eb["st"])
        await pg.evaluate(VIS, "[data-act='zone'][data-v='9C']"); await pg.evaluate(VIS, "[data-act='goal'][data-v='5']"); await pg.wait_for_timeout(250)
        e2 = await pg.evaluate("() => [window.__peli.m.acts.map(a => [a.e, a.d, a.a, a.z, a.g]), document.body.classList.contains('locked')]")
        ok(e2[0] == [["R", 6, "A", "9C", 5]] and not e2[1], "en triar la porteria, es desa bé i es desbloqueja: %s" % e2[0])
        print("2) gol del rival de 7 m:")
        await pg.evaluate(VIS, "[data-act='rplayer'][data-v='6']"); await pg.evaluate(VIS, "#que [data-act='action'][data-v='G']"); await pg.wait_for_timeout(150)
        await pg.evaluate(VIS, "[data-act='zone'][data-v='7M']"); await pg.wait_for_timeout(150)
        f0 = await pg.evaluate(EST)
        ok(f0["st"] == "prov7" and not f0["nose"], "després de «7 m», primer «7 m provocat», sense «No ho sé»: %s" % f0["st"])
        await pg.evaluate("() => { const b = [...document.querySelectorAll('.panel.now button')].find(x => x.getBoundingClientRect().width && /^9/.test(x.textContent.trim())); b.click(); }"); await pg.wait_for_timeout(150)
        f1 = await pg.evaluate(EST)
        ok(f1["st"] == "porteria" and not f1["nose"], "després, la porteria, sense «No ho he vist»: %s" % f1["st"])
        await pg.evaluate(VIS, "[data-act='goal'][data-v='5']"); await pg.wait_for_timeout(250)
        f2 = await pg.evaluate("() => { const a = window.__peli.m.acts[window.__peli.m.acts.length - 1]; return [a.e, a.d, a.a, a.z, a.g, a.pv]; }")
        ok(f2 == ["R", 6, "G", "7M", 5, 9], "desat: %s (provocat pel 9, porteria 5)" % f2)
        print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
