# Informe de més d'un partit: columna «Per partit» (total ÷ partits) al costat del total; amb un sol partit, igual que abans
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, random
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
exec(open(os.path.join(DIR, 'perf_mobil.py')).read().split("CLICK = ")[0].split("FITX = ")[1].split("\n", 1)[1])
LLEGIR = """() => { const t = document.querySelector('#rep .rs-table table'); if (!t) return null; const rows = [...t.querySelectorAll('tr')];
  const hdr = [...rows[1].querySelectorAll('th')].map(x => x.textContent.trim()); const out = { hdr: hdr.join(' | '), files: {} };
  rows.slice(2).forEach(r => { const c = [...r.querySelectorAll('td')].map(x => x.textContent.trim()); out.files[c[0]] = c.slice(1); });
  out.partits = ((document.querySelector('#rep select') || {}).selectedOptions || [{}])[0].textContent; return out; }"""
async def main():
    async with async_playwright() as p:
        for nom, dev, L in (("ordinador", {"viewport": {"width": 1536, "height": 860}}, "ca"), ("mòbil (anglès)", p.devices["Pixel 7"], "en")):
            b = await p.chromium.launch(); ctx = await b.new_context(**dev)
            init = INIT.replace('"seen": 1', '"seen": 1, "guideV": 1, "lang": "' + L + '"')
            await ctx.add_init_script(init)
            await ctx.add_init_script("new MutationObserver(() => document.querySelectorAll('#rep details.rmore:not([open])').forEach(d => { d.open = true; })).observe(document, { childList: true, subtree: true });")   # obre «Més detall», com faria l'entrenador
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(500)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); window.__peli.app.view = 'home'; }")
            # l'informe de temporada
            await pg.evaluate("() => { const b = document.querySelector(\"#home [data-act='seasonrep']\"); if (b) b.click(); }"); await pg.wait_for_timeout(600)
            r = await pg.evaluate(LLEGIR)
            if r:
                n = int(''.join(ch for ch in r["partits"].split("(")[1] if ch.isdigit())) if "(" in r["partits"] else 0
                print("==== %s · %s" % (nom, r["partits"]))
                print("   capçalera: " + r["hdr"])
                for k in list(r["files"])[:16]:
                    if k in ("Pèrdues", "Turnovers", "Gols", "Goals", "% eficàcia", "% efficiency", "Exclusions 2′", "2′ suspensions", "Recuperacions", "Steals"):
                        c = r["files"][k]; print("   %-16s %s" % (k, " | ".join(c)))
                # comprovació: per partit = total ÷ partits, per a totes les files de comptar
                mal = []
                for k, c in r["files"].items():
                    if len(c) >= 8 and c[3] and c[2] and "%" not in c[2]:
                        esper = round(int(c[2]) / n, 1); val = float(c[3].replace(",", "."))
                        if abs(esper - val) > 0.05: mal.append(k)
                print("   files on «per partit» no és total ÷ %d: %s" % (n, mal or "cap"))
                if nom == "ordinador": await (await pg.query_selector("#rep .rs-table")).screenshot(path="/tmp/perpartit.png")
            surt = await pg.evaluate("() => Math.max(document.scrollingElement.scrollWidth - innerWidth, 0)")
            # un sol partit: sense la columna
            await pg.evaluate("() => { const s = document.querySelector('#rep select'); if (s) { const o = [...s.options].find(x => /^P\\d|contra|vs|against/i.test(x.textContent)); if (o) { s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })); } } }"); await pg.wait_for_timeout(400)
            r1 = await pg.evaluate(LLEGIR)
            print("   un sol partit (%s): %s · surt de la pantalla: %d px · errors: %s" % (r1["partits"][:30] if r1 else "?", r1["hdr"] if r1 else "?", surt, errs or "cap"))
            await b.close()
asyncio.run(main())
