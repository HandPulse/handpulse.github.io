// HandPulse: funcionament sense connexió (versió 20261013-4).
// En publicar una versió nova, canvia CACHE perquè els aparells la descarreguin.
const CACHE = "handpulse-20261013-4";
const FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    // La comprovació de versió nova sempre va a la xarxa, mai a la còpia desada.
    if (url.searchParams.has("hpchk")) return;
    // Primer la xarxa per a la pàgina (així s'actualitza), i la còpia desada si no hi ha connexió.
    if (req.mode === "navigate") {
      e.respondWith(fetch(req).then(res => { const cp = res.clone(); caches.open(CACHE).then(c => c.put("./index.html", cp)); return res; })
        .catch(() => caches.match("./index.html")));
      return;
    }
    e.respondWith(caches.match(req, { ignoreSearch: true }).then(hit => hit || fetch(req).then(res => {
      const cp = res.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return res;
    })));
  } else if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(CACHE).then(c => c.match(req).then(hit => hit || fetch(req).then(res => {
      c.put(req, res.clone()); return res;
    }).catch(() => hit))));
  }
});
