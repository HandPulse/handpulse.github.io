# Guia d'inici: surt sola només el primer dia, 7 passos, navegació (botons, teclat, lliscar), es torna a obrir des d'Eines,
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
# tots els botons que esmenta existeixen, 4 idiomes sense textos sense traduir, i res no se surt de la pantalla
import asyncio, json, sys, re
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/peligrograma_directe.html"
ROSTER = [{"d": d, "n": "J" + str(d), "gk": d == 1} for d in (1, 2, 3)]
G = "() => { const g = document.querySelector('#ov .guide'); if (!g) return null; return { n: g.querySelector('.gcount').textContent, t: g.querySelector('.gti').textContent, btn: [...g.querySelectorAll('.gnav .btn')].map(b => b.textContent.trim()).join(' | '), flags: !!g.querySelector('.lsel .langbtn'), svg: !!g.querySelector('.gart svg') }; }"
CATW = r"\b(amb|els|aquest|aquesta|què|partit|partits|jugadors|llançaments?|Desa|Toca|Tanca|també|només|encara|perquè|Esborra|assistència|porteria|aturades?|rellotge|guia|pilota|toca)\b"
async def ctx_for(p, app, dev=None):
    b = await p.chromium.launch(); ctx = await b.new_context(**(dev or {"viewport": {"width": 412, "height": 915}, "has_touch": True}))
    init = "window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); " + ("localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(app)) + "); " if app else "") + "}"
    await ctx.add_init_script(init)
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(350)
    return b, pg, errs
async def main():
    s = open(FITX, encoding="utf-8").read(); D = json.loads(re.search(r"^  var DICT = (\{.*\});$", s, re.M).group(1))
    code = s.replace(re.search(r"^  var DICT = .*$", s, re.M).group(0), "")
    async with async_playwright() as p:
        # 1) usuari nou: la guia surt sola, 7 passos, i en acabar porta a la benvinguda; després de recarregar, ja no surt
        b, pg, errs = await ctx_for(p, None)
        r = [await pg.evaluate(G)]; print("Usuari nou · en obrir l'app: " + (("guia " + r[0]["n"] + " «" + r[0]["t"] + "» · botó d'idioma: " + str(r[0]["flags"])) if r[0] else "NO SURT LA GUIA"))
        for k in range(6):
            await pg.evaluate("() => document.querySelector(\"#ov .guide [data-act='gnext']\").click()"); r.append(await pg.evaluate(G))
        print("   passos: " + " · ".join(x["n"] + " " + x["t"] + (" (dibuix)" if x["svg"] else " (SENSE DIBUIX)") for x in r))
        print("   botons de l'últim pas: " + r[-1]["btn"])
        await pg.evaluate("() => document.querySelector(\"#ov .guide [data-act='gend']\").click()"); await pg.wait_for_timeout(150)
        wl = await pg.evaluate("() => (document.querySelector('#ov h2') || {}).textContent || 'res'")
        vist = await pg.evaluate("() => JSON.parse(localStorage.getItem('peli-directe:app') || '{}').guideV")
        await pg.reload(); await pg.wait_for_timeout(350)
        des = await pg.evaluate("() => document.querySelector('#ov .guide') ? 'TORNA A SORTIR' : ((document.querySelector('#ov h2') || {}).textContent || 'cap finestra')")
        print("   en acabar: «" + wl + "» · queda vista (guideV=" + str(vist) + ") · després de recarregar: «" + des + "» · errors: " + str(errs or "cap"))
        await (await pg.query_selector("#ov .sheet")).screenshot(path="/tmp/guia_benv.png")
        await b.close()
        # 2) usuari actual: no surt sola; Eines › Guia d'inici; teclat i lliscar el dit; l'últim botó és «Tanca»
        APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {}}
        b, pg, errs = await ctx_for(p, APP)
        sola = await pg.evaluate("() => !!document.querySelector('#ov .guide')")
        await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
        await pg.evaluate("() => document.querySelector(\"#home [data-act='guide']\").click()"); await pg.wait_for_timeout(120)
        a = await pg.evaluate(G)
        await pg.keyboard.press("ArrowRight"); k1 = (await pg.evaluate(G))["n"]
        await pg.evaluate("""() => { const mk = (t, x) => new TouchEvent(t, { bubbles: true, touches: t === 'touchstart' ? [new Touch({ identifier: 1, target: document.body, clientX: x, clientY: 400 })] : [], changedTouches: [new Touch({ identifier: 1, target: document.body, clientX: x, clientY: 400 })] });
          document.body.dispatchEvent(mk('touchstart', 320)); document.body.dispatchEvent(mk('touchend', 80)); }"""); k2 = (await pg.evaluate(G))["n"]
        await pg.evaluate("() => document.querySelector(\"#ov .guide [data-act='gdot'][data-v='6']\").click()"); u = await pg.evaluate(G)
        await pg.evaluate("() => document.querySelector(\"#ov .guide [data-act='gend']\").click()"); tanc = await pg.evaluate("() => document.getElementById('ov').hidden")
        print("Usuari actual · surt sola: " + str(sola) + " · Eines › Guia d'inici: " + a["n"] + " · fletxa →: " + k1 + " · lliscar el dit: " + k2 + " · punt 7: " + u["n"] + " (" + u["btn"] + ") · es tanca: " + str(tanc) + " · errors: " + str(errs or "cap"))
        # 3) els botons que esmenta la guia existeixen a l'app (i estan traduïts)
        refs = await pg.evaluate("() => window.__peli.guideRefs()")
        mal = []
        for ref in refs:
            hi_es = ('"' + ref + '"') in code or ('>' + ref + '<') in code or ("'" + ref.replace("'", "\\'") + "'") in code or (ref == "Fi 1a part" and '"Fi {0}a part"' in D["fr"] or ref == "Fi 1a part")
            tr = await pg.evaluate("(r) => { window.__peli.setLang('fr'); const t = window.__peli.T(r); window.__peli.setLang('ca'); return t; }", ref)
            if not hi_es or (tr == ref and ref not in D['fr']): mal.append(ref + (" (no és a l'app)" if not hi_es else " (sense traduir)"))
        print("Botons que esmenta la guia: " + str(len(refs)) + " · que no existeixen o sense traduir: " + (", ".join(mal) or "cap"))
        await b.close()
        # 4) els 4 idiomes: tots els passos sense textos sense traduir; i res no se surt de la pantalla a l'iPhone SE
        for L in ("ca", "es", "en", "fr"):
            APPL = dict(APP); APPL["lang"] = L
            b, pg, errs = await ctx_for(p, APPL, p.devices["iPhone SE"])
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='guide']\").click(); }"); await pg.wait_for_timeout(120)
            sense, cat, surt = set(), set(), []
            for k in range(7):
                txt = await pg.evaluate("() => [...document.querySelectorAll('#ov .guide *')].filter(e => e.children.length === 0 && e.textContent.trim()).map(e => e.textContent.trim())")
                for t in txt:
                    if L != "ca" and t in D[L] and D[L][t] != t: sense.add(t)
                    if L == "fr" and re.search(CATW, t): cat.add(t)
                o = await pg.evaluate("() => { const s = document.querySelector('#ov .sheet'), se = document.scrollingElement; return Math.max(s.scrollWidth - s.clientWidth, 0) + Math.max(se.scrollWidth - innerWidth, 0); }")
                if o > 1: surt.append(k + 1)
                if k < 6: await pg.evaluate("() => document.querySelector(\"#ov .guide [data-act='gnext']\").click()")
            print("%s · sense traduir: %s · català al francès: %s · es surt de la pantalla als passos: %s · errors: %s" % (L, sorted(sense)[:4] or "cap", sorted(cat)[:4] or "cap", surt or "cap", errs or "cap"))
            await b.close()
asyncio.run(main())
