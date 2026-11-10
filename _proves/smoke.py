# Repàs general de HandPulse (substitueix les proves grans perdudes en el reinici del 31/10/2026)
import os
DIR = os.path.dirname(os.path.abspath(__file__))
HP_URL = os.environ.get("HP_URL", "http://127.0.0.1:8765/index.html")   # l'app, servida per web com a GitHub Pages
import asyncio, json, sys
from playwright.async_api import async_playwright
exec(open(os.path.join(DIR, 'fonts.py')).read())
FITX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "..", "index.html")
ROSTER = [{"d": d, "n": "Jugador " + str(d), "gk": d in (1, 12)} for d in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)]
APP = {"v": 1, "team": "UE Sarrià", "durada": 30, "current": None, "roster": ROSTER, "seen": 1, "gkFixAt": "x", "index": {}}
VIS = "(s) => { const e = document.querySelector(s); if (!e) return 'NO HI ÉS'; if (e.disabled) return 'DESACTIVAT'; const r = e.getBoundingClientRect(); if (!r.width || !r.height) return 'AMAGAT'; e.dispatchEvent(new MouseEvent('click', { bubbles: true })); return 'ok'; }"
async def obre(p, dev):
    b = await p.chromium.launch(); ctx = await b.new_context(**dev)
    await ctx.add_init_script("window.__hpTest = true; window.print = () => {}; if (!sessionStorage.getItem('ini')) { sessionStorage.setItem('ini', '1'); localStorage.setItem('peli-directe:app', " + json.dumps(json.dumps(APP)) + "); }")
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
    await pg.goto(HP_URL); await pg.add_style_tag(content=CSS); await pg.wait_for_timeout(300)
    await pg.evaluate("() => { const c = document.querySelector('#ov [data-act=\"close\"]'); if (c) c.click(); }")
    return b, pg, errs
async def partit_nou(pg, rivals="4 R4\n7 R7\n11 R11\n16 Porter R"):
    T = "(s) => { const e = document.querySelector(s); if (e) e.dispatchEvent(new MouseEvent('click', { bubbles: true })); }"
    await pg.evaluate(T, '#home [data-act="partits"]'); await pg.wait_for_timeout(80); await pg.evaluate(T, '#ov [data-act="pnew"]'); await pg.wait_for_timeout(150)
    await pg.evaluate("(l) => { const s = document.getElementById('nfix'); if (s) { s.value = ''; s.dispatchEvent(new Event('change', { bubbles: true })); } const set = (id, v) => { const e = document.getElementById(id); if (e) { e.value = v; e.dispatchEvent(new Event('input', { bubbles: true })); } }; set('nriv', 'CH Prova'); set('nrivals', l); }", rivals)
    await pg.evaluate("() => { const n = document.querySelector('[data-act=\"sqnone\"]'); if (n) n.click(); [1,2,3,4,5,6,7,8,9,10,11,12].forEach(d => { const e = document.querySelector('#sqgrid [data-v=\"' + d + '\"]'); if (e) e.click(); }); document.querySelector('[data-act=\"nstart\"]').click(); }"); await pg.wait_for_timeout(350)
    await pg.evaluate("() => { const c = document.querySelector('#ov [data-act=\"close\"]'); if (c && !document.getElementById('ov').hidden) c.click(); }"); await pg.wait_for_timeout(100)
DEVS = [("Pixel 7", "Pixel 7"), ("iPhone SE", "iPhone SE"), ("Galaxy S8", "Galaxy S8"), ("iPad horitzontal", {"viewport": {"width": 1024, "height": 768}}), ("iPad vertical", {"viewport": {"width": 768, "height": 1024}}), ("Ordinador", {"viewport": {"width": 1440, "height": 900}})]
async def pantalles(p):
    out = []
    for nom, d in DEVS:
        dev = p.devices[d] if isinstance(d, str) else d
        b, pg, errs = await obre(p, dev); await partit_nou(pg)
        mida = "() => { const se = document.scrollingElement; return [se.scrollWidth - innerWidth, se.scrollHeight - innerHeight]; }"
        r1 = await pg.evaluate(mida)
        await pg.evaluate("() => document.querySelector('#qui [data-act=\"player\"][data-v=\"2\"]').dispatchEvent(new MouseEvent('click', { bubbles: true }))"); await pg.wait_for_timeout(100)
        r2 = await pg.evaluate(mida)
        ok = r1[0] <= 1 and r1[1] <= 1 and r2[0] <= 1 and r2[1] <= 1
        out.append("   %-17s partit: %s · jugador tocat: %s %s" % (nom, "ok" if r1[0] <= 1 and r1[1] <= 1 else "se surt %s" % r1, "ok" if r2[0] <= 1 and r2[1] <= 1 else "se surt %s" % r2, "" if not errs else "· errors " + str(errs)))
        await b.close()
    return out
async def partit(p, nom, dev):
    b, pg, errs = await obre(p, dev); fall = []
    async def tap(sel, lab=""):
        r = await pg.evaluate(VIS, sel); await pg.wait_for_timeout(50)
        if r != "ok": fall.append((lab or sel) + ": " + r)
    await partit_nou(pg); await pg.evaluate("() => { window.__peli.m.det = 'com'; }")
    QUI = lambda d: '#qui [data-act="player"][data-v="' + str(d) + '"]'
    async def rival(d):
        if nom == "mobil": await tap('[data-act="rival"]', "botó rival")
        await tap(('#qui' if nom == "mobil" else '#riv') + ' [data-act="rplayer"][data-v="' + str(d) + '"]', "rival " + str(d))
    A = lambda v: '#que [data-act="action"][data-v="' + v + '"]'
    async def port():
        if await pg.evaluate("() => window.__peli.step() === 'porteria'"): await tap('[data-act="goal"][data-v="5"]', "porteria")
    await tap(QUI(2)); await tap(A("G")); await tap('[data-act="zone"][data-v="9C"]'); await port()
    await tap(QUI(3)); await tap(A("PER")); await tap('[data-act="tipus"][data-v="MP"]'); await tap('#on [data-act="opp"][data-v="4"]', "de qui")
    await tap(QUI(5)); await tap(A("P")); await tap('[data-act="zone"][data-v="6C"]'); await tap('#on [data-act="rebot"][data-v="7"]', "rebot")
    await tap(QUI(6)); await tap(A("BLQ")); await tap('#on [data-act="opp"][data-v="7"]'); await tap('#on [data-act="rebot"][data-v="A"]')
    await tap(QUI(9)); await tap(A("G")); await tap('[data-act="zone"][data-v="7M"]'); await tap('#on [data-act="prov7"][data-v="5"]', "7 m provocat"); await port()
    await rival(4); await tap(A("2M")); await tap('#on [data-act="opp"][data-v="2"]', "provocat")
    await tap(QUI(7)); await tap('#que [data-act="ptype"][data-v="CD"]'); await tap('[data-act="zone"][data-v="6C"]'); await tap('#que .acts.res [data-act="action"][data-v="GA"]'); await port(); await tap('[data-act="assist"][data-v="2"]', "assistència")
    await tap(QUI(1)); await tap('#que [data-act="ptype"][data-v="CC"]', "camp a camp del porter"); await tap('#que .acts.res [data-act="action"][data-v="G"]'); await port()
    await tap(QUI(1)); await tap(A("G"), "gol rebut"); await tap('#on [data-act="zone"][data-v="CC"]', "zona camp a camp"); await port()
    n = await pg.evaluate("() => window.__peli.m.acts.length")
    sc = await pg.evaluate("() => (document.querySelector('#board .score') || {}).innerText.replace(/\\n/g, ' ')")
    await pg.evaluate("() => document.querySelector('[data-act=\"report\"]').click()"); await pg.wait_for_timeout(300)
    tabs = await pg.evaluate("() => [...document.querySelectorAll('#rep [data-act=\"rtab\"]')].map(x => x.getAttribute('data-v'))")
    for t in tabs:
        await pg.evaluate("(v) => [...document.querySelectorAll('#rep [data-act=\"rtab\"]')].find(x => x.getAttribute('data-v') === v).click()", t); await pg.wait_for_timeout(120)
    await pg.evaluate("() => { const b = document.querySelector('#rep [data-act=\"rprint\"]'); if (b) b.click(); }"); await pg.wait_for_timeout(400)
    pdf = await pg.evaluate("() => document.querySelectorAll('#print section.pp').length")
    await b.close()
    return "   %s: %d accions desades · marcador %s · informe: %d pestanyes obertes · PDF: %d pàgines-secció · botons que no es veien: %s · errors: %s" % (nom, n, sc, len(tabs), pdf, ", ".join(fall) or "cap", errs or "cap")
async def entrenament(p, nom, dev):
    b, pg, errs = await obre(p, dev); fall = []
    async def tap(sel, lab=""):
        r = await pg.evaluate(VIS, sel); await pg.wait_for_timeout(60)
        if r != "ok": fall.append((lab or sel) + ": " + r)
    await tap('#home [data-act="trnew"]', "entrenament"); await tap('[data-act="sqall"]'); await tap('[data-act="trstart"]')
    await tap('#ov [data-act="tradd"]', "+ equip"); await tap('#ov [data-act="trcolor"][data-v="2:3"]', "C verd"); await tap('#ov [data-act="trok"]', "comença")
    await tap('#qui [data-act="player"]', "jugador A"); await tap('#que [data-act="action"][data-v="G"]'); await tap('[data-act="zone"][data-v="9C"]')
    if await pg.evaluate("() => window.__peli.step() === 'porteria'"): await tap('[data-act="goal"][data-v="5"]')
    s1 = await pg.evaluate("() => (document.querySelector('#board .score') || {}).innerText.replace(/\\n/g, ' ') + ' · punts ' + document.querySelectorAll('#board .tcol').length + ' · esperen ' + document.querySelectorAll('.trwait .tcol').length")
    await tap('[data-act="trrot"]', "partidet nou"); await pg.wait_for_timeout(150)
    if await pg.evaluate("() => !document.getElementById('ov').hidden"):
        await pg.evaluate("() => { const b = [...document.querySelectorAll('#ov [data-act]')].find(x => /trgo|trnext|trok|trplay/.test(x.getAttribute('data-act'))); if (b) b.click(); }"); await pg.wait_for_timeout(200)
    s2 = await pg.evaluate("() => (document.querySelector('#board .score') || {}).innerText.replace(/\\n/g, ' ')")
    await pg.evaluate("() => document.querySelector('[data-act=\"report\"]').click()"); await pg.wait_for_timeout(300)
    await b.close()
    return "   %s: partidet 1 «%s» · partidet nou «%s» · botons que no es veien: %s · errors: %s" % (nom, s1, s2, ", ".join(fall) or "cap", errs or "cap")
async def main():
    async with async_playwright() as p:
        print("1. Pantalles (sense desplaçar ni sortir-se'n):"); [print(x) for x in await pantalles(p)]
        print("2. Partit amb totes les jugades, informe i PDF:")
        print(await partit(p, "mobil", p.devices["Pixel 7"])); print(await partit(p, "tauleta", {"viewport": {"width": 1024, "height": 748}}))
        print("3. Entrenament amb colors i dos partidets:")
        print(await entrenament(p, "mobil", p.devices["Pixel 7"])); print(await entrenament(p, "tauleta", {"viewport": {"width": 1024, "height": 748}}))
asyncio.run(main())
