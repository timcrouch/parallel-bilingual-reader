const CACHE = "parallel-v11";
const ASSETS = ["./", "./index.html", "./styles.css?v=11", "./app.js?v=11", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", "./books/catalog.json?v=11"];
self.addEventListener("install", (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())));
self.addEventListener("activate", (event) => event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (event) => event.respondWith(
  caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
    if (event.request.method === "GET" && response.ok && new URL(event.request.url).origin === self.location.origin) {
      caches.open(CACHE).then((cache) => cache.put(event.request, response.clone()));
    }
    return response;
  })),
));
