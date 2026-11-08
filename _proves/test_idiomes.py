# Cada idioma: recórrer les pantalles principals i buscar textos sense traduir (claus catalanes o paraules catalanes)
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys, re
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/peligrograma_directe.html"
LANGS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["es", "en", "fr"]
ROSTER = [{"d": d, "n": "Jugador " + str(d), "gk": d in (1, 12)} for d in (1, 2, 3, 5, 6, 7, 9, 12)]
CATW = r"\b(amb|els|aquest|aquesta|aquests|què|partit|partits|jugadors|llançaments?|Desa|Toca|Tanca|també|només|encara|perquè|Esborra|assistència|porteria|aturades?|rellotge)\b"
TEXTS = """() => { const out = new Set(); const vis = (e) => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e); return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none'; };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { const t = n.nodeValue.replace(/\\s+/g, ' ').trim(); if (t && /[A-Za-zÀ-ÿ]{2}/.test(t) && n.parentElement && vis(n.parentElement) && !n.parentElement.closest('script,style')) out.add(t); }
  document.querySelectorAll('[title],[aria-label],[placeholder]').forEach(e => { if (!vis(e)) return; ['title', 'aria-label', 'placeholder'].forEach(a => { const v = (e.getAttribute(a) || '').trim(); if (v && /[A-Za-zÀ-ÿ]{2}/.test(v)) out.add(v); }); });
  return [...out]; }"""
async def main():
    s = open(FITX, encoding="utf-8").read(); D = json.loads(re.search(r"^  var DICT = (\{.*\});$", s, re.M).group(1))
    async with async_playwright() as p:
        for L in LANGS:
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {}, "lang": L}
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800})
            await ctx.add_init_script("window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(300)
            seen = {}
            async def grab(nom):
                for t in await pg.evaluate(TEXTS): seen.setdefault(t, nom)
            await grab("benvinguda")
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c) c.click(); }"); await pg.wait_for_timeout(100); await grab("inici")
            await pg.evaluate("() => document.querySelector(\"#home [data-act='partits']\").click()"); await pg.wait_for_timeout(100); await grab("partits")
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='pnew']\").click()"); await pg.wait_for_timeout(150); await grab("partit nou")
            await pg.evaluate("() => { const s = document.getElementById('nfix'); if (s) { s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); } const set = (id, v) => { const e = document.getElementById(id); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); } }; set('nriv', 'CH Prova'); set('nrivals', '4 R4\\n7 R7'); }")
            await pg.evaluate("() => { document.querySelector(\"[data-act='sqall']\").click(); document.querySelector(\"[data-act='nstart']\").click(); }"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); window.__peli.m.det = 'com'; }"); await pg.wait_for_timeout(100)
            T = "(s) => { const e = document.querySelector(s); if (e) e.dispatchEvent(new MouseEvent('click', { bubbles: true })); }"
            await grab("partit: pas 1")
            await pg.evaluate(T, "#qui [data-act='player'][data-v='3']"); await grab("partit: pas 2")
            await pg.evaluate(T, "#que [data-act='action'][data-v='PER']"); await grab("partit: tipus de pèrdua")
            await pg.evaluate(T, "[data-act='tipus'][data-v='MP']"); await grab("partit: qui l'ha recuperat")
            await pg.evaluate(T, "#on [data-act='opp'][data-v='']")
            await pg.evaluate(T, "#qui [data-act='player'][data-v='5']"); await pg.evaluate(T, "#que [data-act='action'][data-v='G']"); await grab("partit: zona")
            await pg.evaluate(T, "[data-act='zone'][data-v='7M']"); await grab("partit: porteria"); await pg.evaluate(T, "[data-act='goal'][data-v='5']"); await grab("partit: qui ha provocat el 7 m")
            await pg.evaluate(T, "#on [data-act='prov7'][data-v='']")
            await pg.evaluate(T, "#qui [data-act='player'][data-v='6']"); await pg.evaluate(T, "#que [data-act='action'][data-v='2M']"); await grab("partit: 2 minuts")
            await pg.evaluate(T, "#on [data-act='opp'][data-v='']")
            await pg.evaluate(T, "[data-act='defs']"); await pg.wait_for_timeout(100); await grab("defenses")
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            await pg.evaluate("() => document.querySelector(\"[data-act='report']\").click()"); await pg.wait_for_timeout(250)
            tabs = await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].map(x => x.getAttribute('data-v'))")
            for t in tabs:
                await pg.evaluate("(v) => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === v).click()", t); await pg.wait_for_timeout(80); await grab("informe: " + t)
            await pg.evaluate("() => { const e = document.querySelector(\"#rep table.rt [data-act='pfitxa']\"); if (e) e.click(); }"); await pg.wait_for_timeout(200); await grab("fitxa del jugador")
            # textos sense traduir: una clau catalana que en aquest idioma es diu diferent, o paraules catalanes (francès)
            keys = D[L] if L != "ca" else {}
            sense = sorted({(t, w) for t, w in seen.items() if t in keys and keys[t] != t})
            cat = sorted({(t, w) for t, w in seen.items() if L == "fr" and re.search(CATW, t) and t not in keys.values()})
            print("== %s: %d textos vistos · sense traduir: %d · amb paraules catalanes: %d · errors: %s" % (L, len(seen), len(sense), len(cat), errs or "cap"))
            for t, w in sense[:15]: print("   sense traduir [%s]: %s" % (w, t[:110]))
            for t, w in cat[:15]: print("   català [%s]: %s" % (w, t[:110]))
            await b.close()
asyncio.run(main())
