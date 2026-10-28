const CACHE_PREFIX = "parallel-v";
const CACHE = "parallel-v13";
const CATALOG_URL = "./books/catalog.json?v=13";
const ASSETS = ["./", "./index.html", "./styles.css?v=13", "./app.js?v=13", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png", CATALOG_URL];

async function precacheLibrary() {
  const cache = await caches.open(CACHE);
  await cache.addAll(ASSETS);
  const catalogResponse = await cache.match(CATALOG_URL);
  const catalog = await catalogResponse.json();
  await cache.addAll(catalog.books.map((book) => `${book.path}?v=13`));
}

self.addEventListener("install", (event) => event.waitUntil(precacheLibrary().then(() => self.skipWaiting())));
self.addEventListener("activate", (event) => event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (event) => event.respondWith(
  caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
    if (event.request.method === "GET" && response.ok && new URL(event.request.url).origin === self.location.origin) {
      caches.open(CACHE).then((cache) => cache.put(event.request, response.clone()));
    }
    return response;
  })),
));
