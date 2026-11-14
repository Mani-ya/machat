const CACHE = 'chat-v2';
const ASSETS = ['./', './index.html', './manifest.json'];
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS).catch(() => {}))); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== CACHE).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
    if (resp && resp.status === 200 && new URL(e.request.url).origin === location.origin) {
      const c = resp.clone(); caches.open(CACHE).then(cache => cache.put(e.request, c));
    }
    return resp;
  }).catch(() => caches.match('./index.html'))));
});
