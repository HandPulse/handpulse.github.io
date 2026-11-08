# PDF de l'informe del partit: logo a cada pàgina (A4 i carta) i cap targeta encavalcada a la pàgina dels jugadors
import os, shutil
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, random, re, subprocess, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
exec(open(os.path.join(DIR, 'perf_mobil.py')).read().split("CLICK = ")[0].split("FITX = ")[1].split("\n", 1)[1])
VERS = [("ara", HP_URL)]   # al repositori només hi ha la versió actual
SOLAP = """() => { const g = document.querySelector('#print .pg2'), cs = [...document.querySelectorAll('#print .pg2 > *')].filter(e => e.getBoundingClientRect().width);
  const r = cs.map(e => e.getBoundingClientRect()), mal = [], gw = g ? g.getBoundingClientRect().width : 0;
  for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) { const w = Math.min(r[i].right, r[j].right) - Math.max(r[i].left, r[j].left), h = Math.min(r[i].bottom, r[j].bottom) - Math.max(r[i].top, r[j].top); if (w > 2 && h > 2) mal.push('encavalcades: ' + (cs[i].querySelector('h3') || cs[i]).textContent.trim().slice(0, 30) + ' / ' + (cs[j].querySelector('h3') || cs[j]).textContent.trim().slice(0, 30)); }
  const f = document.querySelector('#print .pg2 .fsgrid'), fc = f ? f.closest('.repcard') : null, fr = fc ? fc.getBoundingClientRect().width / gw : 0;
  if (fc && fr < 0.95) mal.push('el rendiment per fase només ocupa el ' + Math.round(100 * fr) + ' % de l\\'amplada');
  return { targetes: cs.map(e => (e.querySelector('h3') || e).textContent.trim().slice(0, 22)), fase: !!fc, mal }; }"""
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, fitx in VERS:
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1024, "height": 748}); await ctx.add_init_script(INIT.replace('"seen": 1', '"seen": 1, "guideV": 1'))
            # defenses apuntades (com al partit P06): així surt la targeta «Atac contra cada defensa del rival» al costat
            await ctx.add_init_script("(() => { try { const a = JSON.parse(localStorage.getItem('peli-directe:app')); const k = 'peli-directe:m:' + a.current, m = JSON.parse(localStorage.getItem(k)); if (m && !m.__df) { m.acts.forEach(x => { x.df = x.p === 1 ? '6:0' : '3:2:1'; }); m.__df = 1; localStorage.setItem(k, JSON.stringify(m)); } } catch (e) {} })();")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(fitx); await pg.wait_for_timeout(700)
            await pg.evaluate("() => { window.print = () => {}; const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); const r = document.querySelector(\"[data-act='report']\"); if (r) r.click(); }"); await pg.wait_for_timeout(500)
            so = None
            for paper, ample in (("A4", 726), ("Letter", 748)):   # amplada útil del paper, en punts de pantalla (marges de 9 mm)
                await pg.emulate_media(media="screen"); await pg.set_viewport_size({"width": 1024, "height": 748})
                await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); if (document.getElementById('rep').hidden) { const r = document.querySelector(\"[data-act='report']\"); if (r) r.click(); } }"); await pg.wait_for_timeout(400)
                await pg.evaluate("() => { const b = document.querySelector(\"#rep [data-act='rprint']\"); if (b) b.click(); }"); await pg.wait_for_timeout(900)
                await pg.set_viewport_size({"width": ample, "height": 1000}); await pg.emulate_media(media="print"); await pg.wait_for_timeout(300)
                if so is None or paper == "A4": so = await pg.evaluate(SOLAP)
                f = "/tmp/pdf_%s_%s.pdf" % (nom, paper)
                open(f, "wb").write(await pg.pdf(format=paper, print_background=True, prefer_css_page_size=False))
                if not shutil.which("pdfinfo"): print("   (sense eines de PDF en aquest ordinador: no es miren els logos de cada pàgina)"); continue
                n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", f], capture_output=True, text=True).stdout).group(1))
                sense = []; titols = []
                for k in range(1, n + 1):
                    t = subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), "-layout", f, "-"], capture_output=True, text=True).stdout
                    if not re.search(r"Hand\s*Pulse", t): sense.append(k)
                    titols.append((t.strip().split("\n")[0] if t.strip() else "(buida)")[:46])
                if nom == "ara": mal += 1 if sense else 0
                print("%-5s %-6s · %d pàgines · pàgines sense logo: %s" % (nom, paper, n, sense or "cap"))
                if nom == "ara" and paper == "Letter": print("   títols:", titols)
            if nom == "ara": mal += 1 if (so["mal"] or errs) else 0
            print("%-5s pàgina dels jugadors: %s, rendiment per fase %s · problemes: %s · errors %s" % (nom, so["targetes"], "sí" if so["fase"] else "no", so["mal"] or "cap", errs or "cap"))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
