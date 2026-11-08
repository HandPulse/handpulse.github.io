# Base de dades dels partits (IndexedDB): traspàs des de localStorage, mateix informe, tancament de cop, més de 5 MB,
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
# navegador sense IndexedDB, esborrar un partit, tornar a obrir i còpia de seguretat d'anada i tornada
import asyncio, json, random, sys, os
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
exec(open(os.path.join(DIR, 'perf_mobil.py')).read().split("CLICK = ")[0].split("FITX = ")[1].split("\n", 1)[1])
NOU = "/mnt/user-data/outputs/peligrograma_directe.html"; VELL = "/mnt/user-data/outputs/.proves/app_abans_idb.html"
def url(f): return HP_URL   # al repositori, sempre l'app servida per web
CLOSE = "() => { const c = document.querySelector(\"#ov [data-act='close']\"); if (c && !document.getElementById('ov').hidden) c.click(); }"
IDB = """() => new Promise(res => { const rq = indexedDB.open('handpulse', 1); rq.onupgradeneeded = () => rq.result.createObjectStore('m');
  rq.onsuccess = () => { const db = rq.result, out = {}; const tx = db.transaction('m', 'readonly'), c = tx.objectStore('m').openCursor();
    c.onsuccess = () => { const r = c.result; if (r) { out[r.key] = JSON.parse(r.value).acts.length; r.continue(); } }; tx.oncomplete = () => { db.close(); res(out); }; }; rq.onerror = () => res(null); })"""
LSK = "() => Object.keys(localStorage).filter(k => k.indexOf('peli-directe:m:') === 0).map(k => k.slice(15)).sort()"
RESUM = """async () => { document.querySelector("#home [data-act='seasonrep']").click(); await new Promise(r => setTimeout(r, 500));
  const t = [...document.querySelectorAll('#rep table.rt')].slice(0, 2).map(x => x.textContent.replace(/\\s+/g, ' ').trim()).join(' | ');
  const c = document.querySelector("#rep [data-act='rclose'], #rep [data-act='close']"); if (c) c.click(); return t.slice(0, 600); }"""
def ok(cond, txt, mal):
    print("   %s %s" % ("✓" if cond else "✗", txt)); mal[0] += 0 if cond else 1
async def obre(p, fitx, dev, init=None, sense_idb=False, ctx=None):
    if ctx is None:
        b = await p.chromium.launch(); ctx = await b.new_context(**dev); ctx._b = b
        if sense_idb: await ctx.add_init_script("try { Object.defineProperty(window, 'indexedDB', { value: undefined, configurable: true }); } catch (e) {}")
        if init: await ctx.add_init_script(init)
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150])); pg._errs = errs
    await pg.goto(url(fitx)); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(900); await pg.evaluate(CLOSE)
    return ctx, pg
async def nova(c, fitx):
    pg = await c.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:150])); pg._errs = errs
    await pg.goto(url(fitx)); await pg.wait_for_timeout(1200); await pg.evaluate(CLOSE)
    return pg
async def main():
    async with async_playwright() as p:
        mal = [0]; dev = {"viewport": {"width": 1280, "height": 800}}
        INI = INIT.replace('"seen": 1', '"seen": 1, "guideV": 1')
        G0 = "if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1');"
        assert INI.count(G0) == 1, INI[:300]
        INI1 = INI.replace(G0, "if (!localStorage.getItem('peli-test-ini')) { localStorage.setItem('peli-test-ini', '1');")
        # A) usuari amb dades d'abans: traspàs, mateix informe
        print("A) Usuari amb dades d'abans (a localStorage):")
        cv, pv = await obre(p, VELL, dev, INI, sense_idb=True); resum_vell = await pv.evaluate(RESUM); abans = await pv.evaluate(LSK); await cv._b.close()
        c, pg = await obre(p, NOU, dev, INI1)
        idb = await pg.evaluate(IDB); queden = await pg.evaluate(LSK); act = await pg.evaluate("() => window.__peli.app.current")
        ok(set(idb or {}) == set(abans) and len(abans) >= 10, "els %d partits són a la base nova (%d hi són)" % (len(abans), len(idb or {})), mal)
        ok(queden == [act], "a l'emmagatzematge d'abans només hi queda el partit en curs (%s): %s" % (act, queden), mal)
        resum_nou = await pg.evaluate(RESUM)
        ok(resum_nou == resum_vell and len(resum_nou) > 100, "l'informe de temporada és idèntic al de la versió d'abans (%d caràcters)" % len(resum_nou), mal)
        fv = await pg.evaluate("() => { const id = Object.keys(window.__peli.app.index).find(x => x !== window.__peli.app.current); const mm = window.__peli.store.get('peli-directe:m:' + id); return [id, mm && mm.fv, mm && mm.acts.length]; }")
        ok(fv[1] == 1 and fv[2] > 0, "un partit antic (%s) s'obre amb la versió de format %s i %s accions" % (fv[0], fv[1], fv[2]), mal)
        # B) tancament de cop just després d'apuntar
        print("B) Apuntar i tancar l'app de cop:")
        n0 = await pg.evaluate("() => window.__peli.m ? window.__peli.m.acts.length : -1")
        await pg.evaluate("() => { const m = window.__peli.m; m.acts.push({ i: (m.seq || 0) + 1, t: 100, p: 1, e: 'N', d: 7, a: 'G', z: '9C', k: null, g: null, s: null, gk: 1, rgk: null, x: 0 }); m.seq = (m.seq || 0) + 1; window.__peli.saveMatch(); }")
        await pg.close()   # sense esperar res
        pg = await nova(c, NOU)
        n1 = await pg.evaluate("() => window.__peli.m ? window.__peli.m.acts.length : -1"); idb1 = await pg.evaluate(IDB)
        ok(n1 == n0 + 1 and idb1.get(act) == n0 + 1, "l'acció hi és en tornar a obrir (%d → %d accions; base nova: %s)" % (n0, n1, idb1.get(act)), mal)
        # C) més de 5 MB de partits
        print("C) Més de 5 MB de partits:")
        r = await pg.evaluate("""() => { const s = window.__peli.store, base = s.get('peli-directe:m:' + window.__peli.app.current); let ok = 0;
          for (let k = 0; k < 90; k++) { const mm = JSON.parse(JSON.stringify(base)); mm.id = 'Z' + k; mm.pad = 'x'.repeat(60000); if (s.set('peli-directe:m:Z' + k, mm)) ok++; }
          return { ok, kb: s.kb(), lskb: s.lskb(), idb: s.idb() }; }""")
        await pg.wait_for_timeout(1500)
        toast = await pg.evaluate("() => (document.getElementById('toast') || {}).textContent || ''")
        await pg.close(); pg = await nova(c, NOU)
        llegits = await pg.evaluate("() => { let n = 0; for (let k = 0; k < 90; k++) { const mm = window.__peli.store.get('peli-directe:m:Z' + k); if (mm && mm.pad && mm.pad.length === 60000) n++; } return n; }")
        ok(r["ok"] == 90 and llegits == 90 and "No s'ha pogut" not in toast, "90 partits grans desats i llegits en tornar a obrir: %d de 90 · dades a l'aparell %.1f MB (a l'emmagatzematge d'abans només %d KB) · avís: %s" % (llegits, r["kb"] / 1024, r["lskb"], toast[:40] or "cap"), mal)
        # amb la versió d'abans, el mateix falla
        cv, pv = await obre(p, VELL, dev, INI)
        fail = await pv.evaluate("""() => { const base = localStorage.getItem('peli-directe:m:' + JSON.parse(localStorage.getItem('peli-directe:app')).current); let k = 0;
          try { for (; k < 90; k++) localStorage.setItem('peli-directe:m:Z' + k, base.slice(0, -1) + ',"pad":"' + 'x'.repeat(60000) + '"}'); return 'sense error'; } catch (e) { return 'error a partir del partit ' + k; } }""")
        ok("error" in fail, "a la versió d'abans, el mateix dona error de límit (%s)" % fail, mal); await cv._b.close()
        # G) obrir un partit antic i tancar l'app de cop, abans d'apuntar-hi res
        print("G) Obrir un partit antic i tancar de cop:")
        antic = await pg.evaluate("() => Object.keys(window.__peli.app.index).filter(x => /^P/.test(x) && x !== window.__peli.app.current).sort().pop()")
        nant = await pg.evaluate("(id) => window.__peli.store.get('peli-directe:m:' + id).acts.length", antic)
        await pg.evaluate("() => document.querySelector(\"#home [data-act='partits']\").click()"); await pg.wait_for_timeout(200)
        obert = await pg.evaluate("(id) => { const b = document.querySelector(\"#ov [data-act='open'][data-v='\" + id + \"']\"); if (b) b.click(); return !!b; }", antic); await pg.wait_for_timeout(250)
        await pg.close()
        pg = await nova(c, NOU)
        g = await pg.evaluate("() => [window.__peli.app.current, window.__peli.m ? window.__peli.m.id : null, window.__peli.m ? window.__peli.m.acts.length : -1]")
        ok(obert and g[0] == antic and g[1] == antic and g[2] == nant, "s'obre el partit %s (%d accions) i, en tornar a obrir l'app, és el partit en curs amb totes les accions: %s" % (antic, nant, g), mal)
        act = antic
        # E) esborrar un partit
        print("E) Esborrar un partit:")
        ab = await pg.evaluate(IDB); vict = sorted(k for k in ab if k.startswith("P") and k != act)[0]
        await pg.evaluate("() => document.querySelector(\"#home [data-act='partits']\").click()"); await pg.wait_for_timeout(200)
        await pg.evaluate(CLOSE); await pg.wait_for_timeout(150)
        await pg.evaluate("() => document.querySelector(\"[data-act='menu']\").click()"); await pg.wait_for_timeout(250)
        t1 = await pg.evaluate("(id) => { const b = document.querySelector(\"#ov [data-act='delask'][data-v='\" + id + \"']\"); if (b) b.click(); return !!b; }", vict); await pg.wait_for_timeout(200)
        t2 = await pg.evaluate("() => { const b = document.querySelector(\"#ov [data-act='delmatch']\"); if (b) b.click(); return !!b; }"); await pg.wait_for_timeout(600)
        print("   botons: «Esborra» %s · confirmació %s" % (t1, t2))
        de = await pg.evaluate(IDB); idx = await pg.evaluate("(id) => !!window.__peli.app.index[id]", vict)
        ok(vict not in de and not idx, "el partit %s ja no és a la base nova ni a la llista" % vict, mal)
        print("   errors: %s" % (pg._errs or "cap")); mal[0] += 1 if pg._errs else 0
        # F) còpia de seguretat d'anada i tornada
        print("F) Còpia de seguretat:")
        await pg.evaluate("() => { const ov = document.getElementById('ov'); if (!ov.hidden) { const c = ov.querySelector(\"[data-act='close']\"); if (c) c.click(); } }")
        esperat = await pg.evaluate("() => Object.keys(window.__peli.app.index).length")
        await pg.evaluate("() => document.querySelector(\"#home [data-act='backup']\").click()"); await pg.wait_for_timeout(300)
        async with pg.expect_download() as dl:
            await pg.evaluate("() => document.querySelector(\"#ov [data-act='bkexport']\").click()")
        d = await dl.value; path = "/tmp/copia_idb.json"; await d.save_as(path)
        cop = json.load(open(path)); nmat = len(cop.get("matches", {}))
        totals = {k: len(v.get("acts", [])) for k, v in cop.get("matches", {}).items()}
        await c._b.close()
        c2, pg2 = await obre(p, NOU, dev, "window.__hpTest = true; localStorage.setItem('peli-directe:app', JSON.stringify({ v: 1, roster: [{ d: 1, n: 'X', gk: true }], seen: 1, guideV: 1, index: {}, current: null }));")
        await pg2.evaluate("() => document.querySelector(\"#home [data-act='backup']\").click()"); await pg2.wait_for_timeout(300)
        await pg2.set_input_files("#bkfile", path); await pg2.wait_for_timeout(300)
        await pg2.evaluate("() => document.querySelector(\"#ov [data-act='bkimport']\").click()"); await pg2.wait_for_timeout(1500)
        await pg2.evaluate("() => { const b = [...document.querySelectorAll('#ov button')].find(x => /^(Recupera|Sí|D'acord|Afegeix)/.test(x.textContent.trim()) && x.offsetParent); if (b) b.click(); }"); await pg2.wait_for_timeout(1500)
        rec = await pg2.evaluate(IDB); rec_ix = await pg2.evaluate("() => Object.keys(window.__peli.app.index).length")
        iguals = sum(1 for k, v in totals.items() if (rec or {}).get(k) == v)
        ok(nmat == esperat and nmat >= 10 and iguals == nmat and rec_ix == nmat, "la còpia porta %d partits; en un aparell nou se'n recuperen %d amb totes les accions (a la llista: %d)" % (nmat, iguals, rec_ix), mal)
        print("   errors: %s" % (pg2._errs or "cap")); mal[0] += 1 if pg2._errs else 0
        await c2._b.close()
        # D) navegador sense IndexedDB
        print("D) Navegador sense la base nova:")
        c3, pg3 = await obre(p, NOU, p.devices["Pixel 7"], INI, sense_idb=True)
        n0 = await pg3.evaluate("() => window.__peli.m ? window.__peli.m.acts.length : -1"); usa = await pg3.evaluate("() => window.__peli.store.idb()")
        res3 = await pg3.evaluate(RESUM)   # abans d'afegir el gol de prova
        await pg3.evaluate("() => { const m = window.__peli.m; m.acts.push({ i: (m.seq || 0) + 1, t: 100, p: 1, e: 'N', d: 7, a: 'G', z: '9C', k: null, g: null, s: null, gk: 1, rgk: null, x: 0 }); m.seq++; window.__peli.saveMatch(); }")
        await pg3.reload(); await pg3.wait_for_timeout(800); await pg3.evaluate(CLOSE)
        n1 = await pg3.evaluate("() => window.__peli.m ? window.__peli.m.acts.length : -1"); queden3 = await pg3.evaluate(LSK)
        ok(not usa and n1 == n0 + 1 and res3 == resum_vell and len(queden3) >= 10, "funciona com sempre: base nova %s · acció desada %d → %d · mateix informe %s · partits a l'emmagatzematge d'abans: %d" % (usa, n0, n1, res3 == resum_vell, len(queden3)), mal)
        print("   errors: %s" % (pg3._errs or "cap")); mal[0] += 1 if pg3._errs else 0
        await c3._b.close()
        print("RESUM: %s" % ("tot correcte" if not mal[0] else "%d problemes" % mal[0]))
asyncio.run(main())
