const CACHE = 'chat-v' + Date.now(); // کش جدید در هر بار لود

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // همیشه از شبکه بگیر، اگر شکست خورد از کش
  e.respondWith(
    fetch(e.request).then(resp => {
      if (resp && resp.status === 200 && new URL(e.request.url).origin === location.origin) {
        const clone = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return resp;
    }).catch(() => caches.match(e.request))
  );
});
