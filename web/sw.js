/* Minimal service worker: network-first so a local update is never stale. */
const CACHE = 'lingualens-v9';
const SHELL = ['/login', '/assets/app.css', '/assets/workbench.css', '/assets/mobile.css', '/assets/app.js', '/favicon.svg', '/manifest.webmanifest'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin) || req.url.includes('/api/')) return;
  event.respondWith(
    fetch(req).then((res) => {
      if (res.ok && (req.destination === 'document' || req.destination === 'script' || req.destination === 'style')) {
        const copy = res.clone();
        caches.open(CACHE).then((cache) => cache.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(req).then((hit) => hit || caches.match('/login')))
  );
});
