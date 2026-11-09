# Service worker: amb una connexió que tarda 6 s, l'app s'obre amb la còpia desada als ~3 s i la versió nova queda desada per a la propera vegada;
# sense connexió i amb bona connexió, també s'obre de seguida. La prova porta el seu propi servidor web, que pot fer-se lent.
import asyncio, os, time, threading, functools, http.server, socketserver
from playwright.async_api import async_playwright
DIR = os.path.dirname(os.path.abspath(__file__))
ARREL = os.environ.get("HP_ARREL") or (os.path.abspath(os.path.join(DIR, "..")) if os.path.exists(os.path.join(DIR, "..", "sw.js")) else "/mnt/user-data/outputs/handpulse_web")
LENT = {"on": False}
class Servidor(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if LENT["on"] and self.path.split("?")[0] in ("/", "/index.html"):
            time.sleep(6)
            body = open(os.path.join(ARREL, "index.html"), encoding="utf-8").read().replace("</body>", "<!-- versio-nova-prova --></body>").encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        return super().do_GET()
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Servidor, directory=ARREL)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PORT
async def main():
    async with async_playwright() as p:
        mal = 0
        def ok(c, txt):
            nonlocal mal; mal += 0 if c else 1; print("   %s %s" % ("✓" if c else "✗", txt), flush=True)
        b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 412, "height": 900}, service_workers="allow")
        await ctx.add_init_script("window.__hpTest = true; if (!localStorage.getItem('peli-directe:app')) localStorage.setItem('peli-directe:app', JSON.stringify({ v: 1, team: 'UE Sarrià', roster: [{ d: 7, n: 'Pol' }], seen: 1, guideV: 1, index: {}, current: null }));")
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(1000)
        # l'app només el registra amb https (GitHub Pages); aquí, amb http local, es registra el mateix sw.js des de la prova
        sw = await pg.evaluate("() => Promise.race([navigator.serviceWorker.register('sw.js').then(() => navigator.serviceWorker.ready).then(r => !!r.active), new Promise(r => setTimeout(() => r(false), 8000))]).catch(() => false)")
        await pg.reload(); await pg.wait_for_timeout(1500)
        ok(sw and await pg.evaluate("() => !!navigator.serviceWorker.controller"), "el service worker s'instal·la i controla l'app")
        LENT["on"] = True
        t0 = time.time(); await pg.goto(URL, wait_until="domcontentloaded"); t1 = time.time() - t0
        home = await pg.evaluate("() => !!document.getElementById('home')")
        ok(home and 2.5 <= t1 < 4.5, "amb una connexió que tarda 6 s, l'app s'obre en %.1f s amb la còpia desada (abans, s'esperava tota la descàrrega)" % t1)
        await pg.wait_for_timeout(5500)
        nova = await pg.evaluate("() => caches.keys().then(ks => Promise.all(ks.map(k => caches.open(k).then(c => c.match('./index.html')).then(r => r ? r.text() : '')))).then(ts => ts.some(t => t.includes('versio-nova-prova')))")
        ok(nova, "la versió nova, quan acaba d'arribar, queda desada per a la propera vegada")
        LENT["on"] = False
        await ctx.set_offline(True)
        t0 = time.time(); await pg.goto(URL, wait_until="domcontentloaded"); t2 = time.time() - t0
        ok(await pg.evaluate("() => !!document.getElementById('home')") and t2 < 2.5, "sense connexió, l'app s'obre en %.1f s" % t2)
        await ctx.set_offline(False)
        t0 = time.time(); await pg.goto(URL, wait_until="domcontentloaded"); t3 = time.time() - t0
        ok(t3 < 2.5, "amb bona connexió, s'obre en %.1f s, amb la versió d'internet" % t3)
        await b.close()
        print("RESUM: %s" % ("tot correcte" if not mal else "%d problemes" % mal))
asyncio.run(main())
srv.shutdown()
