// MANDOROS Service Worker for PWA Offline Caching & High-Speed Asset Delivery
const CACHE_NAME = 'mandoros-v3-cache';
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Cairo:wght@500;700;800&display=swap',
  'https://cdn.tailwindcss.com',
  'https://cdn.plot.ly/plotly-2.35.2.min.js',
  'https://code.jquery.com/jquery-3.7.1.min.js',
  'https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js',
  'https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.log('[SW] Pre-cache non-fatal failure:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Pass through non-GET and API / dynamic upload routes to network
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/gradio_api') || url.pathname.startsWith('/queue')) {
    return;
  }

  // Network-first with cache fallback for HTML, Cache-first for CDN/fonts
  if (url.origin.includes('cdn.') || url.origin.includes('fonts.')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(event.request).then((response) => {
          if (response && response.status === 200) {
            const respClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, respClone));
          }
          return response;
        });
      })
    );
  } else {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});
