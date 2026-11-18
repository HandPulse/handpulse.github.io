# Mapes dels informes: amb la manera nova, els pals i el fora per zones al voltant de la porteria; amb partits antics, com abans
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": 1, "n": "Porter", "gk": True}, {"d": 3, "n": "Jugador 3", "gk": False}]
def A(i, a, **kw):
    x = {"i": i, "t": 20 * i, "p": 1, "e": "N", "d": 3, "a": a, "k": None, "z": "9C", "g": None, "s": None, "gk": 1, "rgk": None}; x.update(kw); return x
NOU = [A(1, "G", g=5), A(2, "A", g=1), A(3, "P", pz="TL", po="rebot", rbe="N", rbd=3), A(4, "P", pz="TL", po="fora"), A(5, "P", pz="L2", po="fora"), A(6, "F", fz="R3")] + \
      [dict(A(20 + k, ["G", "A", "P", "F"][k % 4], **({"pz": "T", "po": "fora"} if k % 4 == 2 else {"fz": "L1"} if k % 4 == 3 else {"g": 1 + k % 9})), e="R", d=k + 2) for k in range(44)]
VELL = [A(1, "G", g=5), A(2, "A", g=1), A(3, "P"), A(4, "F")]
async def main():
    async with async_playwright() as p:
        mal = 0
        for nom, acts in (("partit amb la manera nova", NOU), ("partit antic", VELL)):
            M = {"id": "P01", "rival": "CH Prova", "date": "2026-11-14", "durada": 30, "part": 2, "clock": {"acc": 3600, "start": None}, "gk": 1, "rgk": None, "rivals": [], "acts": acts, "seq": len(acts), "squad": [1, 3], "upd": 1}
            APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": "P01", "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {"P01": {"rival": "CH Prova", "n": len(acts), "upd": 1, "sc": [1, 0], "date": "2026-11-14"}}, "guideV": 1}
            b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 1280, "height": 900})
            await ctx.add_init_script("window.__hpTest = true; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); localStorage.setItem('peli-directe:m:P01', " + json.dumps(json.dumps(M)) + "); }")
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
            await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(600)
            await pg.evaluate("() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); document.querySelector(\"#home [data-act='seasonrep']\").click(); }"); await pg.wait_for_timeout(500)
            await pg.evaluate("() => { const s = [...document.querySelectorAll('#rep select')].find(x => [...x.options].some(o => o.value === 'P01')); s.value = 'P01'; s.dispatchEvent(new Event('change', { bubbles: true })); }"); await pg.wait_for_timeout(400)
            await pg.evaluate("() => [...document.querySelectorAll(\"#rep [data-act='rtab']\")].find(x => x.getAttribute('data-v') === 'mapes').click()"); await pg.wait_for_timeout(400)
            r = await pg.evaluate("""() => { const w = document.querySelector('#rep .rgw'); const g = (w || document).querySelector('#rep .rgoal') || document.querySelector('#rep .rgoal');
              const t = (z) => { const e = w && w.querySelector('[data-z="' + z + '"]'); return e ? e.textContent : ''; };
              return { marc: !!w, palTL: t('P:TL'), palL2: t('P:L2'), foraR3: t('F:R3'), ample: g ? Math.round(g.getBoundingClientRect().width) : 0, alt: g ? Math.round(g.getBoundingClientRect().height) : 0 }; }""")
            if nom.startswith("partit amb"):
                ok = r["marc"] and r["palTL"] == "2" and r["palL2"] == "1" and r["foraR3"] == "1"
                if ok: await (await pg.query_selector("#rep .rgw")).screenshot(path="/tmp/mapa_pal.png")
                mida_nou = (r["ample"], r["alt"])
            else:
                ok = not r["marc"]
                ok = ok and abs(r["ample"] - mida_nou[0]) <= 0.2 * r["ample"] and abs(r["alt"] - mida_nou[1]) <= 0.2 * r["alt"]
            ok = ok and not errs; mal += 0 if ok else 1
            print("%s %-28s %s · errors: %s" % ("✓" if ok else "✗", nom, r, errs or "cap"))
            if nom.startswith("partit amb"):
                import subprocess, shutil
                await pg.evaluate("() => { window.print = () => {}; const b = document.querySelector(\"#rep [data-act='print'], #rep [data-act='pdf'], [data-act='rprint']\"); if (b) b.click(); }"); await pg.wait_for_timeout(900)
                pp = await pg.evaluate("() => [...document.querySelectorAll('#print section.pp')].map(x => ((x.querySelector('.ptitle') || {}).textContent || '').slice(0, 34) + ':' + x.querySelectorAll('.repcard.pmap').length)")
                f = "/tmp/mapes_pal.pdf"; open(f, "wb").write(await pg.pdf(format="Letter", print_background=True))
                if shutil.which("pdfinfo"):
                    n = int(subprocess.run(["pdfinfo", f], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
                    sense = [k for k in range(1, n + 1) if "Hand" not in subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), f, "-"], capture_output=True, text=True).stdout]
                else: n, sense = -1, []
                okp = not sense and all(int(x.split(":")[-1]) <= 8 for x in pp if "xuta" in x)
                mal += 0 if okp else 1
                print("%s PDF en mida carta: %s pàgines · sense logo: %s · seccions de mapes: %s" % ("✓" if okp else "✗", n, sense or "cap", [x for x in pp if "xuta" in x]))
            await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
