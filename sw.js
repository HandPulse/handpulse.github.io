// HandPulse: funcionament sense connexió (versió 20261109-1).
// En publicar una versió nova, canvia CACHE perquè els aparells la descarreguin.
const CACHE = "handpulse-20261109-1";
// Escuts oficials de la federació: es guarden la primera vegada i després surten a l'instant, també sense connexió.
// Aquest magatzem no s'esborra en canviar de versió (si un club canvia d'escut, la imatge té una adreça nova).
const ESCUTS = "handpulse-escuts";
const FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];
self.addEventListener("install", e => {
  // En instal·lar, sempre fitxers nous de GitHub, mai còpies velles del navegador.
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES.map(f => new Request(f, { cache: "reload" })))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== ESCUTS).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    // La comprovació de versió nova sempre va a la xarxa, mai a la còpia desada.
    if (url.searchParams.has("hpchk")) return;
    // Primer la xarxa per a la pàgina, preguntant sempre a GitHub si ha canviat (així s'actualitza a l'instant).
    // Però si en 3 segons no ha arribat (un pavelló amb poca cobertura), s'obre la còpia desada a l'instant, i la
    // descàrrega continua per darrere i deixa la versió nova per a la propera vegada. Sense connexió, la còpia desada.
    if (req.mode === "navigate") {
      const net = fetch(new Request(req.url, { cache: "no-cache", credentials: "same-origin" })).then(res => {
        if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put("./index.html", cp)); }
        return res;
      });
      e.respondWith(new Promise(resolve => {
        let done = false;
        const fromCache = () => caches.match("./index.html").then(hit => { if (!done && hit) { done = true; resolve(hit); } return hit; });
        const timer = setTimeout(fromCache, 3000);
        net.then(res => { if (!done) { done = true; clearTimeout(timer); resolve(res); } },
          () => { clearTimeout(timer); fromCache().then(hit => { if (!done) { done = true; resolve(hit || Response.error()); } }); });
      }));
      e.waitUntil(net.then(() => {}, () => {}));
      return;
    }
    e.respondWith(caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(res => {
      const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return res;
    })));
  } else if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(CACHE).then(c => c.match(req).then(hit => hit || fetch(req).then(res => {
      c.put(req, res.clone()); return res;
    }).catch(() => hit))));
  } else if (/(^|\.)isquad\.es$/.test(url.hostname) && url.pathname.indexOf("/images/") >= 0) {
    e.respondWith(caches.open(ESCUTS).then(c => c.match(req, { ignoreVary: true }).then(hit => hit || fetch(req).then(res => {
      if (res.ok || res.type === "opaque") c.put(req, res.clone());
      return res;
    }).catch(() => hit || Response.error()))));
  }
});
