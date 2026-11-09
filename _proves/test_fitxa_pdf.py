# PDF de l'informe individual: la fitxa, els mapes del jugador (amb porteries) i la comparació, amb el logo a totes les pàgines
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, random, sys, subprocess
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
exec(open(os.path.join(DIR, 'perf_mobil.py')).read().split("CLICK = ")[0].split("FITX = ")[1].split("\n", 1)[1])
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt))
        for amb_cmp in (False, True):
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 800}); await ctx.add_init_script(INIT.replace('"seen": 1', '"seen": 1, "guideV": 1'))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(800)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            d = await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => /Tot l'equip/.test(o.textContent))); const o = [...s.options].find(o => o.value === '7') || [...s.options].filter(o => /^\\d+$/.test(o.value))[1]; s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })); return o.value; }"); await pg.wait_for_timeout(600)
            print("%s (jugador %s):" % ("amb comparació" if amb_cmp else "sense comparació", d))
            if amb_cmp:
                await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => !/Tot l'equip/.test(x.textContent) && [...x.options].some(o => /^\\d+/.test(o.textContent.trim()) && o.value !== '')); const o = [...s.options].find(o => o.value && o.value !== s.value && o.value !== '1' && /^\\d+$/.test(o.value) && +o.value > 2); s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(500)
                pant = await pg.evaluate("() => { const c = [...document.querySelectorAll('#rep .repcard')].find(x => x.querySelector('.pcmaps')); return c ? c.querySelectorAll('svg').length : 0; }")
                ok(pant >= 2, "a la pantalla, la comparació mostra els mapes i les porteries dels dos (%d gràfics)" % pant)
            await pg.evaluate("() => { window.print = () => {}; const b = [...document.querySelectorAll('#rep .pfx button')].find(x => x.getAttribute('data-act') !== 'pshare'); if (b) b.click(); }"); await pg.wait_for_timeout(900)
            secs = await pg.evaluate("() => [...document.querySelectorAll('#print section.pp')].map(x => ({ t: ((x.querySelector('.ptitle, .fxh b') || {}).textContent || '').slice(0, 50), logo: !!x.querySelector('.plogo'), svgs: x.querySelectorAll('svg').length }))")
            f = "/tmp/fitxa_%s.pdf" % ("cmp" if amb_cmp else "sol"); open(f, "wb").write(await pg.pdf(format="A4", print_background=True))
            # pàgina per pàgina, només si hi ha pdfinfo i pdftotext (a GitHub no hi són: allà es comproven les seccions, cadascuna amb el logo)
            import shutil
            if shutil.which("pdfinfo") and shutil.which("pdftotext") and not os.environ.get("HP_SENSE_PDFINFO"):
                n = int(subprocess.run(["pdfinfo", f], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
                sense = [k for k in range(1, n + 1) if "Hand" not in subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), f, "-"], capture_output=True, text=True).stdout]
            else:
                n, sense = -1, []
                print("   · sense pdfinfo en aquest ordinador: es comproven les seccions del PDF, no les pàgines")
            esp = 4 if amb_cmp else 3
            ok(len(secs) == esp and all(x["logo"] for x in secs) and secs[1]["svgs"] >= 2, "seccions: %s" % [(x["t"][:30], x["svgs"], "logo" if x["logo"] else "SENSE") for x in secs])
            ok(not sense, "PDF A4: %s pàgines · pàgines sense logo: %s" % (n if n >= 0 else "?", sense or "cap"))
            print("   errors: %s" % (errs or "cap")); mal += 1 if errs else 0
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
