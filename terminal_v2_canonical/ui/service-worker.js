const VERSION = "sykasif-terminal-v2-053015a";
const SHELL_CACHE = VERSION + "-shell";
const RUNTIME_CACHE = VERSION + "-runtime";
const MAP_CACHE = VERSION + "-map";

const APP_SHELL = [
  "/",
  "/manifest.webmanifest"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => ![
            SHELL_CACHE,
            RUNTIME_CACHE,
            MAP_CACHE
          ].includes(key))
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

function isMapRequest(url) {
  const host = url.hostname.toLowerCase();

  return (
    host.includes("tile.openstreetmap.org") ||
    host.includes("openstreetmap") ||
    url.pathname.includes("/tile/") ||
    url.pathname.includes("/tiles/")
  );
}

self.addEventListener("fetch", event => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // HARİTA:
  // Önce cache, yoksa ağ.
  // Görülen harita parçaları sahada tekrar kullanılabilir.
  if (isMapRequest(url)) {
    event.respondWith(
      caches.open(MAP_CACHE).then(async cache => {
        const cached = await cache.match(request);

        if (cached) return cached;

        try {
          const response = await fetch(request);

          if (response && response.ok) {
            cache.put(request, response.clone());
          }

          return response;
        } catch {
          return cached || Response.error();
        }
      })
    );

    return;
  }

  // UYGULAMA:
  // Ağ varsa güncel sürüm.
  // Ağ yoksa önbellek.
  event.respondWith(
    fetch(request)
      .then(response => {
        if (
          response &&
          response.ok &&
          (
            url.origin === self.location.origin ||
            request.destination === "script" ||
            request.destination === "style" ||
            request.destination === "image" ||
            request.destination === "font"
          )
        ) {
          const copy = response.clone();

          caches.open(RUNTIME_CACHE)
            .then(cache => cache.put(request, copy));
        }

        return response;
      })
      .catch(async () => {
        const cached = await caches.match(request);

        if (cached) return cached;

        if (request.mode === "navigate") {
          const root = await caches.match("/");
          if (root) return root;
        }

        return Response.error();
      })
  );
});

self.addEventListener("message", event => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
