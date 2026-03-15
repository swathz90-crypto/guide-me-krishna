// Service Worker for Guide Me Krishna PWA
const CACHE = 'gmk-v1';
const SHELL = [
  '/',
  '/static/manifest.json',
  '/static/krishna_arjuna.jpg.png',
  'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Lato:wght@300;400;700&family=Crimson+Text:ital,wght@0,400;1,400&display=swap'
];

// Install — cache the app shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

// Activate — clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch — network-first for API calls, cache-first for shell
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Always go network for API endpoints
  if (url.pathname.startsWith('/query') || url.pathname.startsWith('/translate') || url.pathname.startsWith('/health')) {
    e.respondWith(fetch(e.request));
    return;
  }

  // Cache-first for everything else (shell, static assets)
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        if (res && res.status === 200 && res.type !== 'opaque') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      }).catch(() => caches.match('/'));
    })
  );
});
