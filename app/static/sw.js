const CACHE_NAME = "todasstore-v1";
const ARQUIVOS_ESSENCIAIS = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/manifest.json",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ARQUIVOS_ESSENCIAIS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((c) => c !== CACHE_NAME).map((c) => caches.delete(c)))
    )
  );
});

self.addEventListener("fetch", (evento) => {
  // Estratégia simples: tenta a rede primeiro, cai pro cache se estiver offline
  evento.respondWith(
    fetch(evento.request).catch(() => caches.match(evento.request))
  );
});
