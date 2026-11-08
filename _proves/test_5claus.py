# Resum de l'informe: marcador i claus a la vista, la resta plegada a «Més detall»; es recorda en canviar de pestanya; el PDF, sencer
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, random, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
exec(open(os.path.join(DIR, 'perf_mobil.py')).read().split("CLICK = ")[0].split("FITX = ")[1].split("\n", 1)[1])
FITX = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/peligrograma_directe.html"
VIS = """() => { const v = s => { const e = document.querySelector('#rep ' + s); if (!e) return 'no hi és'; const vis = e.checkVisibility ? e.checkVisibility({ contentVisibilityAuto: true, visibilityProperty: true }) : !e.closest('details:not([open])'); return vis && (e.tagName === 'SUMMARY' || !e.closest('details:not([open])')) ? 'a la vista' : 'plegat'; };
  return { marcador: v('.rs-score'), claus: v('.keyline, .kcard, .claus, .keys'), detall: v('details.rmore > summary'), taula: v('.rs-table'), tipus: v('.rs-types'), pastis: v('.rs-pie'), obert: !!(document.querySelector('#rep details.rmore') || {}).open }; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, dev in (("tauleta", {"viewport": {"width": 1280, "height": 800}}), ("mòbil", p.devices["Pixel 7"])):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev); await ctx.add_init_script(INIT.replace('"seen": 1', '"seen": 1, "guideV": 1'))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(900)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }")
            for quin, act in (("partit", "[data-act='report']"), ("temporada", "#home [data-act='seasonrep']")):
                if quin == "temporada":
                    await pg.evaluate("() => { const c = document.querySelector(\"#rep [data-act='rclose'], #rep [data-act='close']\"); if (c) c.click(); const h = document.querySelector(\"[data-act='home']\"); if (h) h.click(); }"); await pg.wait_for_timeout(300)
                await pg.evaluate("(s) => document.querySelector(s).click()", act); await pg.wait_for_timeout(500)
                await pg.evaluate("() => { const t = [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'resum'); if (t) t.click(); }"); await pg.wait_for_timeout(300)
                await pg.evaluate("() => { const d = document.querySelector('#rep details.rmore'); if (d && d.open) d.querySelector('summary').click(); }"); await pg.wait_for_timeout(150)
                r0 = await pg.evaluate(VIS)
                await pg.evaluate("() => document.querySelector('#rep details.rmore > summary').click()"); await pg.wait_for_timeout(250)
                r1 = await pg.evaluate(VIS)
                await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'jugadors').click()"); await pg.wait_for_timeout(250)
                await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'resum').click()"); await pg.wait_for_timeout(250)
                r2 = await pg.evaluate(VIS)
                ok = r0["marcador"] == r0["claus"] == r0["detall"] == "a la vista" and r0["taula"] == r0["tipus"] == r0["pastis"] == "plegat" and r1["taula"] == r1["pastis"] == "a la vista" and r2["obert"] and r2["taula"] == "a la vista"
                mal += 0 if ok else 1
                print("%s %s · %s:\n   de sortida: %s\n   en tocar «Més detall»: taula %s, gràfics %s · en tornar d'una altra pestanya: %s" % ("✓" if ok else "✗", nom, quin, r0, r1["taula"], r1["pastis"], "obert" if r2["obert"] else "plegat"))
                if nom == "mòbil" and quin == "partit":
                    await pg.evaluate("() => document.querySelector('#rep details.rmore > summary').click()"); await pg.wait_for_timeout(200)
                    await pg.screenshot(path="/tmp/rep_5claus_tancat.png")
                    await pg.evaluate("() => document.querySelector('#rep details.rmore > summary').click()"); await pg.wait_for_timeout(200)
                    await pg.screenshot(path="/tmp/rep_5claus_mobil.png")
            # el PDF: tot sencer
            await pg.evaluate("() => { window.print = () => { window.__printed = (document.getElementById('printroot') || document.querySelector('.pp') || document.body).innerHTML.length; }; }")
            pdf = await pg.evaluate("""() => { const b = document.querySelector("#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']"); if (b) b.click();
              return new Promise(r => setTimeout(() => { const html = [...document.querySelectorAll('section.pp')].map(x => x.innerHTML).join(''); r({ taula: html.includes('rs-table'), tipus: html.includes('rs-types'), pastis: html.includes('rs-pie'), plegat: html.includes('rmore') }); }, 900)); }""")
            okp = pdf["taula"] and pdf["tipus"] and pdf["pastis"] and not pdf["plegat"]; mal += 0 if okp else 1
            print("%s %s · PDF: taula %s, llançaments per tipus %s, gràfics %s, res plegat: %s · errors %s" % ("✓" if okp else "✗", nom, pdf["taula"], pdf["tipus"], pdf["pastis"], not pdf["plegat"], errs or "cap"))
            mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
